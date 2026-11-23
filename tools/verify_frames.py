"""Frame-by-frame check of a renderer's raw output against the recorded baseline.

The renderer under test writes its frames to stdout as raw RGB24 bytes
(3840x2160, top row first), in loop order. Every frame's SHA256 is compared with
the baseline recorded from the archive's renderer. For a frame that differs, the
pixel distance to the baseline's lossless copy is measured when one was saved.

The frames are read from stdin, or from a renderer started with --command. The
latter needs no shell pipeline, which matters on Windows: PowerShell 5.1 passes
piped bytes through a text decoding step and corrupts them.

By default every frame must be byte-identical. An optional PSNR floor
compares the lossless golden samples across different OpenGL drivers.

Use wallpaper.py verify for the default project and its included baselines.
"""
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

WIDTH, HEIGHT = 3840, 2160
FRAME_BYTES = WIDTH * HEIGHT * 3


def split_command(command):
    """Split a command line into arguments, keeping Windows paths with backslashes intact."""
    parts = shlex.split(command, posix=os.name != "nt")
    if os.name == "nt":
        parts = [part.strip('"') for part in parts]
    return parts


def read_exactly(stream, count):
    parts = []
    remaining = count
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def load_baseline(path):
    with open(path, encoding="utf-8") as handle:
        return {record["frame"]: record for record in map(json.loads, handle)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", required=True, help="baseline_frames.jsonl to compare against")
    parser.add_argument("--golden", help="folder holding the baseline's lossless frames (old_fNNNN.png)")
    parser.add_argument("--diff-dir", help="write amplified difference images for differing frames here")
    parser.add_argument("--frames", type=int, help="frames to expect (default: every frame in the baseline)")
    parser.add_argument("--exclude", action="append", default=[], metavar="START-END",
                        help="frame range to leave out of the comparison, for example 180-237 (repeatable). "
                             "Use this when a feature is meant to change only part of the loop")
    parser.add_argument("--input", default="-", help="raw file to read instead of stdin")
    parser.add_argument("--command", help="renderer command to start, instead of reading stdin; "
                        "its stdout must be the raw frames")
    parser.add_argument("--launch", nargs=argparse.REMAINDER,
                        help="renderer and arguments, supplied as separate tokens")
    parser.add_argument("--min-psnr", type=float, help="accept golden sample differences at or above this PSNR")
    args = parser.parse_args()

    baseline = load_baseline(args.baseline)
    total = args.frames or len(baseline)
    excluded = set()
    for span in args.exclude:
        start, end = (int(value) for value in span.split("-"))
        excluded.update(range(start, end + 1))
    if args.diff_dir:
        Path(args.diff_dir).mkdir(parents=True, exist_ok=True)
    producer = None
    if args.command and args.launch:
        parser.error("provide only one producer via --command or --launch")
    if args.command or args.launch:
        producer = subprocess.Popen(args.launch or split_command(args.command), stdout=subprocess.PIPE)
        source = producer.stdout
    else:
        source = sys.stdin.buffer if args.input == "-" else open(args.input, "rb")

    identical = 0
    skipped = 0
    differing = []
    sample_psnrs = []
    ended_early_at = None
    extra = b""
    try:
        for index in range(total):
            data = read_exactly(source, FRAME_BYTES)
            if len(data) != FRAME_BYTES:
                ended_early_at = index
                break
            if index in excluded:
                skipped += 1
                continue
            digest = hashlib.sha256(data).hexdigest()
            expected = baseline.get(index)
            golden = Path(args.golden) / f"old_f{index:04d}.png" if args.golden else None
            if expected and expected["sha256"] == digest:
                if args.min_psnr is not None and golden and golden.exists():
                    sample_psnrs.append(float("inf"))
                identical += 1
                continue
            report = {"frame": index, "expected_sha256": expected["sha256"] if expected else None,
                      "got_sha256": digest}
            if golden and golden.exists():
                with Image.open(golden) as image:
                    expected_pixels = np.asarray(image.convert("RGB"))
                actual = np.frombuffer(data, np.uint8).reshape(HEIGHT, WIDTH, 3)
                delta = cv2.absdiff(expected_pixels, actual)
                psnr = float(cv2.PSNR(expected_pixels, actual))
                sample_psnrs.append(psnr)
                report.update({"psnr_db": round(psnr, 2),
                               "max_abs_diff": int(delta.max()), "mean_abs_diff": round(float(delta.mean()), 4)})
                if args.diff_dir:
                    amplified = np.clip(delta.astype(np.uint16) * 16, 0, 255).astype(np.uint8)
                    Image.fromarray(amplified).save(Path(args.diff_dir) / f"diff_f{index:04d}.png")
            differing.append(report)
        if ended_early_at is None:
            extra = read_exactly(source, FRAME_BYTES)
    finally:
        if producer is None:
            if args.input != "-":
                source.close()
        else:
            # A producer still holding unread output would otherwise block forever.
            if extra or sys.exc_info()[0] is not None:
                producer.kill()
            source.close()
            producer_failed = producer.wait(timeout=30) != 0

    print(f"baseline        : {args.baseline}")
    print(f"frames compared : {identical + len(differing)} of {total - skipped}")
    print(f"byte-identical  : {identical}")
    print(f"different       : {len(differing)}")
    if skipped:
        print(f"excluded        : {skipped}")
    if ended_early_at is not None:
        print(f"input ended early: at frame {ended_early_at}")
    if extra:
        print(f"extra input     : more than {total} frames were supplied")
    if producer is not None:
        print(f"renderer exited : {'with an error' if producer_failed else 'normally'}")
    for report in differing[:20]:
        print("  " + json.dumps(report, ensure_ascii=False))
    if len(differing) > 20:
        print(f"  ... and {len(differing) - 20} more differing frames")
    matches = identical == total - skipped
    if args.min_psnr is not None and sample_psnrs:
        floor = min(sample_psnrs)
        print(f"sample minimum  : {floor:.2f} dB ({len(sample_psnrs)} golden frames)")
        matches = floor >= args.min_psnr
    passed = matches and ended_early_at is None and not extra
    if producer is not None:
        passed = passed and not producer_failed
    print("RESULT          : " + ("PASS" if passed else "FAIL"))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
