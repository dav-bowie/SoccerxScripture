# DaVinci Resolve Workflow

## Setup (once)

1. Open Resolve → New Project: **Soccer x Scripture**
2. Project settings: Timeline resolution **1920×1080 Vertical** (1080×1920), frame rate **30fps**
3. Save project to `../SoccerxScripture-media/resolve_projects/`

## Per-edit workflow

### 1. Generate recipe

```bash
python scripts/run_pipeline.py plan \
  --reference analysis/profiles/my_ref.json \
  --plan-id skill_chaos_001
```

### 2. Build handoff files

```bash
python scripts/build_resolve_timeline.py plans/skill_chaos_001.yaml
```

This creates:

- `plans/skill_chaos_001_edl.csv` — clip list with in/out points
- `plans/skill_chaos_001_resolve.py` — Resolve scripting stub
- `plans/skill_chaos_001_markers.csv` — text/effect markers

### 3. Import into Resolve

**Option A — Manual (recommended for first edits)**

1. Create timeline **skill_chaos_001** (1080×1920, 30fps)
2. Open `plans/skill_chaos_001.yaml` as your shot list
3. Drag clips from Media Pool in order; set in/out from YAML
4. Add outro clip last: `assets/outro/outro_master_2s.mov`
5. Add music track (pick from Epidemic Sound using suggested search terms in recipe)
6. Add text overlays per marker notes

**Option B — Resolve scripting**

1. Open Resolve
2. Workspace → Console (or run from terminal):

```bash
/Applications/DaVinci\ Resolve/DaVinci\ Resolve.app/Contents/MacOS/DaVinci\ Resolve \
  -script plans/skill_chaos_001_resolve.py
```

Note: Resolve must be running with a project open. The script creates a timeline and places clips if paths resolve.

### 4. Review

Follow [quality-checklist.md](quality-checklist.md). Adjust cuts, music sync, and text timing.

### 5. Approve

```bash
echo "status: approved\nreviewed_at: $(date +%Y-%m-%d)" > plans/skill_chaos_001.status
```

### 6. Export

Deliver page → Custom → H.264, 1080×1920, 30fps, 10–12 Mbps.

Save to `export/reels/YYYY-MM/skill_chaos_001.mp4`

## Brand LUT

Apply a consistent grade:

- **Day / pitch:** warm shadows, lifted greens
- **Night / cage:** teal/orange, crushed blacks

Save LUTs in `assets/brand/luts/` when finalized.

## Outro

Every timeline must end with `assets/outro/outro_master_2s.mov` (2.0s, hard cut from last action).

If outro is missing from export, run:

```bash
python scripts/concat_outro.py export/reels/YYYY-MM/body_only.mp4
```
