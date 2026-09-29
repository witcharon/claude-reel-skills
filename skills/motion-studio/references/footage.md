# Working on a generated take

## Ingest and decide
- Run `ingest.py` and read the contact sheet. The numbers (cuts, dark runs, motion) only tell you where to look.
- Find the real beats in the picture (the lid shut, the zipper, the jump, the landing) and build the grid around them. The picture keeps its timing; the music bends to it by trimming darkness and tuning segment speeds.
- Generators deviate. For each deviation choose: keep it, cut around it, or hide it. For example, a shot that breaks the film's camera logic (a "POV from inside the bag" that suddenly films the bag from outside) gets cut, and you tell the user.

## Retiming (edit.json → plates.py)
- 1x scenes use the nearest frame. Speed-ups above 1.2x use `"blend": true` (a shutter average): smooth, and it hides awkward generated motion.
- Slow motion needs interpolated frames first: `ffmpeg -ss <t0> -i source.mp4 -vf "minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -start_number 0 frames/slow_%04d.png`. Fine for gentle motion (faces, canopies); it ghosts on fast limbs.
- Darkness between scenes needs no plates; the page draws black. Trim darkness so the next reveal lands on a beat.
- Grade lightly (contrast 0.08, saturation 1.06), upscale 720p takes to 1080 with Lanczos and a mild unsharp mask. Ask for 1080p takes when possible.

## Screen replacement
1. Measure the first frame's quad on a 4x zoom crop with a pixel grid: from the lid's outer top edge down to the display's bottom edge, which leaves the chin and its label untouched. The texture draws its own black bezel with rounded top corners.
2. `track_screen.py` tracks it (LK + RANSAC). Check its sheet: the quad must hug the lid edges. Once a hand grabs the lid from the right, use `--left-only-from`.
3. When the lid swings fast, tracking gives out: mark 3–5 quads by hand on zoomed crops (the right edge follows the display's bright edge line; the top sits just under the rim). Add blur that grows with the swing and brightness that falls, and fade the texture out as the lid closes.
4. Hands in front: `keys.hand_matte` on the plate inside the dilated quad, written as an RGBA cut-out layered above the screen. Key by warm hue plus brightness plus size, never brightness alone: grey title bars and yellow tents fool it.
5. UI texture size: a real terminal is about 90 columns on a 13–14" screen. At the hook, make it readable by opening on a frame where the screen is big in the take, not by zooming the plate: a punch-in on a 720p plate reads as a cheap zoom.

## Mattes
- **Canopy/sky:** `hue_key` with the subject's hue bands. Dark straps can stay in front, except where they would eat the logo's first letter (`dark_min_x`).
- **Horizon:** `horizon_fit` per frame, then `below_curve_matte`, to put text behind clouds or make a logo rise like the sun. Skip the columns where a ridge or subject pokes up. Draw the fit on frames and check it.
- Write cut-outs as RGBA PNGs at plate size and layer them above the text that sits "behind".

## Pitfalls that cost renders
- Folder names with non-ASCII characters: serve files with decoded URLs (render.mjs does this).
- The Chromium path changes when Playwright updates; render.mjs searches for it. If a render dies at launch, check `CHROME_PATH`.
- Subframe motion blur: choose plates with `floor(t*fps)`, never `round`, or subframes ghost two plates together.
- A frame at the exact cut time can land on the wrong side. Build cut times from the grid and check `strip` around every cut.
