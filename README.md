# Soccer x Scripture — Video Pipeline

Semi-automatic pipeline that analyzes reference Reels, indexes your personal footage, and produces a reviewable edit recipe for DaVinci Resolve.

## Quick start

```bash
# 1. Install dependencies (once)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg   # if not installed

# 2. Add content
#    - Drop reference Reels in video_examples_to_base_off_of/
#    - Drop your clips in personal/video/

# 3. Run the full pipeline
python scripts/run_pipeline.py all \
  --reference video_examples_to_base_off_of/my_ref.mp4 \
  --plan-id skill_chaos_001
```

## Pipeline stages

| Stage | Command | Output |
|---|---|---|
| Analyze reference | `python scripts/analyze_reference.py <video>` | `analysis/profiles/<name>.json` |
| Index personal | `python scripts/index_personal.py personal/video/` | `analysis/asset_catalog.json` |
| Plan edit | `python scripts/plan_edit.py --reference <profile.json> --output plans/<id>.yaml` | Edit recipe YAML |
| Build timeline | `python scripts/build_resolve_timeline.py plans/<id>.yaml` | EDL + Resolve script |
| Generate outro | `python scripts/generate_outro.py` | `assets/outro/outro_master_2s.mov` |

## Folder layout

```
video_examples_to_base_off_of/   ← reference Reels to mimic
personal/video/                  ← your raw clips
personal/images/                 ← stills for overlays
analysis/profiles/               ← style profiles (JSON)
analysis/asset_catalog.json      ← indexed personal footage
plans/                           ← edit recipes (YAML)
assets/outro/                    ← mandatory 2s brand sting
assets/brand/                    ← colors, fonts, LUT notes
export/reels/                    ← final exports (gitignored)
```

## Rules

- Every video ends with **Soccer x Scripture** (2s outro, identical every time)
- Target length: **10–30 seconds** including outro
- Export: **1080×1920**, H.264, 30fps
- Nothing exports until you approve the recipe in Resolve

See [docs/resolve-workflow.md](docs/resolve-workflow.md) and [docs/quality-checklist.md](docs/quality-checklist.md).
