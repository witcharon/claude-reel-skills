# reel-taste

**Idea to script, with taste.** The first half of a pair: reel-taste writes the film and [**motion-studio**](../motion-studio) builds it.

reel-taste is a concept and script director for short product videos: AI-generated footage with a motion layer on top, or pure motion graphics made in code. It works from a small set of rules:
- **The product's verb is the plot.** Find the one thing the product makes possible and make it the turning point, not the logo on the last frame.
- **Diverge on purpose.** Spread ideas across genres and devices, then cut anything a competitor could run by swapping the logo.
- **Hold ideas to a taste bar.** Every idea must read in one second with the sound off, use specific details rather than hype, have one signature move, look chosen rather than generic (and like real footage, not CG, when there is footage), and make only honest claims.
- **Never the same recipe twice in a row.** Each new video differs from the last in at least three of its five ingredients.

## What you get

For the idea you pick:
1. **A look direction**: the reference and the grammar to take from it, or the look reasoned from the brief. No house style.
2. **One video-model prompt** (films with footage; Seedance or similar) that renders consistently: consistency anchors, timestamped physical actions, cuts where the edit can hide them, an ambient-only audio line and an AVOID line.
3. **Motion notes**: a `time | picture | on screen | sound` table, the signature move, how the product's verb lands, where the CTA goes, and the platform safe zones.
4. **What to check in the generated take** before anyone edits it.
5. **A caption** with the CTA.

## Where it hands over

For films with footage, generate the take from the prompt; we use Seedance 2.5 on [Loomshot](https://loomshot.ai). Then give the package (and the take, if there is one) to **[motion-studio](../motion-studio)**, which turns the look direction into its `style_guide.md` and the notes into its shot list: it builds the film, scores the sound and critiques its own frames.

## Files

- `SKILL.md`: the process and the taste bar.
- `references/devices.md`: the spice rack (genres, hooks, structures, motion, sound and ending devices, with when each turns into a cliché).
- `references/seedance-prompting.md`: how to write prompts a video model renders consistently.
- `references/motion-handoff.md`: what the motion layer can build, safe zones, and the rules that hold for any look.
- `references/case-studies.md`: the Lidlezz reels, what worked, what flopped and why.
- `evals/evals.json`: test prompts used with Anthropic's skill-creator.

On-screen copy is written in the audience's language, and generator prompts in English.
