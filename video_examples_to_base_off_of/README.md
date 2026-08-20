# Reference Videos

Drop Instagram Reels or other vertical videos here that you want the pipeline to study and mimic.

## Naming

Use descriptive names that match the style:

```
fail_compilation_ref.mp4
skill_challenge_ref.mov
golden_hour_soul_ref.mp4
```

One reference per style/category. The analyzer creates a profile in `analysis/profiles/`.

## What gets extracted

- Duration and cut rhythm
- Hook timing (first 1.5s)
- Energy curve (audio + motion)
- Interesting moments (peaks, impacts, reactions)
- Music mood / BPM estimate
- Transition patterns

## Run analysis

```bash
python scripts/analyze_reference.py video_examples_to_base_off_of/your_ref.mp4
```
