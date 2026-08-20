#!/usr/bin/env python3
"""Generate the mandatory 2s Soccer x Scripture outro video."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
    ffmpeg_bin,
)

BG_COLOR = (13, 59, 71)  # #0D3B47
TEXT_COLOR = (212, 175, 55)  # #D4AF37
FONT_SIZE = 72
DURATION = 2.0
WIDTH = TARGET_WIDTH
HEIGHT = TARGET_HEIGHT
TEXT = "Soccer x Scripture"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _render_frame() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_SIZE)

    bbox = draw.textbbox((0, 0), TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2
    draw.text((x, y), TEXT, fill=TEXT_COLOR, font=font)

    tmp = Path(tempfile.gettempdir()) / "soccerxscripture_outro_frame.png"
    img.save(tmp)
    return tmp


def generate_outro(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = _render_frame()

    cmd = [
        ffmpeg_bin(),
        "-y",
        "-loop",
        "1",
        "-i",
        str(frame),
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={EXPORT_AUDIO_SAMPLE_RATE}:cl=stereo:d={DURATION}",
        "-c:v",
        "libx264",
        "-profile:v",
        EXPORT_PROFILE,
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-b:v",
        f"{EXPORT_VIDEO_BITRATE_MBPS}M",
        "-t",
        str(DURATION),
        "-c:a",
        "aac",
        "-ar",
        str(EXPORT_AUDIO_SAMPLE_RATE),
        "-b:a",
        EXPORT_AUDIO_BITRATE,
        "-shortest",
        str(output),
    ]

    subprocess.run(cmd, check=True)
    frame.unlink(missing_ok=True)
    print(f"Outro generated: {output} ({WIDTH}x{HEIGHT} @ {FPS}fps)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Soccer x Scripture outro")
    parser.add_argument("-o", "--output", type=Path, default=OUTRO_PATH)
    args = parser.parse_args()
    generate_outro(args.output)


if __name__ == "__main__":
    main()
