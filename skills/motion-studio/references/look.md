# The look: style_guide.md

Every film gets its own `style_guide.md` before anything is composed. It is where the film's look is decided, on purpose, and it is what the compose step and the critique check against. There is no house style in this skill: not in the doctrine, not in the template. The motion rules (springs, seams, safe area) say how things move; this file says what they look like.

Without it, a model falls back to its default: centred text on a gradient, everything fading in, or the last film's look reused because it was lying around. When hundreds of people give the same prompt, the results rhyme ("brief contagion"); the way out is a look that comes from somewhere specific. Naming a look beats describing one, and a reference beats both.

## Where the look comes from

**A reference, when there is one.** Ask for one if the brief has none: a frame, a video, an account, a folder of past work, a named style ("PC-98", "Swiss grid", "a Stripe launch film"). Then derive the look from it:
- **A video:** extract one frame every half second and read them before writing anything. `ffmpeg -i refs/ref.mp4 -vf "fps=2,scale=480:-1" refs/frames/f_%03d.png`, then tile them into a sheet and look. Write the pacing shot by shot: how long each idea holds, what carries each cut, where the palette changes, how type enters and leaves, what the camera does.
- **A frame:** say what to take (palette, type, grain, layout) and what not to take (the subject, the logo).
- **A library** (images, past films): write the guide from what the pieces share, then name what this film adds.

Take the **grammar** of the reference (pacing, type, palette logic, transitions, texture), never its content, logos or characters. Then match its **craft level**: the depth, lighting, materials and drawing quality that make it look the way it does. Taking a reference's colour flips without its 3D mascots and shadows gives a cheaper film than either. If its craft is out of reach in code, pick a grammar you can execute at that level instead. A re-run of the same brief with a different library gives a completely different film; that is the point.

**Reasoning, when there is none.** There is no menu to pick from. Reason from the brief and write the reasoning down, in a few lines:
- What does the product feel like to use? The look should feel like that (precise, playful, heavy, quiet, tactile).
- Who is watching, where, and what does their feed look like? Stand out from it, not from nothing.
- What is the concept's signature move? The look should serve it (a reveal line wants a hard two-tone split; a detection box wants CCTV chrome; a one-shape morph wants a calm canvas).
- What must be read? The copy, the UI, a number. Pick type that carries it at phone size.
- What would the obvious choice be? Name it, then decide whether to use it or beat it.

**The brand's own films and assets come first.** Before deciding anything, find what the brand has already made: earlier films in the project (the promo root's MP4s, `src/*/`), its site, its app. Make a contact sheet of the best earlier film and look at it, and list what can be reused: a 3D device model, the signature lockup and end card, the colour family, the type pairing, a mascot or icon. Two rules follow:
- **The signature carries over at the same quality or better.** If an earlier film ends on "Close the lid. *Keep it running.*" as a tight lockup on a gradient, this film's version may be restaged, never redrawn worse. Reuse the code when you can.
- **A reference changes the grammar, not the brand.** A reference tells you how to pace, cut and stage; the brand's signature, colours and devices stay recognisable.

**A project whose style has settled.** Brands grow a style over time. When the project already has a `style_guide.md` or earlier films, start from them and write what this film keeps and what it changes. Keeping is fine when it is a decision; drifting into the same film again is not.

**The product's own assets.** Whatever the look, the product appears as itself: collect its real logo, colours, fonts and UI (Playwright captures from its site, or files the user gives) into `assets/`, list what you found, and animate the real thing. Never redraw a product's UI from imagination.

## What style_guide.md contains

```markdown
# <film>: style guide
Source: <reference(s): what to take / not take>   or: <the reasoning, in 3-5 lines>
Brand: <earlier films looked at>; <assets reused (device model, signature lockup, end card)>

## Palette
<hex values with roles: ground, ink, accent, UI>; how it changes across scenes (a new ground per scene? a flip on the drop?)

## Type
<display family, weight, case, tracking; text family; UI/mono family>; sizes at 1080 wide; how type enters and leaves in this film
Fonts: <@fontsource package names to install>

## Space
<grid, margins, where type sits, chrome if any (timecode, labels) and why it's there>

## Texture and shape
<flat, grain, halftone, dither, paper, riso, watercolour, glass>; <shape language>; illustration, character or 3D style if any

## Craft
<frame rate and scale (60 fps · 2x for pure motion graphics)>; <depth: light direction, shadows, glass>; <devices: three.js model, reused from <film> or built>; <illustration style, or none>

## Motion
<the signature move>; <transition family: cuts on the beat, zoom-through, morph, wipes, match cuts>; <shot lengths>; <a technique per scene? which?>

## Sound
<the score's character, tempo, the hits>

## Take / don't take
<from the reference>

## Checks
<3-5 things the critique must verify for this look>
```

Then install the fonts it names (`npm i @fontsource/<family>` in the promo root, `@font-face` in `edit.html`), put the palette and type into the template's CSS variables, and write `shotlist.md` in that style. When a frame breaks the guide, fix the frame or change the guide on purpose; don't let the film drift.

## What the strong references have in common

From the code-made films that travelled (UI showcases, product launches, showreels, music videos, story shorts). These are observations to reason with, not styles to copy:
- **One committed visual world.** Paper cut-outs inside a TikTok feed, PC-98 pixel art, a halftone 3D mascot beside real product cards, watercolour, a single black pill morphing on warm grey, a design-system showreel that flips palette every scene. Each film picks one and never leaves it.
- **A recurring carrier.** One element the eye follows through the whole film: a curved horizon repeated across different materials, an asterisk, a pill, a character. It is also what carries the cuts.
- **One idea per 1.5–3 s,** each one nameable (a morph, a chart, a pattern, a product card, a number), usually changing on the downbeat.
- **Real product UI,** rebuilt as components and driven by a cursor doing real actions, rather than screenshots sliding around.
- **Type as a decision.** A display face and a text face with clear jobs; where a second voice is used (a script or serif accent word), it is there for one word per line, not everywhere.

And what is already turning into a cliché, so choose it only on purpose: a grotesk headline with one italic-serif accent word; timecodes and frame counters in the corners; decorative corner labels and frame borders; everything assembling from blurred-in cards; a one-shape morph for a product that has no UI story.

## Films with no footage

Pure motion graphics skip ingest, plates and tracking: every scene is a function of time and every asset is drawn in code (SVG, canvas, three.js) or supplied. They carry the whole film on design, so the guide matters more, not less:
- **A technique per idea.** A viewer should be able to name what each scene shows and why it's there.
- **Rebuild the product's UI as components** (cards, charts, checkouts, terminals) at a readable size.
- **Generative pieces stay deterministic.** Patterns, particles and point clouds use `rng(seed)` and time, never `Math.random`, so any frame renders alone.
- **Carriers across cuts matter more.** There is no footage to hide a cut in: hand a shape, a colour or a word across it.
- **One timeline, several formats.** Lay scenes out with a `layout(w, h)` function rather than fixed pixels when 9:16, 1:1 and 16:9 are all needed; reframe type and UI per format instead of cropping.
