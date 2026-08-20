# Instagram Reels export checklist

Use after Resolve export and before posting.

## File specs

| Spec | Value |
|---|---|
| Resolution | **1080×1920** (9:16) |
| Frame rate | **60fps** |
| Codec | H.264 High, yuv420p |
| Video bitrate | **12–20 Mbps** (≈16 Mbps) |
| Audio | AAC, **48kHz**, 192–256 kbps |
| Length | **10–30s** including **Soccer x Scripture** outro |
| Cover | Still from the hook frame (not a fail-face unless that *is* the joke) |

Export path: `export/reels/YYYY-MM/<plan_id>.mp4`

## Before upload

- [ ] Plan status is `approved` (`plans/<id>.status`)
- [ ] Watched once on a phone (not only the Mac)
- [ ] Outro is the last 2.0s — identical brand card
- [ ] Music is licensed (receipt in `assets/music/licenses/`)
- [ ] Caption drafted from recipe `caption_template`
- [ ] Cover frame set in Instagram (or exported still)

## Caption pattern

1. Hook line (same energy as on-screen)
2. One-line joke restatement
3. Short verse + plain-English line
4. Soft CTA (`tag a teammate` / `save for game day`)
5. **Soccer x Scripture**

Hashtags: 3–8 max (soccer + tone + light faith). Avoid stuffing.

## Upload tips

- Prefer posting from the phone Instagram app for Reels distribution
- Add audio in-app only if you exported **without** licensed music; otherwise keep the baked licensed track
- Pin a comment with the full verse if the on-screen quote was shortened
- Watch the first 30 minutes of comments

## If the body export forgot the outro

```bash
python scripts/run_pipeline.py concat export/reels/YYYY-MM/body_only.mp4 \
  -o export/reels/YYYY-MM/plan_id_final.mp4
```
