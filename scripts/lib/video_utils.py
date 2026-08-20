"""Shared path and ffprobe utilities."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
PROFILES_DIR = ANALYSIS_DIR / "profiles"
PLANS_DIR = PROJECT_ROOT / "plans"
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTRO_PATH = ASSETS_DIR / "outro" / "outro_master_2s.mov"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
MIN_VIDEO_DURATION = 10.0
MAX_VIDEO_DURATION = 30.0
OUTRO_DURATION = 2.0
MIN_SHOT_S = 0.4
MAX_SHOT_S = 2.5

# Timeline / export targets (vertical Reels)
FPS = 60
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
MIN_SHORT_EDGE = 720  # below this → reject / score 0
PREFERRED_SHORT_EDGE = 1080
QUALITY_THRESHOLD = 0.55

# H.264 High @ 1080p60 — higher bitrate than 30fps exports
EXPORT_VIDEO_BITRATE_MBPS = 16
EXPORT_BITRATE_MBPS_MIN = 12
EXPORT_BITRATE_MBPS_MAX = 20
EXPORT_AUDIO_SAMPLE_RATE = 48000
EXPORT_AUDIO_BITRATE = "192k"
EXPORT_PROFILE = "high"


def fps_near_target(fps: float, tolerance: float = 1.0) -> bool:
    """True if fps is ~60 or common 59.94 NTSC variant."""
    if abs(fps - FPS) <= tolerance:
        return True
    if abs(fps - 59.94) <= 0.1:
        return True
    return False


def export_bitrate_kbps(mbps: float | None = None) -> int:
    rate = EXPORT_VIDEO_BITRATE_MBPS if mbps is None else mbps
    rate = max(EXPORT_BITRATE_MBPS_MIN, min(EXPORT_BITRATE_MBPS_MAX, rate))
    return int(rate * 1000)


def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError(
            "ffmpeg not found. Install with: brew install ffmpeg "
            "or pip install imageio-ffmpeg"
        ) from exc


def ffprobe_bin() -> str:
    path = shutil.which("ffprobe")
    if path:
        return path
    # imageio-ffmpeg bundle includes ffprobe adjacent to ffmpeg on most platforms
    ffmpeg = Path(ffmpeg_bin())
    candidate = ffmpeg.parent / ("ffprobe" + ffmpeg.suffix)
    if candidate.exists():
        return str(candidate)
    # Fall back to ffmpeg for basic probing via -i (limited)
    return ffmpeg_bin()


def run_ffprobe(path: Path) -> dict[str, Any]:
    cmd = [
        ffprobe_bin(),
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_video_stream(probe: dict[str, Any]) -> dict[str, Any] | None:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return None


def video_metadata(path: Path) -> dict[str, Any]:
    try:
        probe = run_ffprobe(path)
        vstream = get_video_stream(probe)
        if not vstream:
            raise ValueError(f"No video stream in {path}")

        duration = float(probe["format"].get("duration", 0))
        width = int(vstream.get("width", 0))
        height = int(vstream.get("height", 0))
        fps_parts = vstream.get("r_frame_rate", f"{FPS}/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(FPS)
    except Exception:
        return _video_metadata_opencv(path)

    orientation = "vertical" if height > width else "horizontal" if width > height else "square"
    crop_safe = orientation == "vertical" or min(width, height) >= PREFERRED_SHORT_EDGE

    try:
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel = str(path)

    return {
        "path": rel,
        "absolute_path": str(path.resolve()),
        "duration_s": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "orientation": orientation,
        "crop_safe": crop_safe,
    }


def _video_metadata_opencv(path: Path) -> dict[str, Any]:
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot read video: {path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or float(FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frames / fps if fps else 0
    cap.release()

    orientation = "vertical" if height > width else "horizontal" if width > height else "square"
    crop_safe = orientation == "vertical" or min(width, height) >= PREFERRED_SHORT_EDGE

    try:
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel = str(path)

    return {
        "path": rel,
        "absolute_path": str(path.resolve()),
        "duration_s": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(float(fps), 3),
        "orientation": orientation,
        "crop_safe": crop_safe,
    }


def ensure_outro_exists() -> Path:
    if not OUTRO_PATH.exists():
        raise FileNotFoundError(
            f"Outro not found at {OUTRO_PATH}. Run: python scripts/generate_outro.py"
        )
    return OUTRO_PATH


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
