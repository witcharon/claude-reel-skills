# Notice and credits

These skills are original work released under the MIT License (see `LICENSE`). They adapt ideas, not code, from the sources below. Each was rewritten in our own words and code for the `renderAt(t)` pipeline.

- **"How to build motion design studio with Opus 5.5 (Full-course)"** by Movez (@0xMovez), 27 September 2026. https://x.com/0xMovez/status/2104216919033192746
  - The seek(t) renderer route, closed-form springs with one spring per target change, sound synthesized on the picture's timeline, the 8+ critique loop, the director's-brief skeleton and generate-then-trace.
- **HyperFrames** by HeyGen, Apache License 2.0. https://github.com/heygen-com/hyperframes
  - The `motion-doctrine`, `cut-the-curve`, `seam-craft` and `oversized-cursor` agent skills informed `skills/motion-studio/references/doctrine.md` and the seam and cascade helpers in `skills/motion-studio/lib/motion.js`: the vector law, carriers, one dominant direction, no idle wobble, springs over easing curves and the oversized cursor.
  - No HyperFrames source files are included.
- **claude-animation-skill** by buildwithhanif, MIT License. https://github.com/buildwithhanif/claude-animation-skill
  - The habit of looking (contact sheets, 12-frame strips around fast moments) behind `skills/motion-studio/scripts/qc.py`, and sound synthesized from the same timeline as the picture.
- **skill-creator** by Anthropic. https://github.com/anthropics/skills
  - Used to write and evaluate `reel-taste`.

Video footage in the examples was generated with Seedance 2.5 on Loomshot (https://loomshot.ai).
