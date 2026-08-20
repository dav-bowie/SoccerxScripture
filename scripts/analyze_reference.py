#!/usr/bin/env python3
"""Analyze a reference video and produce a style profile JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.analysis import (
    audio_energy_curve,
    bucket_energy,
    detect_scenes,
    estimate_bpm,
    find_peaks,
    infer_cut_pattern,
    infer_hook_type,
    infer_theme,
    motion_energy_curve,
    shot_lengths,
)
from scripts.lib.video_utils import PROFILES_DIR, PROJECT_ROOT, save_json, video_metadata


def analyze_reference(path: Path) -> dict:
    meta = video_metadata(path)
    duration = meta["duration_s"]

    cut_times = detect_scenes(path)
    shots = shot_lengths(cut_times)
    avg_shot = round(sum(shots) / len(shots), 3) if shots else duration

    motion = motion_energy_curve(path)
    audio = audio_energy_curve(path)
    motion_vals = [p["motion"] for p in motion]
    energy_labels = bucket_energy(motion_vals) if motion_vals else ["mid"]

    bpm = estimate_bpm(path)
    hook = infer_hook_type(motion, duration)
    pattern = infer_cut_pattern(avg_shot, len(shots))
    theme = infer_theme(len(find_peaks(motion, audio)), avg_shot, bpm)

    target_lo = max(10, int(duration * 0.85))
    target_hi = min(30, int(duration * 1.05))

    try:
        ref_path = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        ref_path = str(path)

    profile = {
        "reference": ref_path,
        "duration_s": duration,
        "target_duration_s": f"{target_lo}-{target_hi}",
        "resolution": {"width": meta["width"], "height": meta["height"]},
        "fps": meta["fps"],
        "hook": hook,
        "cut_rhythm": {
            "cut_times_s": cut_times,
            "shot_lengths_s": shots,
            "avg_shot_length_s": avg_shot,
            "pattern": pattern,
            "shot_count": len(shots),
        },
        "energy_curve": energy_labels,
        "motion_samples": motion[:30],
        "audio_samples": audio[:20],
        "transitions": ["hard_cut"] + (["speed_ramp"] if avg_shot > 1.5 else []),
        "music": {
            "bpm_estimate": bpm,
            "mood": _mood_tags(bpm, theme),
            "energy": "building" if "high" in energy_labels[-2:] else "steady",
            "library": "epidemic_sound",
            "suggested_search": _music_search(bpm, theme),
        },
        "theme": theme,
        "interesting_segments": find_peaks(motion, audio, top_n=5),
    }
    return profile


def _mood_tags(bpm: int | None, theme: str) -> list[str]:
    tags = ["masculine", "stadium"]
    if bpm and bpm > 125:
        tags.append("hype")
    if theme == "soul_beauty":
        tags = ["cinematic", "emotional", "uplifting"]
    elif theme == "comedy_reaction":
        tags.append("playful")
    return tags


def _music_search(bpm: int | None, theme: str) -> list[str]:
    if theme == "soul_beauty":
        return ["cinematic sports emotional", "inspirational instrumental"]
    if bpm and bpm > 130:
        return ["stadium trap", "sports hype instrumental"]
    return ["soccer reel energy", "trap sports beat instrumental"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze reference video → style profile")
    parser.add_argument("video", type=Path, help="Path to reference video")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON path (default: analysis/profiles/<stem>.json)",
    )
    args = parser.parse_args()

    if not args.video.exists():
        print(f"Error: file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    profile = analyze_reference(args.video.resolve())
    out = args.output or PROFILES_DIR / f"{args.video.stem}.json"
    save_json(out, profile)
    print(f"Profile written: {out}")
    print(f"  Theme: {profile['theme']}")
    print(f"  Duration: {profile['duration_s']}s → target {profile['target_duration_s']}s")
    print(f"  Cuts: {profile['cut_rhythm']['shot_count']} shots, avg {profile['cut_rhythm']['avg_shot_length_s']}s")


if __name__ == "__main__":
    main()
