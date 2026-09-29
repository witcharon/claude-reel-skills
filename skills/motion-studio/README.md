# motion-studio

**Script to finished film, rendered from code.** The second half of a pair: [**reel-taste**](../reel-taste) writes the film and motion-studio builds it.

motion-studio builds the motion layer of a short film on top of a generated take (or from nothing):
- real UI tracked onto screens, with hands cut out so fingers stay in front;
- kinetic type on springs, a HUD, and mattes that put type behind things;
- velocity-matched seams and motion blur;
- a synthesized score and sound design, mixed to a measured −15 LUFS;
- a critique loop that looks at every rendered frame.

## How it works

A film is an HTML page with `window.renderAt(t)` that paints the exact frame for any moment. `scripts/render.mjs` drives it in headless Chromium, frame by frame, and pipes the frames into ffmpeg. It uses VideoToolbox on Apple Silicon and libx264 elsewhere. Every frame is a pure function of time, so any fix is an edit plus a re-render, and Claude can look at whatever it made.

The pipeline in `SKILL.md`:
1. Brief
2. Ingest
3. Retime plan and plates
4. Screen quads and mattes
5. Compose
6. Stills and critique
7. Score
8. Render
9. Mux
10. Final QC

A film only ships when every critique score is 8 or more.

## Its brief

The best brief is a **[reel-taste](../reel-taste)** package: the video-model prompt, the `time | picture | on screen | sound` motion notes, the signature move and the checks. Without one, motion-studio writes the motion notes itself and shows them first. If the brief doesn't say which language the on-screen copy is in, it asks.

## Files

- `SKILL.md`: the pipeline and the non-negotiables.
- `lib/motion.js`: closed-form springs and presets, `track()`, snap-and-hold, word entries and exits, nudge, seams, seeded randomness, camera shake, homography and `matrix3d`, grain, safe area, `plateIndex()`.
- `templates/edit.html`: the page skeleton.
- `scripts/`:
  - `ingest.py`, `plates.py`: the take, the retime and the graded plates;
  - `track_screen.py`, `keys.py`: screens, hands, hue keys, horizons;
  - `audio_kit.py`, `beats.py`, `mux.py`: the sound kit, beat measurement, two-pass loudnorm;
  - `render.mjs`, `qc.py`: the renderer and the looking tools.
- `references/`: `doctrine.md` (how things move), `footage.md` (working on generated takes), `sound.md`, `critique.md`.

Requirements: ffmpeg; Python 3.10+ with `numpy scipy opencv-python-headless pillow`; Node 18+ with `playwright-core @fontsource-variable/inter @fontsource/jetbrains-mono`; and Chromium (`npx playwright install chromium`) or Google Chrome.
