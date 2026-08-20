# Soccer x Scripture — Video Pipeline

Semi-automatic pipeline that analyzes reference Reels, indexes your personal footage, and produces a reviewable edit recipe for DaVinci Resolve.

**Brand:** Soccer x Scripture · **Format:** 1080×1920 · **60fps** · **10–30s** · always ends with the brand outro.

## Requirements

- Python **3.11+** (see `.python-version`)
- [ffmpeg](https://ffmpeg.org/) (`brew install ffmpeg`)
- DaVinci Resolve (Free is fine) for the final edit
- Licensed music account (Epidemic Sound or Artlist)

## Quick start (clone → first Reel)

Media is **not** in git (too large). You supply reference + personal clips locally.

```bash
git clone https://github.com/dav-bowie/SoccerxScripture.git
cd SoccerxScripture

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg   # once

# Add your media
#   video_examples_to_base_off_of/my_ref.mp4   ← style to copy (9:16, prefer 60fps)
#   personal/video/*.mp4                       ← your clips (9:16, prefer 60fps)

python scripts/run_pipeline.py all \
  --reference video_examples_to_base_off_of/my_ref.mp4 \
  --plan-id skill_chaos_001
```

Then:

1. Assemble in Resolve using [docs/resolve-workflow.md](docs/resolve-workflow.md) (**manual assemble** is the supported path).
2. Pass [docs/quality-checklist.md](docs/quality-checklist.md).
3. Set `plans/skill_chaos_001.status` to `approved`.
4. Export H.264 1080×1920 @ 60fps → `export/reels/`.
5. Upload with [docs/instagram-export.md](docs/instagram-export.md).

## Pipeline stages

| Stage | Command | Output |
|---|---|---|
| Generate outro | `python scripts/run_pipeline.py outro` | `assets/outro/outro_master_2s.mov` |
| Analyze reference | `python scripts/run_pipeline.py analyze <video>` | `analysis/profiles/<name>.json` |
| Index personal | `python scripts/run_pipeline.py index` | `analysis/asset_catalog.json` |
| Plan edit | `python scripts/run_pipeline.py plan --reference <profile.json> --plan-id <id>` | `plans/<id>.yaml` |
| Build Resolve handoff | `python scripts/run_pipeline.py build plans/<id>.yaml` | EDL + markers + import stub |
| Concat outro (safety) | `python scripts/run_pipeline.py concat export/reels/body.mp4` | body + mandatory outro |

Or one shot: `python scripts/run_pipeline.py all --reference <video> --plan-id <id>`

## Folder layout

```
video_examples_to_base_off_of/   ← reference Reels to mimic (binaries gitignored)
personal/video/                  ← your raw clips (gitignored)
analysis/profiles/               ← style profiles (JSON)
analysis/asset_catalog.json      ← indexed personal footage
plans/                           ← edit recipes (YAML) + status
assets/outro/                    ← mandatory 2s brand sting
assets/brand/                    ← colors, fonts, LUT notes
assets/music/licenses/           ← Epidemic/Artlist receipts (no audio files)
export/reels/                    ← final exports (gitignored)
```

## Rules

- Every video ends with **Soccer x Scripture** (2s outro, identical every time)
- Target length: **10–30 seconds** including outro
- Film and export source at **60fps**; pipeline timelines/markers assume 60fps
- Export: **1080×1920**, H.264 High, **60fps**, ~12–20 Mbps, AAC 48kHz
- Prefer native 1080×1920; sub-720p clips are rejected by the indexer
- Nothing ships until the recipe status is `approved` after Resolve review
- Music must be licensed — see [assets/music/licenses/README.md](assets/music/licenses/README.md)

## Docs

- [Resolve workflow](docs/resolve-workflow.md) — assemble + export
- [Quality checklist](docs/quality-checklist.md) — pre-approve gate
- [Instagram export](docs/instagram-export.md) — Reels upload checklist
