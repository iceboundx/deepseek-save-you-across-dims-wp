"""Compare a produced video with the published wallpaper, frame by frame.

The primary test is the SHA256 of the raw H.264 stream: equal hashes mean the
two files carry bit-identical video. When the streams differ, the decoded frames
are compared and their PSNR reported, so a build made on another platform or
with another encoder can still be judged against a threshold.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

PUBLISHED_STREAM_SHA256 = "ca58785617391313b9525d62e9532022a31e06df3c9a5850f5e3400714bff76b"
WIDTH, HEIGHT = 3840, 2160
FRAME_BYTES = WIDTH * HEIGHT * 3


def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def stream_hash(ffmpeg, video):
    command = [str(ffmpeg), "-v", "error", "-i", str(video), "-map", "0:v:0", "-c", "copy", "-f", "h264", "pipe:1"]
    digest = hashlib.sha256()
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        for block in iter(lambda: process.stdout.read(1 << 20), b""):
            digest.update(block)
        if process.wait() != 0:
            raise RuntimeError(f"cannot extract the video stream of {video}")
    return digest.hexdigest()


def decoder(ffmpeg, video):
    command = [str(ffmpeg), "-v", "error", "-i", str(video), "-map", "0:v:0", "-an",
               "-vf", "scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    return subprocess.Popen(command, stdout=subprocess.PIPE)


def compare_frames(ffmpeg, produced, published):
    streams = [decoder(ffmpeg, video) for video in (produced, published)]
    psnrs, identical, largest, count = [], 0, 0, 0
    while True:
        frames = [stream.stdout.read(FRAME_BYTES) for stream in streams]
        if not any(frames):
            break
        if any(len(frame) != FRAME_BYTES for frame in frames):
            raise RuntimeError(f"the two videos differ in length at frame {count}")
        first = np.frombuffer(frames[0], np.uint8).reshape(HEIGHT, WIDTH, 3)
        second = np.frombuffer(frames[1], np.uint8).reshape(HEIGHT, WIDTH, 3)
        if frames[0] == frames[1]:
            identical += 1
        else:
            psnrs.append(float(cv2.PSNR(first, second)))
            largest = max(largest, int(cv2.absdiff(first, second).max()))
        count += 1
    for stream in streams:
        if stream.stdout.read(1) or stream.wait() != 0:
            raise RuntimeError("decoding failed")
    return {"frames": count, "frames_identical_after_decode": identical,
            "psnr_min": round(min(psnrs), 3) if psnrs else None,
            "psnr_median": round(float(np.median(psnrs)), 3) if psnrs else None,
            "largest_value_difference": largest}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", required=True, help="the mp4 to check")
    parser.add_argument("--published", help="the published mp4, for a frame-by-frame comparison when streams differ")
    parser.add_argument("--expect-stream-sha256", default=PUBLISHED_STREAM_SHA256,
                        help="stream hash the video must have (default: the published wallpaper)")
    parser.add_argument("--min-psnr", type=float, help="accept the video when its PSNR against the published one "
                        "reaches this value, even if the streams differ")
    parser.add_argument("--ffmpeg", help="ffmpeg executable (default: the one from imageio-ffmpeg)")
    args = parser.parse_args()
    ffmpeg = args.ffmpeg or ffmpeg_path()

    result = {"video": str(Path(args.video)), "bytes": Path(args.video).stat().st_size,
              "stream_sha256": stream_hash(ffmpeg, args.video), "expected_stream_sha256": args.expect_stream_sha256}
    result["stream_identical"] = result["stream_sha256"] == args.expect_stream_sha256
    if not result["stream_identical"] and args.published:
        result["against_published"] = compare_frames(ffmpeg, args.video, args.published)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["stream_identical"]:
        print("RESULT          : PASS (bit-identical video stream)")
        sys.exit(0)
    floor = (result.get("against_published") or {}).get("psnr_min")
    if args.min_psnr is not None and floor is not None and floor >= args.min_psnr:
        print(f"RESULT          : PASS (streams differ, PSNR {floor} dB is at or above {args.min_psnr} dB)")
        sys.exit(0)
    print("RESULT          : FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
