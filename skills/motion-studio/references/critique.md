# Critique loop

Act as a harsh motion director, not a proud author. Run the loop on stills before the full render, and again on the final.

## Look
```
python3 $SKILL/scripts/qc.py sheet  out/video.mp4            # the whole film, 4 fps
python3 $SKILL/scripts/qc.py strip  out/video.mp4 --at <t>   # 12 frames around every cut and fast move
python3 $SKILL/scripts/qc.py phone  out/video.mp4            # 360 px wide: does it read on a phone?
python3 $SKILL/scripts/qc.py safe   out/video.mp4 --at <t,t,t>
python3 $SKILL/scripts/qc.py centre out/video.mp4 --at <t> --band <y0:y1>
python3 $SKILL/scripts/qc.py loud   out/video.mp4
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

## Hunt specifically for
- A frame that breaks the style guide, or looks like the template or the last film
- Decorative corner labels and frame borders that carry no information
- Text overlapping during swaps, or two titles on screen at once
- Anything sliding linearly instead of springing
- A frame with the previous scene's plate at a cut (strip every cut)
- Ghosting from subframes picking two plates
- Mattes that eat a letter or cut a finger
- Type sitting on busy detail without enough contrast
- A beat where nothing happens that isn't a deliberate vacuum
- Blurry scaled text (`will-change`, scaling a bitmap)

## Then
Write the scores and the three worst problems with timestamps in `out/review_log.md`, fix them, re-render only the affected stills or seconds, and score again. Stop when every score is 8+, then run the full render and repeat the look on the final.
