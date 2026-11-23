"""Compare two recorded baselines of the same renderer, usually one per platform.

Reports how many frames are byte-identical and, for the frames both baselines
saved losslessly, how far apart the pixels are. Used to state what "the same
picture" means on a platform that does not reproduce the reference bit for bit.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load(path):
    with open(path, encoding="utf-8") as handle:
        return {record["frame"]: record for record in map(json.loads, handle)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--a", required=True, help="baseline_frames.jsonl of the reference run")
    parser.add_argument("--b", required=True, help="baseline_frames.jsonl of the run to compare")
    parser.add_argument("--golden-a", required=True, help="lossless frames of the reference run")
    parser.add_argument("--golden-b", required=True, help="lossless frames of the other run")
    args = parser.parse_args()

    a, b = load(args.a), load(args.b)
    shared = sorted(set(a) & set(b))
    print(f"frames compared       : {len(shared)}")
    print(f"byte-identical frames : {sum(a[n]['sha256'] == b[n]['sha256'] for n in shared)}")

    print(f"\n{'frame':12s} {'PSNR dB':>8s} {'max diff':>9s} {'mean diff':>10s} {'values differing':>17s}")
    rows = []
    for image in sorted(Path(args.golden_a).glob("old_f*.png")):
        other = Path(args.golden_b) / image.name
        if not other.exists():
            continue
        with Image.open(image) as first, Image.open(other) as second:
            x = np.asarray(first.convert("RGB"))
            y = np.asarray(second.convert("RGB"))
        delta = cv2.absdiff(x, y)
        psnr, largest, mean = float(cv2.PSNR(x, y)), int(delta.max()), float(delta.mean())
        share = float(np.count_nonzero(delta) / delta.size)
        rows.append((psnr, largest, mean))
        print(f"{image.stem:12s} {psnr:8.2f} {largest:9d} {mean:10.4f} {share:16.2%}")
    if rows:
        print(f"\nover {len(rows)} sampled frames: lowest PSNR {min(r[0] for r in rows):.2f} dB, "
              f"largest single-value difference {max(r[1] for r in rows)} of 255, "
              f"largest mean difference {max(r[2] for r in rows):.3f}")


if __name__ == "__main__":
    main()
