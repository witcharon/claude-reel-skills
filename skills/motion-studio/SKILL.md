---
name: motion-studio
description: Build a short film in code, either as pure motion graphics (no footage) or as a motion layer on a generated take (Seedance or similar): a look decided per film in style_guide.md (from a reference's grammar or reasoned from the brief), a shot list on the beat grid, real UI (tracked onto screens or rebuilt as components), kinetic type on springs, mattes, velocity-matched seams, motion blur, synthesized score and sound design, a measured mix, and a critique loop over the rendered frames. Use it whenever someone asks for a motion video, motion graphics, a launch or promo video, a showreel, an animated explainer, hands over a take to "do the motion on", or asks to edit/remake/re-render a reel, add titles, screen replacement, sound or an end card, even if they only say "make the video". Pairs with reel-taste, which does the concept and script; this skill executes it and calls on reel-taste when there is no brief.
---

# Motion Studio

A film here is a **program**: an HTML page with `window.renderAt(t)` that paints the exact frame for any moment, rendered by headless Chromium frame by frame and encoded by ffmpeg. Sound is synthesized on the same timeline. Because every frame is a pure function of time, any fix is an edit plus a re-render of the affected seconds, and you can look at any frame you made. **Looking is the method**: the first render is never the film.

The skill has no house style. How things move (springs, seams, safe area) and how finished they look (frame rate, depth, real 3D devices, type) are fixed craft; what the film looks like is decided per film, from the brief, the brand's earlier films and a reference, and written down before anything is composed.

Scripts live in `scripts/`, the browser library in `lib/motion.js`, a neutral page skeleton in `templates/edit.html`. Read `references/look.md` before deciding the look, `references/doctrine.md` before composing motion, `references/footage.md` when working on a take, `references/sound.md` before scoring, and `references/critique.md` before judging a render.

## Project layout

One folder per film, next to the others (e.g. `promo/src/<film>/`), with the finished MP4 written to the promo root:

```
<film>/
  brief.md              the concept and motion notes (a reel-taste package, or written with its process)
  style_guide.md        the look: palette, type, space, texture, motion grammar, sound   (step 2)
  shotlist.md           every shot on the beat grid                                    (step 3)
  refs/                 reference frames/videos and the frames extracted from them
  assets/               the product's real logo, colours, fonts, UI captures
  source.mp4            the take, if there is one (copy it in; never edit the user's original)
  node_modules -> ../node_modules      (playwright-core, @fontsource/*)
  lib/motion.js         copied from the skill (the film must be self-contained)
  frames/, plates/, edit.json          takes only (ingest.py, plates.py)
  edit.html             the film                                 (from templates/edit.html)
  audio.py              the score, built on scripts/audio_kit.py
  out/                  stills/, qc/, video.mp4, score.wav, review_log.md
  README.md             how to rebuild it, in a few commands
```

`SKILL=~/.claude/skills/motion-studio`. Python needs numpy, scipy, opencv-python-headless and pillow; Node needs playwright-core and a Chromium (render.mjs finds the newest Playwright Chromium or Google Chrome), and `three` for 3D devices.

## Pipeline

1. **Brief: the concept is reel-taste's job.** With a reel-taste package, use it. Without one, don't jump from the request to motion notes: load reel-taste (it covers pure motion graphics as well as footage films) and run its process: find the product's verb, diverge, pick, script, taste-audit. If reel-taste isn't installed, still hold the concept to its bar: it reads in one second with the sound off, the product's verb is the turning point, there is one signature move, the copy is specific, and nothing is a generic default. Then check two things before any work:
   - **Deliverables.** How many films, with footage or pure motion, length, format. When a request can be read two ways ("a motion video and one with footage" is one film or two?), ask.
   - **Language** of the on-screen copy (titles, labels, HUD, UI text, end card, CTA). If the brief doesn't say, ask instead of assuming one.
2. **Look → `style_guide.md`** (`references/look.md`). First the brand's own films and assets: find its earlier films in the project, make a contact sheet of the best one, and list what carries over (a 3D device model, the signature lockup and end card, the colour family). The signature comes back at the same quality or better; a reference changes the grammar, not the brand. With a reference (a frame, a video, an account, a folder, a named style), extract frames (`ffmpeg -vf fps=2`), study them and write the guide from the reference's *grammar*: palette in hex, type, shot lengths, transitions, camera, texture, how text enters and leaves. Never take its content, logos or characters, and match its craft level (depth, light, materials, drawing), not only its grammar. Without a reference, reason the look from the brief and write the reasoning down. When the project already has a guide (a brand whose style has settled), start from it and say what this film keeps and changes. Collect the product's real assets (logo, colours, fonts, UI via Playwright or files) into `assets/` and list them.
3. **Shot list → `shotlist.md`** on the beat grid (120 BPM → 0.5 s, or a supplied track's beats from `scripts/beats.py`): every shot with its time, picture, on-screen copy, motion and transition, and sound. For a take, this is the motion notes table. Show the style guide and the shot list and get an OK before writing code when the user is around; a rejection means rewriting the shot list, not the code.
4. **Takes only: ingest.** `python3 $SKILL/scripts/ingest.py source.mp4` gives frames, a labelled contact sheet, cuts, dark runs and an audio profile. Open the contact sheet and *look*: where the real beats are, where the generator deviated from the prompt, and what to cut. Deviations are editorial decisions; tell the user which ones you made and why.
5. **Takes only: plan time and film data.** Write `edit.json` (scenes at 1x, darkness trimmed to the beat, speed ramps with shutter blend, slow motion from interpolated frames), run `python3 $SKILL/scripts/plates.py edit.json`, then screen quads (`scripts/track_screen.py`, hand-marked quads for fast swings), mattes (`scripts/keys.py`) and whatever else the film needs, written into `plates/meta.json`. Pure motion films skip steps 4–5: every scene is a function of time and every asset is drawn in code or supplied.
6. **Compose `edit.html`** from `templates/edit.html` with `lib/motion.js`: the guide's palette and type go into the template's CSS variables, its fonts get installed (`npm i @fontsource/<family>`). Follow the doctrine, including its craft section: springs, not easing curves; one signature move; seams that carry the eye; something always travelling between beats; depth and light; product devices in three.js (reused when the project has one); type inside the safe area and centred on x = 540.
7. **Stills first.** `node $SKILL/scripts/render.mjs --root . --stills …` at every beat, then run the critique loop (`references/critique.md`) on those stills, against the style guide and side by side with the reference and the brand's best earlier film (`qc.py compare`), before any full render. A draft render (`--capture jpeg`) plus `qc.py motion` shows whether it flows before the final one. Log scores and the three worst problems in `out/review_log.md`.
8. **Score.** `audio.py` on `audio_kit.py`: the take's own sound per scene if there is one, the score on the grid, effects cued ~0.03 s early, perspective and silence as structure. It writes `out/score.wav`.
9. **Render.** Footage films follow the take: `node $SKILL/scripts/render.mjs --root . --fps 24 --from 0 --to <dur> --sub 4 --shutter .5 --out out/video.mp4`. Pure motion graphics render at 60 fps, drawn at 2x and downscaled: `--fps 60 --scale 2`. `--sub` (subframes) and `--shutter` set the motion blur: start from the doctrine's starting points, then let `qc.py motion` and a full-size strip around each fast stretch decide where it needs more subframes, a real blur, sharp frames or a slower move (doctrine, Craft: motion blur). Re-render only the stretches that need it and splice them in with `scripts/splice.py`. Subframes give real motion blur; pages that show plates must pick them with `plateIndex()` (floor, not round). Run long renders in the background. Capture is nearly all the cost, so frames are grabbed through CDP with `optimizeForSpeed` by several pages in parallel (`--workers`, default half the cores, max 6), written to ffmpeg in order; on an M4 that took a 4-subframe frame from 1.41 s to 0.46 s. `--capture jpeg` is ~3x faster again (SSIM ~0.99), good for drafts. Encoding uses VideoToolbox when available, else libx264. The render goes to `<out>.partial.mp4`, becomes `<out>` only when ffprobe counts every frame, and any failure (capture timeouts retry 3x) exits non-zero with no output file. To change only part of the film, render that range and splice it in with `scripts/splice.py`, which keeps the frame count and verifies it.
10. **Mux.** `python3 $SKILL/scripts/mux.py out/video.mp4 out/score.wav <final>.mp4` masters to −15 LUFS with a 4x-oversampled true-peak limiter under −1.5 dBTP, re-measures after the AAC encode, and exits non-zero if it misses the target or if the video is shorter than the score (a render that stopped early).
11. **Critique the final.** `qc.py sheet | strip | phone | safe | centre | loud | motion | compare`, then score and fix the worst three. Score against the reference and the brand's earlier film, not against your intentions. Deliver only when every score is 8+.

## Non-negotiables

- **A look per film, decided before composing.** It comes from a reference's grammar or is reasoned from the brief, and it is written in `style_guide.md`. Never the template's look, never the last film's look by default.
- **Take the grammar, never the content.** From a reference take pacing, type, palette logic and transitions; never its subject, logos, characters or copy.
- **Pure function of time.** No `Math.random` (use `rng`/`hash`), no timers, no CSS transitions, no state carried between frames. Load images with `setImg` inside the async `renderAt`.
- **Real UI, real size.** The product's interface comes from what it really shows (captured, or rebuilt faithfully as components), at a realistic size. Never an invented or oversized screen.
- **Safe area.** Text only between y 250 and 1440; in the right-button band (y 880–1600) keep it within x 190–890; centre on x 540. Measure it (`qc.py centre`), don't eyeball it.
- **Springs on everything that moves** (`SPRING` presets): UI may overshoot a hair, type never does.
- **One signature move per film.** Everything else in the motion layer serves it.
- **Craft at the level of the reference and the brand's earlier films.** Pure motion graphics at 60 fps and 2x; devices in real 3D; light, shadow and depth; no flat clipart; the brand's signature never redrawn worse than before.
- **Look before you ship.** Contact sheet, strips around fast moments, a phone-size pass and the safe-zone overlay, every time.
- **Honest delivery.** Say what was measured (LUFS, peaks, centring) and what wasn't (you did not listen). Name the editorial deviations from the script and anything staged (a recreated UI session is not a screen recording). Keep the user's original files untouched and write new versions under new names unless they ask to overwrite.

## Delivering

Report in this order: where the file is and its specs; what changed versus the script or the previous version (only what matters); anything the user must check by eye or ear; and where the source, style guide and README live.
