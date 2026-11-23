"""Exercise build-time options at the frames they are intended to change."""

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from src.whale.bake import prepare_assets
from src.whale.config import GLITCH_STYLES, load_config
from src.whale.render import Renderer
from src.whale.timeline import MASTER_FRAMES, SIZE, Timeline


ROOT = Path(__file__).resolve().parents[1]


class ConfigRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(ROOT / "config.toml")
        cls.cache = ROOT / "build/cache"

    def render(self, config, *indices):
        assets = prepare_assets(ROOT / "assets", self.cache, config)
        with Renderer(assets, config) as renderer:
            return [renderer.render(index) for index in indices]

    def test_dof_strength_and_focus_pull(self):
        reference = self.render(self.config, 300)[0]
        for settings in ({"depth": 0.0}, {"focus_pull": False}):
            with self.subTest(settings=settings):
                changed = self.render(replace(self.config, **settings), 300)[0]
                self.assertNotEqual(reference, changed)
                # The middle of the portrait is in focus in both versions.
                offset = (1000 * SIZE[0] + 2500) * 3
                self.assertEqual(reference[offset:offset + 3], changed[offset:offset + 3])

    def test_speed_and_output_fps_resample_the_loop(self):
        fast = replace(self.config, rate=1.6)
        timeline = Timeline.for_output(fast.fps, fast.rate)
        self.assertEqual(timeline.count, 510)
        self.assertEqual(timeline.position(120), 192)
        self.assertEqual(Timeline.for_output(30, 1.0).count, MASTER_FRAMES // 2)
        at_60_hz = self.render(self.config, 120, 192)
        faster = self.render(fast, 120, 122)
        self.assertNotEqual(at_60_hz[0], faster[0])
        self.assertEqual(at_60_hz[1], faster[0])
        self.assertNotEqual(faster[0], faster[1])

    def test_glitch_styles_are_local_to_the_two_windows(self):
        indices = (179, 185, 238, 676, 683, 739)
        original = self.render(self.config, *indices)
        for style in GLITCH_STYLES:
            with self.subTest(style=style):
                changed = self.render(replace(self.config, glitch=style), *indices)
                for index, expected, actual in zip(indices, original, changed, strict=True):
                    if index in (185, 683):
                        self.assertNotEqual(expected, actual)
                    else:
                        self.assertEqual(expected, actual)

    def test_warning_text_changes_only_the_warning_panel(self):
        copy = (ROOT / "config.toml").read_text(encoding="utf-8")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "hud.toml"
            path.write_text(copy.replace('heading = "WARNING"', 'heading = "CAUTION"'), encoding="utf-8")
            config = load_config(path)
        untouched, reference = self.render(self.config, 0, 120)
        changed_untouched, changed = self.render(config, 0, 120)
        self.assertEqual(untouched, changed_untouched)
        self.assertNotEqual(reference, changed)
        delta = np.frombuffer(reference, np.uint8) != np.frombuffer(changed, np.uint8)
        left = delta.reshape(SIZE[1], SIZE[0], 3)[:, :SIZE[0] // 2]
        self.assertEqual(np.count_nonzero(left), np.count_nonzero(delta))


if __name__ == "__main__":
    unittest.main()
