"""Read the build settings and keep HUD copy in its fixed layout order."""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import tomllib

from .timeline import MASTER_FPS, SIZE


PANEL_ORDER = ("trace", "warning", "phase", "boundary")
ENCODERS = ("auto", "nvenc", "libx264")
GLITCH_STYLES = ("scanline", "jitter", "displacement")


@dataclass(frozen=True)
class Config:
    size: tuple[int, int]
    fps: int
    encoder: str
    rate: float
    depth: float
    focus_pull: bool
    glitch: str | None
    panels: tuple[dict, ...]


def _positive_number(value, field, *, allow_zero=False):
    if (type(value) not in (float, int) or not isfinite(value) or
            value < 0 or (not allow_zero and value == 0)):
        raise ValueError(f"{field} must be a {'nonnegative' if allow_zero else 'positive'} finite number")
    return value


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def load_config(path: Path):
    with path.open("rb") as stream:
        data = tomllib.load(stream)

    output = data.get("output", {})
    size = (output.get("width", SIZE[0]), output.get("height", SIZE[1]))
    if any(type(n) is not int or n <= 0 or n % 2 for n in size):
        raise ValueError("output.width and output.height must be positive even integers")
    fps = output.get("fps", MASTER_FPS)
    if type(fps) is not int or fps <= 0:
        raise ValueError("output.fps must be a positive integer")
    encoder = output.get("encoder", "auto")
    if encoder not in ENCODERS:
        raise ValueError(f"output.encoder must be one of {', '.join(ENCODERS)}")

    rate = _positive_number(data.get("speed", {}).get("rate", 1.0), "speed.rate")
    dof = data.get("dof", {})
    depth = _positive_number(dof.get("strength", 1.0), "dof.strength", allow_zero=True)
    focus_pull = dof.get("focus_pull", True)
    glitch = data.get("glitch", {})
    enabled = glitch.get("enabled", False)
    if type(focus_pull) is not bool or type(enabled) is not bool:
        raise ValueError("dof.focus_pull and glitch.enabled must be boolean")
    style = glitch.get("style", "scanline")
    if style not in GLITCH_STYLES:
        raise ValueError(f"glitch.style must be one of {', '.join(GLITCH_STYLES)}")

    panels = data.get("hud", {}).get("panels", [])
    if (len(panels) != len(PANEL_ORDER) or
            {panel.get("id") for panel in panels} != set(PANEL_ORDER)):
        raise ValueError("hud.panels must define trace, warning, phase and boundary once each")
    by_id = {panel["id"]: panel for panel in panels}
    ordered = []
    for key in PANEL_ORDER:
        panel = by_id[key]
        fields = {name: _text(panel.get(name), f"hud.{key}.{name}")
                  for name in ("heading", "side", "type")}
        records = panel.get("records")
        if not isinstance(records, list) or len(records) != 6:
            raise ValueError(f"hud.{key}.records must contain six entries")
        fields["records"] = [_text(record, f"hud.{key}.records") for record in records]
        ordered.append(fields)

    return Config(size, fps, encoder, rate, depth, focus_pull, style if enabled else None, tuple(ordered))
