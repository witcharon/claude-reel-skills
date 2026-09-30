# What the motion layer can build (write scripts for it)

With footage, the edit is built frame by frame on top of the take: tracked screens, mattes, HTML/Canvas type and HUD, occasionally three.js, and synthesized sound mixed with the take's own audio. Without footage, every scene is drawn in code (SVG, canvas, three.js): the product's UI rebuilt as components, generative patterns, characters. Scripts should ask for things in this list and supply what each needs.

## Reliable moves and what they need from the footage

| Move | Needs in the take |
|---|---|
| Real UI replaced onto a laptop or phone screen | Screen facing the camera, dark UI, unobstructed for ~2 s; hands may come in front later (they get keyed back in front) |
| Text or logo behind the subject | A clean background that separates by colour: sky, snow, space, a saturated canopy |
| Horizon / limb effects (logo rising like the sun) | A clear, fairly stable horizon line |
| World-locked labels on objects | The objects visible and not too blurred |
| HUD / diegetic UI | Nothing; it lives in screen space |
| Speed ramps, slow motion | Slow motion needs gentle motion (frame interpolation) |
| Hiding cuts | Darkness, flash or whip frames around each cut |
| 3D product shot (reveal, lid close) | Nothing, but use it sparingly; full-CG reels flopped |

## Look and type

- There are no typography defaults. Palette, type, texture and transitions come from the film's look direction, which motion-studio turns into `style_guide.md` (from a reference's grammar, or reasoned from the brief).
- What holds for any look: words enter on the beat, one idea at a time; the product's UI at a real, readable size (laptop UI at real terminal size, ~90 columns, never oversized); contrast before style.
- The end card is designed in the film's look: the brand, one line about the product, the CTA.

## Platform safe zones (1080×1920)

- Keep all text between **y 250 and y 1440**: the top has the app bar, the bottom has the caption, username and audio.
- The right-hand buttons sit at roughly **y 880–1600**. Lines in that band stay within **x 190–890**.
- **Centre on the frame (x 540), not on the safe column.** A 64 px left shift was noticed immediately.
- Decorative frames (viewfinder brackets) may bleed into the zones; text may not.

## Timing

- Build on a beat grid (120 BPM → 0.5 s) and put the story beats on it: the lid shut, the zipper open, the drop.
- No punch-in zoom at the start; open full frame.
- Typing and key clicks follow the finger strikes visible in the take, not a fixed speed.
- Hold the end card ~6 s; the CTA appears ~1.7 s into it.

## Sound

- Mix the take's own ambience with synthesized score and effects; perspective tricks (muffled/unmuffled) are cheap and strong.
- Target about −15 LUFS integrated and true peak ≤ −1 dBFS.
- The mix is measured, not listened to. Always tell the user to listen once on headphones before posting.

## CTA

- When links go out through a comment keyword (ManyChat-style), the video either says "check the caption for the link" or names the keyword itself (comment “motion”), and the caption says "Comment <WORD> and we'll DM you the link". Don't lead with the URL.
