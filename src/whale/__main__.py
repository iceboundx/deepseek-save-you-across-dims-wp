"""Build, bake, or verify the DeepSeek live wallpaper."""

import argparse
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from .bake import prepare_assets
from .config import ENCODERS, load_config
from .encode import encode_video
from .pack import VIDEO_NAME, pack
from .render import Renderer
from .timeline import Timeline


ROOT = Path(__file__).resolve().parents[2]


def _verify(args):
    baseline = ROOT / "baseline" / args.platform
    command = [sys.executable, str(ROOT / "tools/verify_frames.py"),
               "--baseline", str(baseline / "baseline_frames.jsonl"),
               "--golden", str(baseline / "golden")]
    if args.diff_dir:
        command += ["--diff-dir", str(args.diff_dir)]
    if args.min_psnr is not None:
        command += ["--min-psnr", str(args.min_psnr)]
    for window in args.exclude:
        command += ["--exclude", window]
    command += ["--launch", sys.executable, str(ROOT / "wallpaper.py"),
                "--config", str(args.config), "--build-dir", str(args.build_dir), "frames"]
    result = subprocess.run(command)
    if result.returncode or args.video is None:
        return result.returncode
    video = [sys.executable, str(ROOT / "tools/verify_video.py"), "--video", str(args.video)]
    if args.published:
        video += ["--published", str(args.published)]
    if args.min_video_psnr is not None:
        video += ["--min-psnr", str(args.min_video_psnr)]
    return subprocess.run(video).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.toml")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    commands = parser.add_subparsers(dest="command", required=True)
    frames = commands.add_parser("frames", help="stream 4K RGB24 to stdout")
    frames.add_argument("--start", type=int, default=0)
    frames.add_argument("--frames", type=int)
    commands.add_parser("bake", help="prepare the renderer's cached textures")
    build = commands.add_parser("build", help="build a Wallpaper Engine project directory")
    build.add_argument("--output", type=Path, help="project directory (default: build/wallpaper)")
    build.add_argument("--encoder", choices=ENCODERS, help="override output.encoder in TOML")
    verify = commands.add_parser("verify", help="compare native 4K frames with the baseline")
    verify.add_argument("--platform", choices=("windows", "ubuntu"),
                        default="windows" if sys.platform == "win32" else "ubuntu")
    verify.add_argument("--diff-dir", type=Path)
    verify.add_argument("--exclude", action="append", default=[], metavar="START-END")
    verify.add_argument("--min-psnr", type=float, help="use a PSNR floor for sampled golden frames")
    verify.add_argument("--video", type=Path, help="also compare this MP4 with the published stream hash")
    verify.add_argument("--published", type=Path, help="published MP4 for decoded quality comparison")
    verify.add_argument("--min-video-psnr", type=float)
    args = parser.parse_args()
    if args.command == "verify":
        return _verify(args)

    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    timeline = Timeline.for_output(config.fps, config.rate)
    if args.command == "frames":
        stop = timeline.count if args.frames is None else args.start + args.frames
        if not 0 <= args.start < stop <= timeline.count:
            parser.error(f"frame range lies outside the {timeline.count}-frame loop")

    started = perf_counter()
    assets = prepare_assets(ROOT / "assets", args.build_dir / "cache", config)
    if args.command == "bake":
        print(f"Assets ready in {perf_counter() - started:.2f}s")
        return 0

    bake_done = perf_counter()
    with Renderer(assets, config) as renderer:
        print(f"OpenGL: {renderer.context.info['GL_RENDERER']}", file=sys.stderr)
        if args.command == "frames":
            for frame in range(args.start, stop):
                sys.stdout.buffer.write(renderer.render(frame))
            sys.stdout.buffer.flush()
            return 0

        output = (args.output or args.build_dir / "wallpaper").resolve()
        preview = None

        def render(frame):
            nonlocal preview
            pixels = renderer.render(frame)
            if frame == 0:
                preview = pixels
            return pixels

        encoder, rendered, streamed = encode_video(
            render, timeline.count, output / VIDEO_NAME,
            args.encoder or config.encoder, config.size, config.fps,
        )
        pack(output, preview, config.size, config.fps, timeline.count)
    print(output)
    print(f"{encoder} | {timeline.count} frames | rendering {rendered:.2f}s "
          f"({rendered * 1000 / timeline.count:.2f}ms/frame) | "
          f"rendering and encoding {streamed:.2f}s | cache preparation {bake_done - started:.2f}s "
          f"| total {perf_counter() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
