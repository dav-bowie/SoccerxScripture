#!/usr/bin/env python3
"""Concatenate body video with mandatory outro (safety net)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.video_utils import OUTRO_PATH, ensure_outro_exists, ffmpeg_bin


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
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
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
