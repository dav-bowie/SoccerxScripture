# DaVinci Resolve Workflow

## Setup (once)

1. Open Resolve → New Project: **Soccer x Scripture**
2. Project settings: Timeline resolution **1920×1080 Vertical** (1080×1920), frame rate **60fps**
3. Save project outside the git repo (e.g. `../SoccerxScripture-media/resolve_projects/`)

## Supported path: manual assemble (Option A)

This is the **production** workflow. Use the YAML + EDL as a shot list; you make the final cuts.

### 1. Generate recipe

```bash
python scripts/run_pipeline.py all \
  --reference video_examples_to_base_off_of/my_ref.mp4 \
  --plan-id skill_chaos_001
```

### 2. Handoff files

`python scripts/build_resolve_timeline.py plans/skill_chaos_001.yaml` creates:

- `plans/skill_chaos_001_edl.csv` — clip list with in/out
- `plans/skill_chaos_001_markers.csv` — text/effect markers (60fps frame numbers)
- `plans/skill_chaos_001_resolve.py` — **import stub only** (not a full auto-editor)

### 3. Assemble in Resolve

1. Create timeline **skill_chaos_001** (1080×1920, **60fps**)
2. Open `plans/skill_chaos_001.yaml` as the shot list
3. Drag clips from Media Pool in order; set in/out from YAML
4. Add outro last: `assets/outro/outro_master_2s.mov` (generate with `python scripts/run_pipeline.py outro` if missing)
5. Add licensed music (search terms in recipe → receipt in `assets/music/licenses/`)
6. Add hook / verse text per markers — verse **after** the joke

### 4. Review

Follow [quality-checklist.md](quality-checklist.md).

### 5. Approve

```bash
cat > plans/skill_chaos_001.status <<'EOF'
status: approved
reviewed_at: YYYY-MM-DD
note: Ready for Instagram export
EOF
```

### 6. Export

Deliver → Custom → **H.264 High**, 1080×1920, **60fps**, **12–20 Mbps**, AAC 48kHz.

Save to `export/reels/YYYY-MM/skill_chaos_001.mp4`

Then follow [instagram-export.md](instagram-export.md).

## Option B — Resolve script (not production)

The generated `*_resolve.py` script can create a timeline and **import** media when Resolve is open. It does **not** reliably place in/out points or build the finished cut. Treat it as a convenience importer only; finish the edit manually (Option A).

## Brand LUT

- **Day / pitch:** warm shadows, lifted greens
- **Night / cage:** teal/orange, crushed blacks

Save LUTs in `assets/brand/luts/` when finalized.

## Outro

Every timeline must end with the 2.0s **Soccer x Scripture** master at 60fps (hard cut from last action).

If a body export forgot the outro:

```bash
python scripts/run_pipeline.py concat export/reels/YYYY-MM/body_only.mp4
```
