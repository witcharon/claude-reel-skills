# motion-studio

**Script to finished film, rendered from code.** The second half of a pair: [**reel-taste**](../reel-taste) writes the film and motion-studio builds it.

motion-studio builds a short film in code, as pure motion graphics or as a motion layer on a generated take. It has no house style: each film's look is decided in `style_guide.md`, from a reference's grammar or reasoned from the brief. Then:
- real UI tracked onto screens, with hands cut out so fingers stay in front;
- kinetic type on springs, a HUD, and mattes that put type behind things;
- velocity-matched seams and motion blur;
- a synthesized score and sound design, mixed to a measured −15 LUFS;
- a critique loop that looks at every rendered frame.

## How it works

A film is an HTML page with `window.renderAt(t)` that paints the exact frame for any moment. `scripts/render.mjs` drives it in headless Chromium with several pages in parallel and pipes the frames, in order, into ffmpeg; a render that fails or comes up short exits non-zero and leaves no file. It uses VideoToolbox on Apple Silicon and libx264 elsewhere. Every frame is a pure function of time, so any fix is an edit plus a re-render, and Claude can look at whatever it made.

The pipeline in `SKILL.md`:
1. Brief (reel-taste's package, or its process run first)
2. Look → `style_guide.md`
3. Shot list → `shotlist.md`, OK before code
4. Ingest (footage)
5. Retime, plates, screen quads and mattes (footage)
6. Compose
7. Stills and critique
8. Score
9. Render
10. Mux
11. Final QC

A film only ships when every critique score is 8 or more.

## Its brief

The best brief is a **[reel-taste](../reel-taste)** package: the concept, the look direction, the `time | picture | on screen | sound` motion notes, the signature move and the checks. Without one, motion-studio runs reel-taste's process first, so the concept gets the same taste pass. It asks when the deliverables are ambiguous and which language the on-screen copy is in.

## Files

- `SKILL.md`: the pipeline and the non-negotiables.
- `lib/motion.js`: closed-form springs and presets, `track()`, snap-and-hold, word entries and exits, nudge, seams, seeded randomness, camera shake, homography and `matrix3d`, grain, safe area, `plateIndex()`.
- `templates/edit.html`: a neutral page skeleton; the look goes into its CSS variables.
- `scripts/`:
  - `ingest.py`, `plates.py`: the take, the retime and the graded plates;
  - `track_screen.py`, `keys.py`: screens, hands, hue keys, horizons;
  - `audio_kit.py`, `beats.py`, `mux.py`: the sound kit, beat measurement, a true-peak-safe master to −15 LUFS that verifies itself;
  - `render.mjs`, `qc.py`: the renderer and the looking tools.
- `references/`: `look.md` (deciding the look, `style_guide.md`), `doctrine.md` (how things move), `footage.md` (working on generated takes), `sound.md`, `critique.md`.

Requirements: ffmpeg; Python 3.10+ with `numpy scipy opencv-python-headless pillow`; Node 18+ with `playwright-core @fontsource-variable/inter @fontsource/jetbrains-mono`; and Chromium (`npx playwright install chromium`) or Google Chrome.
