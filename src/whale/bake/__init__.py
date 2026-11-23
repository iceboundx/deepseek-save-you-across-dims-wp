"""Build and cache the deterministic inputs used by the renderer."""

import hashlib
import json
import os
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image

from . import eyes, hair, hand, motion, optics, prism
from ..assets import Assets, FILES
from ..timeline import MASTER_FRAMES, Timeline


RECIPES = Path(__file__).parent
SOURCE_INPUTS = ("base.png", "plates/ocean.png", "eyes/painted-open.png", "data/motion.json")


def _cached(cache, group, inputs, parameters, bake):
    digest = hashlib.sha256(json.dumps([sys.platform, parameters], sort_keys=True).encode())
    for path in inputs:
        with path.open("rb") as stream:
            digest.update(hashlib.file_digest(stream, "sha256").digest())
    target = cache / group / digest.hexdigest()
    if target.is_dir():
        return target

    print(f"Baking {group}...", file=sys.stderr, flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent) as directory:
        staged = Path(directory) / "output"
        staged.mkdir()
        bake(staged)
        try:
            staged.rename(target)
        except OSError:
            # A simultaneous build may have completed the same recipe first.
            if not target.is_dir():
                raise
    return target


def _bake_textures(root, stage):
    def output(name):
        path = stage / FILES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    base = root / "base.png"
    eyes.bake(root / "eyes/painted-open.png", output("eye_mask"))
    hand.bake(base, output("hand_mask"))
    prism.bake(base, output("prism"))
    optics.bake(root / "plates/ocean.png", output("optics"))
    hair.bake(base, output("hair_matte"), output("face_under"))
    motion.bake(root / "data/motion.json", output("motion"))


def prepare_assets(root, cache, config):
    project = RECIPES.parents[2]
    python_recipes = sorted(RECIPES.glob("*.py"))
    prepared = _cached(
        cache, "prepared",
        [*python_recipes, project / "pyproject.toml", *(root / name for name in SOURCE_INPUTS)],
        None, lambda path: _bake_textures(root, path),
    )

    node_recipe = RECIPES / "node.cjs"
    lock = project / "package-lock.json"

    def node(group, script, payload, extra_inputs=(), finish=None):
        def bake(stage):
            subprocess.run(
                ["node", str(node_recipe), group, str(stage.resolve())],
                input=json.dumps(payload), encoding="utf-8", check=True,
            )
            if finish is not None:
                finish(stage)

        return _cached(cache, group, [node_recipe, RECIPES / script, lock, *extra_inputs],
                       payload, bake)

    supplied_fonts = os.environ.get("WHALE_FONT_DIR")
    font_inputs = [Path(supplied_fonts) / name for name in
                   ("arialbd.ttf", "consola.ttf", "consolab.ttf")] if supplied_fonts else []
    hud_payload = {"panels": config.panels}
    master = root / "portable/hud"
    if sys.platform.startswith("linux"):
        # Skia's font rasterization differs with the same font files. Keep
        # the published artwork for unchanged panels, even on a fontless host.
        reference = json.loads((master / "panels.json").read_text(encoding="utf-8"))
        changed = [index for index, (original, current) in
                   enumerate(zip(reference, config.panels, strict=True)) if original != current]
        hud_payload["changed"] = changed
        hud_inputs = [master / name for name in ("panels.json", "headings.png", "logs.png")]
        hud = node("hud", "hud.cjs", hud_payload, [*hud_inputs, *(font_inputs if changed else [])],
                   lambda stage: _compose_hud(master, stage / "hud", changed))
    else:
        hud = node("hud", "hud.cjs", hud_payload, font_inputs)

    count = Timeline.for_output(config.fps, config.rate).count
    if sys.platform.startswith("linux") and count == MASTER_FRAMES:
        # These two Skia rasters round a few channel values differently.
        corrections = (Path("fx/dust/0193.png"), Path("fx/dust/0601.png"))
        sources = [root / "portable" / file for file in corrections]

        def apply_corrections(stage):
            for original, relative in zip(sources, corrections, strict=True):
                copyfile(original, stage / relative)

        particles = node("particles", "particles.cjs", {"frames": count}, sources, apply_corrections)
    else:
        particles = node("particles", "particles.cjs", {"frames": count})
    return Assets(root, prepared, hud, particles)


def _compose_hud(reference, output, changed):
    if not changed:
        for name in ("headings.png", "logs.png"):
            copyfile(reference / name, output / name)
        return

    with Image.open(reference / "headings.png") as original, Image.open(output / "headings.png") as text:
        with Image.open(output / "headings-mask.png") as image:
            mask = image.getchannel("A").point(lambda alpha: 255 if alpha else 0)
        headings = Image.composite(text, original, mask)
    headings.save(output / "headings.png")
    (output / "headings-mask.png").unlink()

    with Image.open(reference / "logs.png") as original, Image.open(output / "logs.png") as text:
        logs = original.copy()
        width, height = logs.width // 2, logs.height // 2
        for index in changed:
            x, y = index % 2 * width, index // 2 * height
            logs.paste(text.crop((x, y, x + width, y + height)), (x, y))
    logs.save(output / "logs.png")
