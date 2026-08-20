# Pre-Export Quality Checklist

Review every edit in DaVinci Resolve before export. Mark the plan `approved` in `plans/<id>.status` only after all items pass.

## Hook (first 1.5s)

- [ ] Motion or text visible by frame 1
- [ ] Hook text is 3–6 words max, high contrast
- [ ] No dead air or setup before the joke

## Cuts & pacing

- [ ] No mid-action cuts (watch each transition once at 100% speed)
- [ ] Average shot length matches reference energy (0.4–2.5s for comedy)
- [ ] Payoff shot gets the longest hold
- [ ] Speed ramps only on the one hero moment

## Audio

- [ ] Licensed music from Epidemic Sound / Artlist (receipt in `assets/music/licenses/`)
- [ ] Music hits on payoff, not random
- [ ] Integrated loudness ~−14 LUFS, true peak ≤ −1 dB
- [ ] Outro stinger present and consistent

## Text & branding

- [ ] Hook text inside safe margins (avoid bottom 250px, top 120px)
- [ ] Verse / faith note comes *after* the joke, not before
- [ ] Last 2 seconds = **Soccer x Scripture** outro (identical every video)

## Technical

- [ ] Timeline: 1080×1920, 9:16
- [ ] Total duration: 10–30 seconds including outro
- [ ] No black frames or flash frames at cuts
- [ ] Cover frame exported from hook moment

## Approval

Create `plans/<id>.status` with:

```
status: approved
reviewed_at: YYYY-MM-DD
reviewer: your_name
```

Nothing exports until status is `approved`.
