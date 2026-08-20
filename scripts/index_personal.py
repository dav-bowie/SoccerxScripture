#!/usr/bin/env python3
"""Index personal footage and build asset catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.analysis import audio_energy_curve, motion_energy_curve
from scripts.lib.quality import best_segments, infer_tags, sample_quality
from scripts.lib.video_utils import (
    ANALYSIS_DIR,
    PROJECT_ROOT,
    QUALITY_THRESHOLD,
    VIDEO_EXTENSIONS,
    save_json,
    video_metadata,
)


def index_directory(root: Path, min_quality: float = QUALITY_THRESHOLD) -> dict:
    clips = []
    skipped = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        try:
            meta = video_metadata(path)
            quality = sample_quality(path)
            motion = motion_energy_curve(path, sample_interval=0.5)
            tags = infer_tags(path, motion, quality)
            segments = best_segments(path, meta["duration_s"])

            has_dialogue = _detect_dialogue(path)

            entry = {
                **meta,
                "quality_score": quality,
                "tags": tags,
                "best_segments": segments,
                "audio_usability": "dialogue" if has_dialogue else "sfx_only",
                "usable": quality >= min_quality,
            }

            if entry["usable"]:
                clips.append(entry)
            else:
                skipped.append({"path": entry["path"], "quality_score": quality, "reason": "below threshold"})

        except Exception as exc:
            skipped.append({"path": str(path), "reason": str(exc)})

    catalog = {
        "source_dir": str(root.relative_to(PROJECT_ROOT)) if root.is_relative_to(PROJECT_ROOT) else str(root),
        "clip_count": len(clips),
        "skipped_count": len(skipped),
        "quality_threshold": min_quality,
        "clips": sorted(clips, key=lambda c: c["quality_score"], reverse=True),
        "skipped": skipped,
    }
    return catalog


def _detect_dialogue(path: Path) -> bool:
    audio = audio_energy_curve(path)
    if len(audio) < 5:
        return False
    vals = [p["audio_rms"] for p in audio]
    # High variance in speech-like audio
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    return variance > 0.0001 and mean > 0.02


def main() -> None:
    parser = argparse.ArgumentParser(description="Index personal video footage")
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=PROJECT_ROOT / "personal" / "video",
        help="Directory to scan (default: personal/video/)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ANALYSIS_DIR / "asset_catalog.json",
    )
    parser.add_argument("--min-quality", type=float, default=QUALITY_THRESHOLD)
    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Warning: directory not found: {args.directory}", file=sys.stderr)
        catalog = {
            "source_dir": str(args.directory),
            "clip_count": 0,
            "skipped_count": 0,
            "quality_threshold": args.min_quality,
            "clips": [],
            "skipped": [],
        }
    else:
        catalog = index_directory(args.directory.resolve(), args.min_quality)

    save_json(args.output, catalog)
    print(f"Catalog written: {args.output}")
    print(f"  Usable clips: {catalog['clip_count']}")
    print(f"  Skipped: {catalog['skipped_count']}")


if __name__ == "__main__":
    main()
