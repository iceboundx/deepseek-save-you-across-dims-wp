"""Expand local GLSL includes and feature defines before compilation."""

from pathlib import Path


DIRECTORY = Path(__file__).with_name("shaders")


def load_shader(name, definitions=()):
    source = _expand(DIRECTORY / name)
    if not definitions:
        return source
    version, rest = source.split("\n", 1)
    defines = "".join(f"#define {name}\n" for name in definitions)
    return f"{version}\n{defines}{rest}"


def _expand(path):
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith('#include "'):
            lines.append(_expand(path.parent / line.split('"')[1]))
        else:
            lines.append(line)
    return "".join(lines)
