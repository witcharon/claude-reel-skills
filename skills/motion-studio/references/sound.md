# Sound

Sound is where code video starts feeling like a film. Build it on the picture's timeline with `audio_kit.py`.

## Layers
- **World:** the take's own audio, cut per scene with the same retime (`atrim` + `atempo`, one WAV per segment), 10 ms fades at each edge. Boost quiet takes, tame loud ones.
- **Score:** synthesized on the grid (pads, bass, drums, plucks, organ) or a supplied track measured with `beats.py`.
- **Effects:** clicks, zips, thumps, whooshes, impacts. Cue each one ~0.03 s before its contact frame (`Kit.EARLY`) and vary the pitch of repeats (`kit.vary()`) so typing and ticks don't sound pasted.
- **UI:** blips and chimes for HUD events. These live "inside" the product and are never muffled.

## Structural devices
- **The bed lands late.** Open the hook on typing, clicks and room tone alone, and bring the music in with the first cut or the first big action. It hits harder than music from frame one.
- **Perspective.** `openness(spans)` plus `perspective()` makes the world and the score sound as they would from where the camera is: muffled inside a bag or behind a door, bursting in when it opens.
- **Vacuum.** Duck everything for 0.1–0.5 s before the drop.
- **Tape-stop.** The score winds down to nothing when something sleeps or dies (`tape_stop`).
- **Nolan ending.** Organ, clock ticks speeding from 1/s to 1/4 s and a rising Shepard tone under the last scene, then `hard_cut` to silence, one tick 0.45 s later and the `horn` under a wide-tracked title card. Once a brand has used it, rest it unless asked.
- **Sidechain.** Duck pads and bass under a four-on-the-floor kick (`sidechain`).

## Levels
- `finish()` soft-limits and writes the WAV; `mux.py` sets the final loudness with a two-pass loudnorm to −15 LUFS integrated and −1.5 dBTP.
- Print section RMS/peaks (`sections=`) to check the dynamics you meant: inside vs. outside, silence vs. hit.
- You cannot listen. Say so, and ask the user to listen once on headphones before posting.
