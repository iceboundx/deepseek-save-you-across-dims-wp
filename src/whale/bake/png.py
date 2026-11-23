"""Use OpenCV's PNG codec with Python's Unicode-aware file paths."""

import cv2
import numpy as np


def read_png(path):
    return cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)


def write_png(path, pixels):
    ok, encoded = cv2.imencode(".png", pixels)
    if not ok:
        raise RuntimeError(f"Cannot encode {path}")
    path.write_bytes(encoded.tobytes())
