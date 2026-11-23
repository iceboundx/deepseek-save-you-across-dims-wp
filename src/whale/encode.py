"""Stream RGB frames to FFmpeg and write the fast-start MP4."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from imageio_ffmpeg import get_ffmpeg_exe

from .timeline import MASTER_FPS, SIZE


ENCODERS = {
    "nvenc": ["-c:v", "h264_nvenc", "-profile:v", "high", "-level", "5.2",
              "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0",
              "-maxrate", "125M", "-bufsize", "180M", "-g", "120"],
    "libx264": ["-c:v", "libx264", "-preset", "medium", "-crf", "8",
                "-tune", "animation", "-g", "120"],
}


def choose_encoder(ffmpeg, requested, size=SIZE, fps=MASTER_FPS):
    if requested != "auto":
        return requested
    probe = [ffmpeg, "-v", "error", "-f", "lavfi", "-i",
             f"color=black:s={size[0]}x{size[1]}:r={fps}",
             "-t", "1", *ENCODERS["nvenc"], "-f", "null", "-"]
    result = subprocess.run(probe, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "nvenc" if result.returncode == 0 else "libx264"


def encode_video(render, count, output, requested="auto", size=SIZE, fps=MASTER_FPS):
    ffmpeg = get_ffmpeg_exe()
    encoder = choose_encoder(ffmpeg, requested, size, fps)
    output.parent.mkdir(parents=True, exist_ok=True)
    render_seconds = 0.
    scale = "scale=out_color_matrix=bt709:in_range=pc:out_range=tv,format=yuv420p"
    if size != SIZE:
        scale = scale.replace("scale=", f"scale={size[0]}:{size[1]}:", 1)
    encode_started = perf_counter()
    with TemporaryDirectory(dir=output.parent) as directory:
        silent = Path(directory) / "silent.mp4"
        master = silent.with_name("master.mp4")
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", f"{SIZE[0]}x{SIZE[1]}",
                   "-framerate", str(fps), "-i", "pipe:0", "-an",
                   "-vf", scale,
                   *ENCODERS[encoder], "-color_primaries", "bt709", "-color_trc", "bt709",
                   "-colorspace", "bt709", str(silent)]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
            try:
                for frame in range(count):
                    started = perf_counter()
                    rgb = render(frame)
                    render_seconds += perf_counter() - started
                    process.stdin.write(rgb)
                process.stdin.close()
            except BrokenPipeError as exc:
                raise RuntimeError(f"FFmpeg stopped while encoding with {encoder}") from exc
            if process.wait():
                raise subprocess.CalledProcessError(process.returncode, command)
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(silent), "-map", "0:v:0",
                        "-c:v", "copy", "-an", "-movflags", "+faststart", str(master)], check=True)
        master.replace(output)
    return encoder, render_seconds, perf_counter() - encode_started
