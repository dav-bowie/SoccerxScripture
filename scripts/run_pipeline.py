#!/usr/bin/env python3
"""Run the full Soccer x Scripture pipeline or individual stages."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"


def run(cmd: list[str]) -> None:
    print(f"\n→ {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def stage_analyze(reference: Path) -> Path:
    out = PROJECT_ROOT / "analysis" / "profiles" / f"{reference.stem}.json"
    run([sys.executable, str(SCRIPTS / "analyze_reference.py"), str(reference), "-o", str(out)])
    return out


def stage_index(personal_dir: Path) -> Path:
    out = PROJECT_ROOT / "analysis" / "asset_catalog.json"
    run([sys.executable, str(SCRIPTS / "index_personal.py"), str(personal_dir), "-o", str(out)])
    return out


def stage_plan(profile: Path, plan_id: str) -> Path:
    out = PROJECT_ROOT / "plans" / f"{plan_id}.yaml"
    run(
        [
            sys.executable,
            str(SCRIPTS / "plan_edit.py"),
            "--reference",
            str(profile),
            "--plan-id",
            plan_id,
            "--output",
            str(out),
        ]
    )
    return out


def stage_build(recipe: Path) -> None:
    run([sys.executable, str(SCRIPTS / "build_resolve_timeline.py"), str(recipe)])


def stage_outro() -> None:
    run([sys.executable, str(SCRIPTS / "generate_outro.py")])


def main() -> None:
    parser = argparse.ArgumentParser(description="Soccer x Scripture pipeline runner")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze reference video")
    p_analyze.add_argument("reference", type=Path)

    p_index = sub.add_parser("index", help="Index personal footage")
    p_index.add_argument("directory", type=Path, nargs="?", default=PROJECT_ROOT / "personal" / "video")

    p_plan = sub.add_parser("plan", help="Generate edit recipe")
    p_plan.add_argument("--reference", type=Path, required=True)
    p_plan.add_argument("--plan-id", type=str, default="edit_001")

    p_build = sub.add_parser("build", help="Build Resolve handoff")
    p_build.add_argument("recipe", type=Path)

    sub.add_parser("outro", help="Generate brand outro")

    p_all = sub.add_parser("all", help="Run full pipeline")
    p_all.add_argument("--reference", type=Path, required=True)
    p_all.add_argument("--personal", type=Path, default=PROJECT_ROOT / "personal" / "video")
    p_all.add_argument("--plan-id", type=str, default="edit_001")

    args = parser.parse_args()

    if args.command == "analyze":
        stage_analyze(args.reference)
    elif args.command == "index":
        stage_index(args.directory)
    elif args.command == "plan":
        stage_plan(args.reference, args.plan_id)
    elif args.command == "build":
        stage_build(args.recipe)
    elif args.command == "outro":
        stage_outro()
    elif args.command == "all":
        stage_outro()
        profile = stage_analyze(args.reference)
        stage_index(args.personal)
        recipe = stage_plan(profile, args.plan_id)
        stage_build(recipe)
        print("\n✓ Pipeline complete. Review recipe in plans/ and open Resolve handoff files.")


if __name__ == "__main__":
    main()
