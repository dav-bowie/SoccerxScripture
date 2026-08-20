#!/usr/bin/env python3
"""Concatenate body video with mandatory outro (safety net)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.video_utils import (
    EXPORT_AUDIO_BITRATE,
    EXPORT_AUDIO_SAMPLE_RATE,
    EXPORT_PROFILE,
    EXPORT_VIDEO_BITRATE_MBPS,
    FPS,
    OUTRO_PATH,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    ensure_outro_exists,
    ffmpeg_bin,
)


def concat_outro(body: Path, output: Path, outro: Path | None = None) -> None:
    outro = outro or ensure_outro_exists()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        # FFmpeg concat demuxer requires escaped paths
        f.write(f"file '{body.resolve()}'\n")
        f.write(f"file '{outro.resolve()}'\n")
        list_path = f.name

    cmd = [
        ffmpeg_bin(),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c:v",
        "libx264",
        "-profile:v",
        EXPORT_PROFILE,
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-s",
        f"{TARGET_WIDTH}x{TARGET_HEIGHT}",
        "-b:v",
        f"{EXPORT_VIDEO_BITRATE_MBPS}M",
        "-c:a",
        "aac",
        "-ar",
        str(EXPORT_AUDIO_SAMPLE_RATE),
        "-b:a",
        EXPORT_AUDIO_BITRATE,
        str(output),
    ]
    subprocess.run(cmd, check=True)
    Path(list_path).unlink(missing_ok=True)
    print(f"Output with outro: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Append Soccer x Scripture outro to video")
    parser.add_argument("body", type=Path, help="Body video (without outro)")
    parser.add_argument("-o", "--output", type=Path, help="Output path")
    args = parser.parse_args()

    out = args.output or args.body.with_stem(args.body.stem + "_with_outro")
    concat_outro(args.body, out)


if __name__ == "__main__":
    main()
