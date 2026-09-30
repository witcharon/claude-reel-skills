# Motion doctrine

How things should move. Adapted from Movez's "How to build motion design studio with Opus 5.5" course, HyperFrames' motion-doctrine, cut-the-curve, seam-craft and oversized-cursor skills (Apache-2.0), and claude-animation-skill's notes (MIT), rewritten for our renderAt(t) films.

## Contents
1. Mass: springs, snap-and-hold
2. Seams: the vector law, carriers, causal motion
3. Performance: no idle wobble, stillness before the climax
4. Type
5. Catalog of moves
6. Banned defaults

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
- Letter cascades: wrap each letter in an inline-block and track with an explicit `margin-right` (0 on the last letter). `letter-spacing` on inline-block letters is applied unpredictably (doubled, or dropped with `text-indent`) and pushes the line off-centre. Measure with `qc.py centre`.

## 5. Catalog of moves

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

## 6. Banned defaults

A look nobody chose (the template's, or the last film's by default); centred title on a gradient; everything fading in; corner labels and frame borders as decoration; glow on UI chrome; generic particle bursts; oversized UI text on a laptop; `will-change` on anything the camera scales (blurry text); a dead beat where nothing happens; sine wobble on UI; the same transition at every cut.
