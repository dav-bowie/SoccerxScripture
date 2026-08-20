# Soccer x Scripture — Outro Design Spec

The master outro is generated programmatically and can be refined in DaVinci Resolve.

## Spec

| Property | Value |
|---|---|
| Text | Soccer x Scripture |
| Duration | 2.0 seconds |
| Resolution | 1080×1920 (9:16) |
| Frame rate | 60fps |
| Codec | H.264 High, ~16 Mbps |
| Audio | AAC 48kHz (silent bed) |
| Background | Dark teal `#0D3B47` |
| Text color | Gold `#D4AF37` |
| Font | Georgia / serif display |

## Generate

```bash
python scripts/generate_outro.py
```

Output: `assets/outro/outro_master_2s.mov`

## Refine in Resolve (optional)

1. Import `assets/outro/outro_master_2s.mov`
2. Add subtle gradient, grain, or Fusion title animation
3. Add 4–6 note stinger on audio track
4. Re-export with same filename to replace master

Every edit recipe ends with this asset. Do not change duration or spelling.
