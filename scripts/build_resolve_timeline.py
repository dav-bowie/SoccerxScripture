#!/usr/bin/env python3
"""Build Resolve handoff files from edit recipe YAML."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.video_utils import PLANS_DIR, PROJECT_ROOT


def load_recipe(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def resolve_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def build_edl(recipe: dict, out_path: Path) -> None:
    rows = [["slot", "clip_path", "in_s", "out_s", "duration_s", "effect", "text", "timeline_start_s"]]

    cursor = 0.0
    for item in recipe.get("timeline", []):
        slot = item["slot"]
        effect = item.get("effect", "hard_cut")
        text = item.get("text", "")

        if slot == "outro":
            clip_path = resolve_path(item["asset"])
            duration = item.get("duration_s", 2.0)
            rows.append([slot, str(clip_path), "0", str(duration), str(duration), effect, item.get("text", ""), str(round(cursor, 3))])
            cursor += duration
            continue

        clip_path = resolve_path(item["clip"])
        in_s = item["in"]
        out_s = item["out"]
        duration = item.get("duration_s", out_s - in_s)
        rows.append([slot, str(clip_path), str(in_s), str(out_s), str(duration), effect, text, str(round(cursor, 3))])
        cursor += duration

    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def build_markers(recipe: dict, out_path: Path) -> None:
    rows = [["frame", "color", "name", "note", "duration_s"]]
    fps = 30
    cursor = 0.0

    for item in recipe.get("timeline", []):
        if item.get("text"):
            rows.append(
                [
                    str(int(cursor * fps)),
                    "Blue",
                    item["slot"],
                    f"TEXT: {item['text']} | EFFECT: {item.get('effect', '')}",
                    str(item.get("duration_s", 1.0)),
                ]
            )
        elif item.get("effect") and item["slot"] != "outro":
            rows.append(
                [
                    str(int(cursor * fps)),
                    "Green",
                    item["slot"],
                    f"EFFECT: {item.get('effect', '')}",
                    str(item.get("duration_s", 1.0)),
                ]
            )

        if item["slot"] == "outro":
            cursor += item.get("duration_s", 2.0)
        else:
            cursor += item.get("duration_s", item.get("out", 0) - item.get("in", 0))

    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def build_resolve_script(recipe: dict, out_path: Path, edl_path: Path, markers_path: Path) -> None:
    title = recipe.get("title", "SoccerxScripture_Edit")
    timeline_items = []

    for item in recipe.get("timeline", []):
        if item["slot"] == "outro":
            timeline_items.append(
                {
                    "slot": "outro",
                    "path": str(resolve_path(item["asset"])),
                    "in": 0,
                    "out": item.get("duration_s", 2.0),
                }
            )
        else:
            timeline_items.append(
                {
                    "slot": item["slot"],
                    "path": str(resolve_path(item["clip"])),
                    "in": item["in"],
                    "out": item["out"],
                }
            )

    script = f'''#!/usr/bin/env python3
"""
DaVinci Resolve timeline builder for: {title}
Run with Resolve open and a project loaded.

Usage (Resolve must be running):
  /Applications/DaVinci\\ Resolve/DaVinci\\ Resolve.app/Contents/MacOS/DaVinci\\ Resolve -script {out_path.name}
"""

import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
if not project:
    raise RuntimeError("Open a Resolve project first")

media_pool = project.GetMediaPool()
root = media_pool.GetRootFolder()

TIMELINE_NAME = "{title}"
TIMELINE_ITEMS = {repr(timeline_items)}

timeline = None
for i in range(1, project.GetTimelineCount() + 1):
    tl = project.GetTimelineByIndex(i)
    if tl.GetName() == TIMELINE_NAME:
        timeline = tl
        break

if not timeline:
    timeline = media_pool.CreateEmptyTimeline(TIMELINE_NAME)
    project.SetCurrentTimeline(timeline)

media_pool.SetCurrentFolder(root)

for item in TIMELINE_ITEMS:
    media_pool.ImportMedia([item["path"]])

print(f"Timeline '{{TIMELINE_NAME}}' ready.")
print("Import clips from EDL if auto-append fails:")
print("  {edl_path}")
print("Markers file:")
print("  {markers_path}")
'''

    out_path.write_text(script)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Resolve handoff from edit recipe")
    parser.add_argument("recipe", type=Path, help="Edit recipe YAML")
    args = parser.parse_args()

    recipe = load_recipe(args.recipe)
    stem = args.recipe.stem

    edl_path = args.recipe.with_name(f"{stem}_edl.csv")
    markers_path = args.recipe.with_name(f"{stem}_markers.csv")
    resolve_path_out = args.recipe.with_name(f"{stem}_resolve.py")

    build_edl(recipe, edl_path)
    build_markers(recipe, markers_path)
    build_resolve_script(recipe, resolve_path_out, edl_path, markers_path)

    print(f"EDL:      {edl_path}")
    print(f"Markers:  {markers_path}")
    print(f"Resolve:  {resolve_path_out}")


if __name__ == "__main__":
    main()
