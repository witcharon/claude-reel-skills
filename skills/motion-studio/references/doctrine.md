# Motion doctrine

How things should move. Adapted from Movez's "How to build motion design studio with Opus 5.5" course, HyperFrames' motion-doctrine, cut-the-curve, seam-craft and oversized-cursor skills (Apache-2.0), and claude-animation-skill's notes (MIT), rewritten for our renderAt(t) films.

## Contents
1. Mass: springs, snap-and-hold
2. Seams: the vector law, carriers, causal motion
3. Performance: no idle wobble, stillness before the climax
4. Type
5. Craft: frame rate, depth, devices, drawing, camera
6. Catalog of moves
7. Banned defaults

## 1. Mass

- **Springs, not curves.** A fixed curve from A to B looks cheap; a spring accelerates, (maybe) overshoots and settles. Use `springP(t - t0, preset)`:

| Preset | Use | Overshoot |
|---|---|---|
| `snappy` [320, 30] | carets, toggles, leading edges | tiny |
| `ui` [220, 24] | chips, notifications, pills | a hair |
| `base` [170, 26] | cards, containers, camera | slight |
| `type` [150, 26] | big type | none |
| `heavy` [90, 20] | huge words landing, logo lockups | none, slow |
| `playful` [260, 14] | stickers, mascots | visible bounce |

- **Many targets, one value.** A progress bar that goes 18 → 34 → 52 → 100 uses `track(t, [[t0,18],[t1,34],…])`, one spring per change, never a restart.
- **Snap, then hold.** A state change that takes ~0.07 s and then sits still reads as intentional (a status flipping, a digit, a pop). Easing it over 0.5 s reads as a slideshow. Put the ease on the settle, not on the change.
- **Anticipation and overlap.** A small move the opposite way first (a word dips before it punches). Parts arrive at different times: body first, details 2–3 frames later.

## 2. Seams

- **Vector law.** How scene A exits decides how scene B enters: same axis, same direction, matched speed, and the cut lands *mid-motion* on both sides. Exit with `power4In`, enter with `power4Out` over the same distance and duration (`seam()`). Settling to rest before a cut, or starting from rest after it, is a dead beat.
- **One current.** Pick one dominant direction for ordinary transitions. Other directions are reserved and mean something: up = a reveal or conclusion, Z forward = deeper into the same thought, Z backward = an arrival, a burst = leaving a world. Never ping-pong directions on consecutive seams without a visible cause.
- **Carriers.** The eye follows objects. The best seams hand a concrete thing across the cut at the same position and speed: a cursor mid-path, a box that docks into the next layout, a word group, an opening slit. A crossfade has no carrier.
- **Causal motion.** Chain moves so each one is visibly launched by the last: click → squash → spring → impact → reveal. Effects start on the causing frame, not "shortly after". Big things react slower, small things snap.
- **Footage seams.** In generated takes the cut is often hidden in darkness or a flash. Give it a physical carrier the story already has, like an opening zipper, a closing lid or a door, with an exit that accelerates into the dark and an entry that bursts out of it.

## 3. Performance

- **No idle wobble.** A scene between its entry and exit must perform (something new every 2–4 s) or hold perfectly still. Floating, breathing and sine wobble on UI read as filler. A deliberate breathing light is fine when it *means* something, e.g. "asleep".
- **Stillness before the climax.** Freeze, empty or silence the beat before the big one (a 0.1–0.5 s vacuum). It is the strongest tool for making a hit land.
- **Loops out of phase.** Anything that repeats gets its own phase; a looping element starts mid-cycle.

## 4. Type

- Families, weights, case, tracking and colour come from the film's `style_guide.md` (`references/look.md`). This section only governs how type moves and sits.
- Words enter one at a time on the beat: they rise on the `type` spring and sharpen from a small blur (`wordIn`), and they exit by accelerating away (`wordOut`) so a following cut hits peak velocity.
- Cascades: a multi-word line uses `stagger(i, 0.06–0.14)`, heavier words taking longer steps. Never let every word land at once.
- Three big-type moments per film at most. Whisper-size copy has its own power.
- Contrast before style: dark type on bright grounds, light type on dark ones, and a shadow or plate only when the ground is busy. Measure centring; don't trust `left: 64px; width: 826px` tricks.
- Word spacing comes from the font: separate word wrappers with a real space, never with margins. Margins on top of the font's own space read as gaps, worst on a serif whose space is narrow.
- Tracking at display sizes is tight and set per family: a grotesk around −0.045 to −0.05em, a display serif around −0.02 to −0.03em. A serif left at 0 next to a tightly tracked sans looks loose and cheap.
- A two-line lockup (a sans line over a serif line) leans together: line-height 0.9–1.0, the serif about 1.2x the sans so the x-heights match, both lines at the same visual width or the serif slightly narrower. Set it once, measure it, and reuse it every time the line appears.
- Letter cascades: wrap each letter in an inline-block and track with an explicit `margin-right` (0 on the last letter). `letter-spacing` on inline-block letters is applied unpredictably (doubled, or dropped with `text-indent`) and pushes the line off-centre. Measure with `qc.py centre`.

## 5. Craft: frame rate, depth, devices, drawing, camera

The doctrine above makes motion correct; this section makes it look expensive. Pure motion graphics carry the whole film on craft, so it matters more there.

- **Frame rate and resolution.** Footage films follow the take (24 fps). Pure motion graphics render at **60 fps and 2x** (`render.mjs --fps 60 --scale 2 --sub 2`: drawn at 2160x3840, downscaled with Lanczos), which is where the smooth, crisp feel comes from. At 24 fps a motion-graphics film either sits still or jumps.
- **Motion blur is a judgement, not a setting.** `render.mjs --sub N --shutter s` renders N sharp copies across s of each frame and averages them. That reads as blur only while the copies are close; when something moves fast, they separate into a doubled or stepped edge. How to judge it:
  - **Measure where it matters.** `qc.py motion` lists the fast stretches with their on-screen speed and the gap the copies would leave at sub 2, 4 and 6. The number is a 95th percentile over the whole frame, so one fast object can dominate it, and a slow full-frame pan can hide behind it.
  - **Look at full size.** `qc.py strip <film> --at <t> --w 1080` around each fast stretch. Only edges you can actually see doubled or stepped are a problem. A lid slamming for three frames may read fine at 60 fps; a slow sideways pan that judders won't.
  - **Choose the remedy that fits the move:**
    - *More subframes* when the gap is a few px too wide (roughly up to 6 to 8 subframes). Render time grows about linearly, so re-render only those stretches (`render.mjs --from --to --sub 6`) and splice them in with `scripts/splice.py`.
    - *A real blur on the moving thing* when the speed is beyond what subframes can carry (the report says so): a CSS or canvas blur along the motion, a smear or trail drawn in, or a whip pan's blur on the whole layer. Subframes then only smooth what's left.
    - *Sharp frames* (`--sub 1`) for very fast, short hits at 60 fps: a crisp object reads as speed; stepped copies read as a glitch.
    - *A slower or eased move* when the speed itself is the problem: the eye can't follow it either.
  - **Starting points, then measure:** footage takes at 24 fps usually want sub 4 (the take has its own blur to match); pure motion graphics at 60 fps often need only sub 2 for calm scenes. Neither is a rule.
- **Keep it moving.** Between beats something is always travelling: a slow camera push or orbit, parallax between layers, a background gradient drifting. A hard cut to a static hold, then another, reads as a slideshow; check it with `qc.py motion`. Hold perfectly still only on purpose (the vacuum before a hit, a final card).
- **Depth.** Light comes from somewhere: soft contact shadows under objects, a long soft drop shadow under cards, gradients with a direction, glass (backdrop blur, a 1 px inner highlight) where a surface floats over colour. Flat shapes on a flat ground with no shadow read as clipart.
- **Product devices are real 3D.** A laptop, phone or watch is built in three.js, not stacked CSS boxes: rounded extruded slabs, `MeshPhysicalMaterial` aluminium (metalness 1, roughness ~0.3, light clearcoat), an environment map (`PMREMGenerator` + `RoomEnvironment`), ACES tone mapping, sRGB output, instanced keys, the screen as a `CanvasTexture`, the lid on a hinge pivot, and a real perspective camera that moves. When the project already has a device model, reuse it.
- **Drawing.** Commit to an illustration style that has its own shading and line (halftone, flat with a shadow colour, line-and-fill, 3D), or don't draw. A cup, a moon and a pillow as single-colour blobs make the whole film look cheap, however good the motion is.
- **Colour as a family.** Each scene can change colour, but the colours belong to one family with the brand's (shared value range, one accent, deliberate contrast). Unrelated saturated flats one after another feel like a template, unless the reference does exactly that with the craft to carry it.

## 6. Catalog of moves

| Move | What | When |
|---|---|---|
| Zoom-through | Push into an element until it fills the frame, cut at peak speed into the next scene already moving forward | Deeper into the same idea |
| Inverse zoom | The next scene arrives from far and lands | An arrival, a result, a logo |
| Rack-focus blur cut | Blur up (~10 px text, 18–20 px full frame) to the cut, blur down after | A calm change of subject |
| Waterfall entry | A title arrives as a cascade of words or letters, staggered by weight | Title cards, openers, end cards |
| Nudge | A group slides slow–fast–slow (10/65/25 %) to a new layout, no cut | Re-layouts, log lines pushing up |
| Slit/aperture | The picture opens from a line (lid, zipper, eyelid) over ~0.3 s (`out3`), readable across 4–6 frames; it shuts accelerating out (~0.18 s, `power4In`). No white flash on the open: it lifts the black around the slit to grey | Darkness seams in POV takes |
| Oversized cursor | A pointer about 7 % of the frame width enters from off-screen, clicks, and the click causes the next beat | UI films, scenes that read as static |
| World-locked label | A tag stuck to an object in the take, riding its track | Explaining what an object is or does |
| System state | A CRT-off collapse when something sleeps, a boot-up when it wakes | Machines as characters |

## 7. Banned defaults

A look nobody chose (the template's, or the last film's by default); a brand's signature redrawn worse than in its earlier films; product devices as flat CSS boxes; single-colour clipart; a motion-graphics film rendered at 24 fps; centred title on a gradient; everything fading in; corner labels and frame borders as decoration; glow on UI chrome; generic particle bursts; oversized UI text on a laptop; `will-change` on anything the camera scales (blurry text); a dead beat where nothing happens; sine wobble on UI; the same transition at every cut.
