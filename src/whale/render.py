"""Render water, scene and finishing passes to packed RGB24 frames."""

import sys

import moderngl as gl
import numpy as np
from PIL import Image

from .fragments import tracks
from .shader import load_shader
from .timeline import (
    MASTER_FPS, MASTER_FRAMES, SIZE, Timeline, eye_closures, eyelid_at,
    hair_at, motion_at, prepare_motion,
)


IMAGE_TEXTURES = (
    (0, "art", "base", "RGB"),
    (1, "panel", "panel", "RGBA"),
    (2, "headings", "headings", "RGBA"),
    (3, "logAtlas", "logs", "RGBA"),
    (4, "eyeMask", "eye_mask", "L"),
    (8, "skinMask", "hand_mask", "L"),
    (9, "ocean", "ocean", "RGB"),
    (10, "actor", "actor", "RGBA"),
    (11, "prism", "prism", "RGB"),
    (12, "bubbleInk", "bubbles", "RGB"),
    (13, "silk", "silk", "RGBA"),
)


class Renderer:
    def __init__(self, assets, config):
        self.assets = assets
        self.config = config
        self.timeline = Timeline.for_output(config.fps, config.rate)
        backend = {"backend": "egl"} if sys.platform.startswith("linux") else {}
        self.context = gl.create_standalone_context(require=330, **backend)
        try:
            self._setup()
        except Exception:
            self.context.release()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.context.release()

    def _setup(self):
        context = self.context
        vertex = load_shader("fullscreen.vert")
        focus_defines = () if self.config.focus_pull else ("FIXED_FOCUS",)

        def program(name, glitch=None):
            defines = focus_defines + (("SIGNAL_FAULT",) if glitch else ())
            fragment = load_shader(f"{name}.frag", defines)
            if glitch:
                fragment += load_shader("glitch/patch.glsl") + load_shader(f"glitch/{glitch}.glsl")
            return context.program(vertex_shader=vertex, fragment_shader=fragment)

        self.scene = program("scene")
        self.scene_quad = context.vertex_array(self.scene, [])
        self.output = context.simple_framebuffer(SIZE, components=4)
        self.output.use()
        self.scene_color = self._texture(15, SIZE, 4)
        hand = self._texture(18, SIZE, 1)
        self.scene_target = context.framebuffer(color_attachments=[self.scene_color, hand])

        self.finish = program("finish")
        self.finish_quad = self._finish_quad(self.finish)
        self.glitch = self.glitch_quad = None
        if self.config.glitch:
            self.glitch = program("finish", self.config.glitch)
            self.glitch_quad = self._finish_quad(self.glitch)

        self.water = program("water")
        self.water_quad = context.vertex_array(self.water, [])
        water = self._scene_texture(14, "waterPlane", SIZE, 3)
        self.water_target = context.framebuffer(color_attachments=[water])
        self.scene["depthAmount"].value = .73 * self.config.depth
        self.water["ocean"].value = 9
        self.water["bubbleInk"].value = 12
        self.water["optics"].value = 17

        data = np.load(self.assets["grade"])
        self.grade = context.texture3d((49, 49, 49), 3, data.tobytes(), dtype="f2")
        self.grade.filter = (gl.LINEAR, gl.LINEAR)
        self.grade.repeat_x = self.grade.repeat_y = self.grade.repeat_z = False
        self.grade.use(16)

        self.textures = [self._image_texture(slot, uniform, self.assets[name], mode)
                         for slot, uniform, name, mode in IMAGE_TEXTURES]
        self.textures.append(self._array_texture(17, "optics", self.assets["optics"]))
        self.textures.append(self._array_texture(21, "hairMatte", self.assets["hair_matte"]))
        self.textures.append(self._image_texture(22, "faceUnder", self.assets["face_under"], "RGBA"))
        self.scene["hairGain"].value = 1.

        self.lids = self._scene_texture(5, "lid", (1380, 850), 3)
        self.dust = self._scene_texture(6, "dust", (800, 680), 4)
        self.flow = self._scene_texture(7, "motion", (193, 109), 2, dtype="f4")
        self.hair_motion = np.load(self.assets["hair_motion"]) * np.array(
            [[2.65, 2.25], [3.45, 2.5], [5.8, 3.9]], dtype="f4"
        )
        self.motion = prepare_motion(np.load(self.assets["motion"]))
        self.sample_chips = tracks(self.assets["actor"])

    def _finish_quad(self, program):
        program["peripheralFocus"].value = .66 * self.config.depth
        program["scene"].value = 15
        program["handPlane"].value = 18
        program["printGrade"].value = 16
        return self.context.vertex_array(program, [])

    def _texture(self, slot, size, components, data=None, dtype="f1"):
        texture = self.context.texture(size, components, data, dtype=dtype)
        texture.filter = (gl.LINEAR, gl.LINEAR)
        texture.repeat_x = texture.repeat_y = False
        texture.use(slot)
        return texture

    def _scene_texture(self, slot, uniform, size, components, data=None, dtype="f1"):
        texture = self._texture(slot, size, components, data, dtype)
        if uniform in self.scene:
            self.scene[uniform].value = slot
        return texture

    def _image_texture(self, slot, uniform, path, mode):
        with Image.open(path) as image:
            return self._scene_texture(slot, uniform, image.size, len(mode), image.convert(mode).tobytes())

    def _array_texture(self, slot, uniform, path):
        data = np.load(path)
        return self._scene_texture(slot, uniform, data.shape[1::-1], data.shape[2], data.tobytes(), "f2")

    def render(self, index):
        frame = self.timeline.position(index)
        phase = frame / MASTER_FRAMES
        amount = max(eye_closures(frame))
        if amount > .0001:
            with Image.open(self.assets.eyelid(eyelid_at(frame))) as image:
                self.lids.write(image.tobytes())
        with Image.open(self.assets.dust(index)) as image:
            self.dust.write(image.tobytes())
        self.flow.write(motion_at(self.motion, frame).tobytes())
        self.scene["phase"].value = phase
        self.scene["closed"].value = amount
        self.scene["lockNow"].write(hair_at(self.hair_motion, frame).tobytes())
        self.scene["lockLate"].write(hair_at(self.hair_motion, (frame - 7) % MASTER_FRAMES).tobytes())
        for uniform, values in zip(("chips", "chipInk", "sockets"), self.sample_chips(phase)):
            self.scene[uniform].write(values.tobytes())

        self.water_target.use()
        self.water["phase"].value = phase
        self.water_quad.render(mode=gl.TRIANGLES, vertices=3)
        self.scene_target.use()
        self.scene_quad.render(mode=gl.TRIANGLES, vertices=3)
        self.output.use()
        self.scene_color.build_mipmaps(0, 5)
        seconds = frame / MASTER_FPS
        finish, quad = self.finish, self.finish_quad
        # Only fault-window frames use the alternate program. The original
        # finish program renders the rest of the loop even with faults enabled.
        if self.glitch is not None and (3.00 < seconds < 3.95 or 11.28 < seconds < 12.30):
            finish, quad = self.glitch, self.glitch_quad
        if "seconds" in finish:
            finish["seconds"].value = seconds
        quad.render(mode=gl.TRIANGLES, vertices=3)
        # The shaders treat the first uploaded row as the top of the artwork.
        # OpenGL's readback returns that row first, with no CPU-side flip.
        return self.output.read(components=3, alignment=1)
