# REVIEW: Reels version (9:16), long cut

1080x1920, 30 fps, 85.5 s (47 bars at 132 BPM). Rebuilt for density and a slower pace on request.

- Nine scenes: needle drop (with portrait below), research in two pages (question and AIK, then four real figures and three 2026 studies), stage (talkshow, then eight venues with topics), leadership (new), field (four programmes and two businesses), flip to Side B with a certificate strip, the climb in six steps (2021, 2022, 2023 BKKBN DIY, 2023 Governor, 2024 held three bars, 2026), the claim with a photo strip, end card with three facts and the address.
- Text stays between 168 and 1330 px; below that only photos, certificates and decorative type fill the frame, clear of the Instagram caption and buttons.
- `hyperframes check`: clean. Holds marked with `data-hold` where a page is meant to be read.
- Not checked on a real phone; the sound was measured, not heard.

## Revision round 1 (6 changes)
1. Talkshow photo reframed so Miranto (seated left) is visible; title moved up and the dark band no longer covers him.
2. "On stage at": scrim only behind the list (two columns), photo reframed past the screenshot's black bars, both speakers visible.
3. Leadership photo replaced with YBW UII Expo 2024, all five people in frame; list arrives faster.
4. Filled empty floors with real-data graphics: an animated Java map (Pekalongan programmes and Pempek BOOM, Bandung sourcing, distribution arcs without invented destinations) and the FEBIC path model with its betas. No sales chart: only an average yearly figure exists.
5. End card: portrait background removed locally, enlarged as a papercut figure over the record. Source is 582 px wide, so it is slightly soft.
6. Music removed; sound effects kept (mean level now about -24 dB).

## Final touch: image quality
- Every photo re-processed from the original uploads (not the compressed copies): Lanczos upscale to at least its 4K display size, light denoise, unsharp mask, WebP quality 93. The cutout was rebuilt from the 3x portrait.
- AI super-resolution (Real-ESRGAN) was not used: running a downloaded binary was blocked in this session. Detail the source never had cannot be recovered; sharpening improves edges and removes compression mush.
- Master rendered at 2160x3840 (`--resolution portrait-4k --quality delivery`); the Instagram file is a Lanczos downscale at CRF 16.
