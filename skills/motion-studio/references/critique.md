# Critique loop

Act as a harsh motion director, not a proud author. Run the loop on stills before the full render, and again on the final.

## Look
```
python3 $SKILL/scripts/qc.py sheet  out/video.mp4            # the whole film, 4 fps
python3 $SKILL/scripts/qc.py strip  out/video.mp4 --at <t>   # 12 frames around every cut and fast move
python3 $SKILL/scripts/qc.py phone  out/video.mp4            # 360 px wide: does it read on a phone?
python3 $SKILL/scripts/qc.py safe   out/video.mp4 --at <t,t,t>
python3 $SKILL/scripts/qc.py centre out/video.mp4 --at <t> --band <y0:y1> [--save]   # measured against the local background
python3 $SKILL/scripts/qc.py loud   out/video.mp4
python3 $SKILL/scripts/qc.py motion  out/video.mp4                      # fluidity: still frames, jumps, the biggest jumps with times
python3 $SKILL/scripts/qc.py compare out/video.mp4 --ref <film>.mp4    # side by side with the reference and the brand's best earlier film
```
Open every image and look at it properly.

## Score 1–10
1. Hook in the first 2 s, sound off
2. Readability at phone size
3. Motion quality: springs, no sliding, no dead frames
4. Seams: carriers, matched vectors, no pops or doubled frames at cuts
5. Variety: something new every 2–4 s, one signature move
6. Composition and safe area: centred on 540, nothing in the danger zones
7. Brand and product accuracy: the real UI at a real size, honest states
8. Sound sync: effects on contact frames, the structure audible in the section levels
9. Look: every frame belongs to the film's `style_guide.md`, and nothing reads as a default
10. Craft: next to the reference and the brand's best earlier film (`qc.py compare`), does it look as finished: depth, light, materials, drawing, type? Score it against them, not against your intentions.
11. Fluidity (`qc.py motion`): for motion graphics, few frames sit still outside deliberate holds and no jumps beyond the planned cuts; compare the numbers with the reference's

Score honestly. A score of 8+ means you would put it next to the reference without apology; if you can't say why it's an 8 with the compare sheet open, it isn't one.

## Hunt specifically for
- A frame that breaks the style guide, or looks like the template or the last film
- The brand's signature (lockup, end card, device) looking worse than in its earlier films
- Flat clipart, shapes without light or shadow, devices built from flat boxes
- A run of static holds joined by hard cuts in a motion-graphics film
- Decorative corner labels and frame borders that carry no information
- Text overlapping during swaps, or two titles on screen at once
- Anything sliding linearly instead of springing
- A frame with the previous scene's plate at a cut (strip every cut)
- Ghosting from subframes picking two plates
- Doubled or stepped edges on fast moves: strip each fast stretch from `qc.py motion` at full size (`--w 1080`) and judge what you see, then pick the remedy in the doctrine's craft section
- Mattes that eat a letter or cut a finger
- Type sitting on busy detail without enough contrast
- A beat where nothing happens that isn't a deliberate vacuum
- Blurry scaled text (`will-change`, scaling a bitmap)

## Then
Write the scores and the three worst problems with timestamps in `out/review_log.md`, fix them, re-render only the affected stills or seconds, and score again. Stop when every score is 8+, then run the full render and repeat the look on the final.
