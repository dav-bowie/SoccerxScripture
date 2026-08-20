#!/usr/bin/env python3
"""Generate edit recipe YAML from reference profile + asset catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.video_utils import (
    EXPORT_AUDIO_SAMPLE_RATE,
    EXPORT_BITRATE_MBPS_MAX,
    EXPORT_BITRATE_MBPS_MIN,
    EXPORT_PROFILE,
    EXPORT_VIDEO_BITRATE_MBPS,
    FPS,
    MAX_SHOT_S,
    MAX_VIDEO_DURATION,
    MIN_SHORT_EDGE,
    MIN_SHOT_S,
    MIN_VIDEO_DURATION,
    OUTRO_DURATION,
    OUTRO_PATH,
    PLANS_DIR,
    PREFERRED_SHORT_EDGE,
    PROJECT_ROOT,
    QUALITY_THRESHOLD,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    ensure_outro_exists,
)


SLOT_SEQUENCE = {
    "rapid_montage": ["hook", "beat_1", "beat_2", "beat_3", "beat_4", "payoff", "outro"],
    "triple_fail_then_payoff": ["hook", "fail_1", "fail_2", "fail_3", "payoff", "reaction", "outro"],
    "slow_build_hold": ["hook", "beauty_1", "beauty_2", "payoff", "outro"],
    "beat_matched_cuts": ["hook", "beat_1", "beat_2", "payoff", "reaction", "outro"],
}

SLOT_TAG_PREFERENCES = {
    "hook": ["action", "kick", "high_quality"],
    "fail_1": ["reaction_fail", "kick", "action"],
    "fail_2": ["reaction_fail", "kick", "action"],
    "fail_3": ["reaction_fail", "kick", "action"],
    "beat_1": ["action", "kick"],
    "beat_2": ["action", "kick"],
    "beat_3": ["action", "kick"],
    "beat_4": ["action", "kick"],
    "payoff": ["kick", "action", "high_quality"],
    "reaction": ["reaction_smug", "reaction", "face_closeup"],
    "beauty_1": ["beauty_slowmo", "high_quality"],
    "beauty_2": ["beauty_slowmo", "high_quality"],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def pick_clip_for_slot(clips: list[dict], slot: str, used_paths: set[str]) -> dict | None:
    prefs = SLOT_TAG_PREFERENCES.get(slot, ["action"])
    fresh = [c for c in clips if c["path"] not in used_paths and c.get("usable", True)]
    pool = fresh if fresh else [c for c in clips if c.get("usable", True)]
    pool.sort(key=lambda c: c["quality_score"], reverse=True)

    for tag in prefs:
        for clip in pool:
            if tag in clip.get("tags", []):
                return clip

    return pool[0] if pool else None


def segment_for_slot(
    clip: dict,
    slot: str,
    target_len: float,
    segment_index: int = 0,
) -> tuple[float, float]:
    segments = clip.get("best_segments", [])
    duration = clip["duration_s"]

    target_len = max(MIN_SHOT_S, min(MAX_SHOT_S, target_len))

    ranked = sorted(segments, key=lambda s: s.get("score", 0), reverse=True) if segments else []

    if ranked and segment_index < len(ranked):
        seg = ranked[segment_index]
        start = seg["start"]
        end = min(start + target_len, seg["end"], duration)
        if end - start < MIN_SHOT_S:
            end = min(start + target_len, duration)
    else:
        # Exhausted peaks (or none): spread evenly across the clip timeline
        # Offset past ranked peaks so we don't re-pick the same windows
        usable = max(duration - target_len, 0)
        if usable <= 0:
            start, end = 0.0, min(target_len, duration)
        else:
            # Use a spaced grid; skip early windows already covered by peaks
            n_slots = max(6, len(ranked) + 4)
            idx = segment_index if not ranked else segment_index - len(ranked)
            start = min((idx % n_slots) * (usable / n_slots), usable)
            end = min(start + target_len, duration)

    start = round(start, 2)
    end = round(max(start + MIN_SHOT_S, end), 2)
    if end > duration:
        end = round(duration, 2)
        start = round(max(0.0, end - target_len), 2)
    return start, end


def slot_effect(slot: str, profile: dict) -> str:
    if slot == "hook":
        hook_type = profile.get("hook", {}).get("type", "impact_first")
        return "smash_zoom" if hook_type == "impact_first" else "hard_cut"
    if slot == "payoff":
        return "speed_ramp" if "speed_ramp" in profile.get("transitions", []) else "hold"
    if slot.startswith("fail"):
        return "hard_cut"
    if slot.startswith("beauty"):
        return "slow_hold"
    return "hard_cut"


def hook_text(profile: dict) -> str | None:
    theme = profile.get("theme", "")
    texts = {
        "skill_vs_chaos": "he said easy",
        "hype_challenge": "one take.",
        "comedy_reaction": "watch this",
        "soul_beauty": None,
    }
    return texts.get(theme, "let's go")


def plan_edit(profile: dict, catalog: dict, plan_id: str, profile_path: str = "") -> dict:
    ensure_outro_exists()

    pattern = profile.get("cut_rhythm", {}).get("pattern", "beat_matched_cuts")
    slots = SLOT_SEQUENCE.get(pattern, SLOT_SEQUENCE["beat_matched_cuts"])

    avg_shot = profile.get("cut_rhythm", {}).get("avg_shot_length_s", 1.0)
    avg_shot = max(MIN_SHOT_S, min(MAX_SHOT_S, avg_shot))

    clips = catalog.get("clips", [])
    if not clips:
        raise ValueError("No usable clips in asset catalog. Add footage to personal/video/ and re-index.")

    used_paths: set[str] = set()
    reuse_index: dict[str, int] = {}
    timeline = []
    body_duration = 0.0

    target_parts = profile.get("target_duration_s", "16-20")
    if isinstance(target_parts, str) and "-" in target_parts:
        target_total = float(target_parts.split("-")[1]) if "-" in target_parts else 18.0
    else:
        target_total = 18.0

    body_budget = min(
        MAX_VIDEO_DURATION - OUTRO_DURATION,
        max(MIN_VIDEO_DURATION - OUTRO_DURATION, target_total - OUTRO_DURATION),
    )
    content_slots = [s for s in slots if s != "outro"]
    slot_budget = body_budget / max(1, len(content_slots))

    for slot in content_slots:
        clip = pick_clip_for_slot(clips, slot, used_paths)
        if not clip:
            continue

        path = clip["path"]
        seg_idx = reuse_index.get(path, 0)
        start, end = segment_for_slot(clip, slot, min(avg_shot, slot_budget), seg_idx)
        reuse_index[path] = seg_idx + 1
        used_paths.add(path)

        shot_dur = end - start
        entry = {
            "slot": slot,
            "clip": path,
            "in": start,
            "out": end,
            "duration_s": round(shot_dur, 2),
            "effect": slot_effect(slot, profile),
        }

        text = hook_text(profile) if slot == "hook" else None
        if text:
            entry["text"] = text

        timeline.append(entry)
        body_duration += shot_dur

    # Pad: prefer lengthening shots before adding extras (avoids duplicate windows)
    while body_duration < MIN_VIDEO_DURATION - OUTRO_DURATION and timeline:
        content = [t for t in timeline if t["slot"] != "outro"]
        if not content:
            break
        # Grow shortest shots toward MAX_SHOT_S first
        grew = False
        for entry in sorted(content, key=lambda t: t["duration_s"]):
            if entry["duration_s"] >= MAX_SHOT_S:
                continue
            clip_meta = next((c for c in clips if c["path"] == entry["clip"]), None)
            if not clip_meta:
                continue
            room = min(MAX_SHOT_S - entry["duration_s"], clip_meta["duration_s"] - entry["out"])
            if room < 0.05:
                # Try extending start earlier
                room_back = min(MAX_SHOT_S - entry["duration_s"], entry["in"])
                if room_back < 0.05:
                    continue
                entry["in"] = round(entry["in"] - room_back, 2)
                entry["duration_s"] = round(entry["out"] - entry["in"], 2)
                body_duration += room_back
                grew = True
                break
            add = min(room, (MIN_VIDEO_DURATION - OUTRO_DURATION) - body_duration)
            entry["out"] = round(entry["out"] + add, 2)
            entry["duration_s"] = round(entry["out"] - entry["in"], 2)
            body_duration += add
            grew = True
            break
        if grew:
            continue

        # Fall back: add one extra beat from a fresh window
        best = max(clips, key=lambda c: c["quality_score"])
        path = best["path"]
        seg_idx = reuse_index.get(path, 0)
        start, end = segment_for_slot(best, "beat_extra", avg_shot, seg_idx)
        # Skip if this window duplicates an existing cut
        if any(
            t.get("clip") == path and abs(t.get("in", -1) - start) < 0.05 and abs(t.get("out", -1) - end) < 0.05
            for t in timeline
        ):
            reuse_index[path] = seg_idx + 1
            if seg_idx > 20:
                break
            continue
        reuse_index[path] = seg_idx + 1
        shot_dur = end - start
        timeline.append(
            {
                "slot": f"beat_extra_{seg_idx}",
                "clip": path,
                "in": start,
                "out": end,
                "duration_s": round(shot_dur, 2),
                "effect": "hard_cut",
            }
        )
        body_duration += shot_dur
        if seg_idx > 20:
            break

    timeline.append(
        {
            "slot": "outro",
            "asset": str(OUTRO_PATH.relative_to(PROJECT_ROOT)),
            "duration_s": OUTRO_DURATION,
            "text": "Soccer x Scripture",
            "effect": "hard_cut",
        }
    )
    body_duration += OUTRO_DURATION

    # Trim if over max
    while body_duration > MAX_VIDEO_DURATION and len(timeline) > 2:
        # Remove second-to-last non-outro slot
        for i in range(len(timeline) - 2, 0, -1):
            if timeline[i]["slot"] != "outro":
                removed = timeline.pop(i)
                body_duration -= removed.get("duration_s", 0)
                break
        else:
            break

    music = profile.get("music", {})
    recipe = {
        "title": plan_id,
        "status": "draft",
        "reference": profile.get("reference"),
        "reference_profile": profile_path,
        "fps": FPS,
        "target_duration_s": round(body_duration, 2),
        "music": {
            "mood": "_".join(music.get("mood", ["hype", "masculine"])[:2]),
            "bpm_target": f"{(music.get('bpm_estimate') or 128) - 5}-{(music.get('bpm_estimate') or 128) + 5}",
            "library": music.get("library", "epidemic_sound"),
            "suggested_search": music.get("suggested_search", ["sports hype instrumental"]),
        },
        "timeline": timeline,
        "quality_rules": {
            "fps": FPS,
            "min_resolution": [TARGET_WIDTH, TARGET_HEIGHT],
            "min_short_edge": MIN_SHORT_EDGE,
            "preferred_short_edge": PREFERRED_SHORT_EDGE,
            "quality_threshold": QUALITY_THRESHOLD,
            "export": {
                "codec": "H.264",
                "profile": EXPORT_PROFILE,
                "resolution": [TARGET_WIDTH, TARGET_HEIGHT],
                "fps": FPS,
                "video_bitrate_mbps": EXPORT_VIDEO_BITRATE_MBPS,
                "video_bitrate_mbps_range": [EXPORT_BITRATE_MBPS_MIN, EXPORT_BITRATE_MBPS_MAX],
                "audio": f"AAC {EXPORT_AUDIO_SAMPLE_RATE // 1000}kHz",
            },
            "min_shot_s": MIN_SHOT_S,
            "max_shot_s": MAX_SHOT_S,
            "no_mid_action_cuts": True,
            "outro_required": True,
        },
        "caption_template": _caption_template(profile),
    }
    return recipe


def _caption_template(profile: dict) -> str:
    theme = profile.get("theme", "comedy_reaction")
    hooks = {
        "skill_vs_chaos": "{hook_line}\n\nWe plan. God laughs. — Proverbs 16:9\n\nTag a teammate who said \"easy\"\n\nSoccer x Scripture",
        "hype_challenge": "{hook_line}\n\nFall seven times, stand up eight. — Proverbs 24:16\n\nSave for game day\n\nSoccer x Scripture",
        "soul_beauty": "Play free.\n\nFor we are God's masterpiece. — Ephesians 2:10\n\nSoccer x Scripture",
        "comedy_reaction": "{hook_line}\n\nLet another praise you. — Proverbs 27:2\n\nSoccer x Scripture",
    }
    return hooks.get(theme, hooks["comedy_reaction"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan edit from profile + catalog")
    parser.add_argument("--reference", type=Path, required=True, help="Style profile JSON")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=PROJECT_ROOT / "analysis" / "asset_catalog.json",
    )
    parser.add_argument("--output", type=Path, help="Output YAML path")
    parser.add_argument("--plan-id", type=str, default="edit_001")
    args = parser.parse_args()

    profile = load_json(args.reference)
    catalog = load_json(args.catalog) if args.catalog.exists() else {"clips": []}

    try:
        profile_rel = str(args.reference.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        profile_rel = str(args.reference)

    recipe = plan_edit(profile, catalog, args.plan_id, profile_path=profile_rel)
    out = args.output or PLANS_DIR / f"{args.plan_id}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.dump(recipe, default_flow_style=False, sort_keys=False))

    status_path = out.with_suffix(".status")
    status_path.write_text(
        "status: draft\n"
        f"created_at: {__import__('datetime').date.today().isoformat()}\n"
        "note: Review in DaVinci Resolve before changing to approved\n"
    )

    print(f"Recipe written: {out}")
    print(f"  Status: {status_path} (draft — approve after Resolve review)")
    print(f"  Timeline slots: {len(recipe['timeline'])}")
    print(f"  Target duration: {recipe['target_duration_s']}s")


if __name__ == "__main__":
    main()
