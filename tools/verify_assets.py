"""Compare the source and freshly baked assets with the archive's recorded hashes."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

from src.whale.bake import prepare_assets
from src.whale.config import load_config


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    parser.add_argument("--archive-work", type=Path, help="also check the original archive's work directory")
    args = parser.parse_args()
    assets = prepare_assets(ROOT / "assets", args.build_dir / "cache", load_config(ROOT / "config.toml"))
    directories = {"assets": assets.root, "prepared": assets.prepared,
                   "hud": assets.hud, "particles": assets.particles}
    with (assets.root / "manifest.jsonl").open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream]
    passed = Counter()
    pixels_only = Counter()
    different = Counter()
    for record in records:
        group = record["group"]
        path = directories[group] / record["path"]
        expected = record["sha256"]
        if args.archive_work:
            original = args.archive_work / record["archive"]
            if sha256(original) != expected:
                print(f"Archive differs: {original}")
                return 1
        if path.is_file() and sha256(path) == expected:
            passed[group] += 1
            continue
        if sys.platform.startswith("linux") and path.is_file() and "pixels_sha256" in record:
            with Image.open(path) as image:
                pixels = hashlib.sha256(image.tobytes()).hexdigest()
            if pixels == record["pixels_sha256"]:
                pixels_only[group] += 1
                continue
        if different[group] < 5:
            print(f"Different: {group}/{record['path']}")
        different[group] += 1
    for group in directories:
        print(f"{group}: {passed[group]} byte-identical, "
              f"{pixels_only[group]} pixel-identical, {different[group]} different")
    return int(bool(different))


if __name__ == "__main__":
    raise SystemExit(main())
