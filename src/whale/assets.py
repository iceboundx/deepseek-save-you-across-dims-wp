"""Texture and motion paths shared by the baker and renderer."""

from dataclasses import dataclass
from pathlib import Path


FILES = {
    "base": "base.png",
    "panel": "hud/panel.png",
    "headings": "hud/headings.png",
    "logs": "hud/logs.png",
    "eye_mask": "eyes/mask.png",
    "hand_mask": "hand/mask.png",
    "ocean": "plates/ocean.png",
    "actor": "plates/actor.png",
    "prism": "plates/prism.png",
    "bubbles": "fx/bubble-ink.png",
    "silk": "fx/silk.png",
    "optics": "data/optics.npy",
    "hair_matte": "hair/matte.npy",
    "face_under": "hair/face-under.png",
    "hair_motion": "hair/motion.npy",
    "motion": "data/body-motion.npy",
    "grade": "data/grade-lut.npy",
}

PREPARED = {"eye_mask", "hand_mask", "prism", "optics", "hair_matte", "face_under", "motion"}
HUD = {"panel", "headings", "logs"}


@dataclass(frozen=True)
class Assets:
    root: Path
    prepared: Path
    hud: Path
    particles: Path

    def __getitem__(self, name):
        if name in PREPARED:
            directory = self.prepared
        elif name in HUD:
            directory = self.hud
        else:
            directory = self.root
        return directory / FILES[name]

    def eyelid(self, frame):
        return self.root / "eyes/cels" / f"{frame}.png"

    def dust(self, frame):
        return self.particles / "fx/dust" / f"{frame:04}.png"
