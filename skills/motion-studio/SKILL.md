---
name: motion-studio
description: Build the motion layer of a short film in code, on top of a generated take (Seedance or similar) or from nothing: real UI tracked onto screens, kinetic type on springs, a HUD, mattes that put type behind things, velocity-matched seams, motion blur, synthesized score and sound design, a measured mix, and a critique loop over the rendered frames. Use it whenever someone hands over a video take to "do the motion on", asks to edit/remake/re-render a reel or promo, add titles, screen replacement, sound or an end card to AI footage, or to make a code-rendered motion video, even if they only say "make the video" or "put the UI on the laptop". Pairs with reel-taste (which writes the script); this skill executes it.
---

# Motion Studio

A film here is a **program**: an HTML page with `window.renderAt(t)` that paints the exact frame for any moment, rendered by headless Chromium frame by frame and encoded by ffmpeg. Sound is synthesized on the same timeline. Because every frame is a pure function of time, any fix is an edit plus a re-render of the affected seconds, and you can look at any frame you made. **Looking is the method**: the first render is never the film.

Scripts live in `scripts/`, the browser library in `lib/motion.js`, a page skeleton in `templates/edit.html`. Read `references/doctrine.md` before composing motion, `references/footage.md` when working on a take, `references/sound.md` before scoring, and `references/critique.md` before judging a render.

## Project layout

One folder per film, next to the others (e.g. `promo/src/<film>/`), with the finished MP4 written to the promo root:

```
<film>/
  source.mp4            the take (copy it in; never edit the user's original)
  node_modules -> ../node_modules      (playwright-core, @fontsource/*)
  lib/motion.js         copied from the skill (the film must be self-contained)
  frames/               src_%04d.png, slow_%04d.png            (ingest.py, ffmpeg)
  plates/               p_%04d.jpg, cut-outs, meta.json          (plates.py + film scripts)
  edit.json             the retime plan (segments)               (you write it)
  edit.html             the film                                 (from templates/edit.html)
  audio.py              the score, built on scripts/audio_kit.py
  out/                  stills/, qc/, video.mp4, score.wav
  README.md             how to rebuild it, in six commands
```

`SKILL=~/.claude/skills/motion-studio`. Python needs numpy, scipy, opencv-python-headless and pillow; Node needs playwright-core and a Chromium (render.mjs finds the newest Playwright Chromium or Google Chrome).

## Pipeline

1. **Read the brief.** Usually a reel-taste package: footage prompt, motion notes table, the signature move, the checks. If there is none, write the motion notes table yourself first (time | picture | on screen | sound) and show it. Check that the brief says which language the on-screen copy is in (titles, labels, HUD, UI text, end card, CTA); if it doesn't, ask the user before composing instead of assuming one.
2. **Ingest the take.** `python3 $SKILL/scripts/ingest.py source.mp4` gives frames, a labelled contact sheet, cuts, dark runs and an audio profile. Open the contact sheet and *look*: where the real beats are (the lid shut, the zipper, the jump), where the generator deviated from the prompt, and what to cut. Deviations are editorial decisions; tell the user which ones you made and why.
3. **Plan time.** Put story beats on a grid (120 BPM → 0.5 s) or on a supplied track's measured beats (`scripts/beats.py`). Write `edit.json`: scenes at 1x, darkness trimmed to the beat, speed ramps with shutter blend, slow motion from interpolated frames. Then `python3 $SKILL/scripts/plates.py edit.json`.
4. **Film-specific data.** Screen quads (`scripts/track_screen.py`, then hand-marked quads for fast swings), mattes (`scripts/keys.py`: hands, hue keys, horizons), sun positions and so on, written into `plates/meta.json` by a small film script.
5. **Compose `edit.html`** from `templates/edit.html` with `lib/motion.js`. Follow the doctrine: springs, not easing curves; one signature move; seams that carry the eye; type inside the safe area and centred on x = 540.
6. **Stills first.** `node $SKILL/scripts/render.mjs --root . --stills …` at every beat, then run the critique loop (`references/critique.md`) on those stills before any full render.
7. **Score.** `audio.py` on `audio_kit.py`: the take's own sound per scene, score on the grid, effects cued ~0.03 s early, perspective and silence as structure. It writes `out/score.wav`.
8. **Render.** `node $SKILL/scripts/render.mjs --root . --fps 24 --from 0 --to <dur> --sub 4 --shutter .5 --out out/video.mp4`. Subframes give real motion blur; the page must pick plates with `plateIndex()` (floor, not round). Run long renders in the background. Encoding uses the Apple Media Engine (VideoToolbox) when available and falls back to libx264; on an M4 this made a 31 s film ~28% faster with no visible difference. Capture, not encoding, is ~95% of render time, so fewer subframes on calm scenes is the next lever.
9. **Mux.** `python3 $SKILL/scripts/mux.py out/video.mp4 out/score.wav <final>.mp4` does a two-pass loudnorm to −15 LUFS / −1.5 dBTP.
10. **Critique the final.** `qc.py sheet | strip | phone | safe | centre | loud`, then score and fix the worst three. Deliver only when every score is 8+.

## Non-negotiables

- **Pure function of time.** No `Math.random` (use `rng`/`hash`), no timers, no CSS transitions, no state carried between frames. Load images with `setImg` inside the async `renderAt`.
- **Real UI, real size.** The product's interface is drawn from what it really shows, at a realistic size on a tracked screen. Never an oversized or invented screen.
- **Safe area.** Text only between y 250 and 1440; in the right-button band (y 880–1600) keep it within x 190–890; centre on x 540. Measure it (`qc.py centre`), don't eyeball it.
- **Springs on everything that moves** (`SPRING` presets): UI may overshoot a hair, type never does.
- **One signature move per film.** Everything else in the motion layer stays quiet.
- **Look before you ship.** Contact sheet, strips around fast moments, a phone-size pass and the safe-zone overlay, every time.
- **Honest delivery.** Say what was measured (LUFS, peaks, centring) and what wasn't (you did not listen). Name the editorial deviations from the script. Keep the user's original files untouched and write new versions under new names unless they ask to overwrite.

## Delivering

Report in this order: where the file is and its specs; what changed versus the script or the previous version (only what matters); anything the user must check by eye or ear; and where the source and README live.
