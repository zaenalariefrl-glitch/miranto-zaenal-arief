---
name: video-generate
description: Generate motion-graphic videos (opening, intro, teaser, bumper, title sequence) for Jen as high-fps MP4 (60 fps default, up to 120) with a dense, synced procedural sound-effects mix. Use whenever Jen asks for a video, opening, intro, animation, motion graphic, teaser, or "video generate" in this repo.
---

# Video Generate (60+ fps + dense SFX)

Pipeline in `video/` (all local, deterministic, no paid API):

```
scenes/<name>.html  --render.mjs (Playwright, frame-by-frame)-->  out/<name>/video.mp4 (H.264, CRF 14, 60fps)
        |  window.SCENE.cues
        +--> out/<name>/cues.json --sfx.py mix (numpy synth)--> sfx.wav --ffmpeg loudnorm -14 LUFS--> final.mp4
```

## Commands (run from `video/`)
- Full build: `tools/make_video.sh scenes/<name>.html --fps 60 --workers 4`
- 120 fps: add `--fps 120`. 4K: add `--scale 2` (scene stays authored at 1920x1080).
- Preview a slice: `--from 3 --to 6` (renders only that range; cues still full).
- Re-mix sound only (fast): `AUDIO_ONLY=1 tools/make_video.sh scenes/<name>.html`
- QC: `tools/contact_sheet.sh out/<name>/final.mp4 16` -> contact.png + wave.png. Always look at both before delivering.
- SFX catalogue: `python3 tools/sfx.py list`; audition all: `python3 tools/sfx.py preview out/sfx_preview`

## Scene contract
Copy `scenes/_template.html`. A scene must define:
- `window.SCENE = {width:1920, height:1080, duration, fps:60, cues:[...]}`
- `window.seek(t)`: sets every element as a pure function of `t`. Never use CSS transitions/animations, `setTimeout`, `requestAnimationFrame` or `Date.now()`; they break frame accuracy.
- Optional `window.preload()` (async) for images/video assets.
Use `tools/motion.js` (`M.tw`, `M.prog`, `M.life`, `M.E.*` easings, `M.shake`, `M.flash`, `M.split`, `M.rand`).
Fonts are vendored in `assets/fonts/fonts.css`: Playfair Display, Montserrat, Cinzel (+ system Inter, JetBrains Mono).

## Sound design rules ("padat")
Every visual event gets a sound; define the hit times once as constants and use them for BOTH motion and cues.
- Bed: one `pad` across the full duration (gain -14 to -18) and/or `pulse` (bpm) under montage parts.
- Before every big reveal: `riser` (end-aligned on the hit, `dur` 1.5 to 3) + `reverse_swell` ending on the hit.
- On the reveal: `impact` / `logo_hit` / `braam` + camera `M.shake` + `M.flash` on the same `t`.
- Every element entering/moving: `whoosh` (0.4 to 0.9 s) or `swish` (fast), pan to follow screen direction (-1 left, 1 right).
- Text/UI: `typing`, `tick`, `click`; glitch cuts: `glitch`; gold glints: `shimmer`/`chime`; transitions: `sub_drop`, `tape_stop`.
- Density target: at least 1 cue every 0.5 s on average, layered 2 to 3 deep on key hits. Leave 0.3 to 0.5 s of near-silence right before the main logo hit for contrast.
- Gains in dB. Rough levels: hits 0, whooshes -6, ticks -8, shimmer -8, bed -14. Master is auto loudnormed to -14 LUFS / -1 dBTP.
- Real samples: `{t, sfx:'file', path:'assets/sfx/name.wav', gain}` (48k/44.1k WAV).

## Visual defaults for Jen
Minimalist, dark: obsidian `#1a1614`, deep brown `#2d241e`, gold `#b38b4d`, brass `#d4af37`, paper `#fdfcfb` (navy `#0f1b2d` as alternative). Serif titles (Playfair/Cinzel) + Montserrat tracking caps. Film grain, light leaks, subtle camera push-in. Credentials appear inside the narrative, not as an opening list. Copy for competition/international use: full English. No em/en dashes in on-screen text.

## Delivery
Output `out/<name>/final.mp4` (gitignored). Copy the final into the repo root or scratchpad and send it with SendUserFile, together with contact.png. Report fps, resolution, duration, cue count in 1 to 2 sentences.
Rendering speed is roughly 6 to 10 frames/s with 4 workers at 1080p; a 15 s 60 fps opening is ~900 frames, so run long renders with `run_in_background`.
