# REVIEW: "Side A, Side B" portfolio intro

**Built:** storyline A, 38.2 s, 1920×1080 at 30 fps, 8 scenes on a 132 BPM bar grid. Not built: B "The Climb" (year as a match-cut anchor; its year roll lives on inside scene 6) and C "The Question" (kinetic type opening). Both are in STORYLINES.md.

**Creative calls**
- The portfolio's record player is the carrier: the needle drop opens, the camera dives through the spindle hole into the research, the record returns and flips to Side B before the climb, and the sleeve carries the record into the end card.
- Transitions: dive through the hole, whip (twice), colour flood, plinth slide-in, 3D flip, year roll, hard cut into the claim. Seven seams, two hard cuts.
- Music: the original bossa loop from the portfolio site, looped once at bar 16 and faded under the end card. Sound effects: Pixabay-licensed clips bundled with the skill (needle click, whooshes, bass hit on 2024).
- Copy only from the CV, certificates and portfolio. "Four MSME programmes" counts PKM Berdampak, two batik sessions and Safina smoked fish.

**Measured vs looked**
- `hyperframes check`: no errors. Snapshots of every scene, every seam (−0.2 s to +0.2 s) and the phone sheet at 360 px were reviewed and fixed (tonearm over the title, year roll overlap, "The Climb" visible before the flip, lines held too briefly, 26 px labels).
- The sound was placed and level-checked by the tool, not heard by a person.

**Warnings kept on purpose**
- `line_unread` on the rolling venue names in the stage scene: it is a slot-machine roll, and the last venue holds.
- `gsap_repeated_fromto_without_baseline` / `overlapping_gsap_tweens` on the climb: the linter resolves every loop target as `#c-p1`; each step tweens its own element.

**Weakest shot and next step**
- The field scene (14.5 to 18.2 s) is type only on umber: it has no real photo of the MSME work. A photo of the batik or smoked fish sessions would make it as strong as the stage scene.
- The cover portrait is 582 px wide, so the end card sleeve is slightly soft.
