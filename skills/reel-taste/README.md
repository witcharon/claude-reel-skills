# reel-taste

**Idea to script, with taste.** The first half of a pair: reel-taste writes the film and [**motion-studio**](../motion-studio) builds it.

reel-taste is a concept and script director for short product reels. AI-generated footage carries the action and a motion layer carries the product. It works from a small set of rules:
- **The product's verb is the plot.** Find the one thing the product makes possible and make it the turning point, not the logo on the last frame.
- **Diverge on purpose.** Spread ideas across genres and devices, then cut anything a competitor could run by swapping the logo.
- **Hold ideas to a taste bar.** Every idea must read in one second with the sound off, use specific details rather than hype, have one signature move, look like real footage rather than CG, and make only honest claims.
- **Never the same recipe twice in a row.** Each new video differs from the last in at least three of its five ingredients.

## What you get

For the idea you pick:
1. **One video-model prompt** (Seedance or similar) that renders consistently: consistency anchors, timestamped physical actions, cuts where the edit can hide them, an ambient-only audio line and an AVOID line.
2. **Motion notes**: a `time | picture | on screen | sound` table, the signature move, how the product's verb lands, where the CTA goes, and the platform safe zones.
3. **What to check in the generated take** before anyone edits it.
4. **A caption** with the CTA.

## Where it hands over

Generate the take from the prompt; we use Seedance 2.5 on [Loomshot](https://loomshot.ai). Then give the take and the motion notes to **[motion-studio](../motion-studio)**, which treats the notes as its brief: it tracks the real UI onto screens, sets the type, scores the sound and critiques its own frames.

## Files

- `SKILL.md`: the process and the taste bar.
- `references/devices.md`: the spice rack (genres, hooks, structures, motion, sound and ending devices, with when each turns into a cliché).
- `references/seedance-prompting.md`: how to write prompts a video model renders consistently.
- `references/motion-handoff.md`: what the motion layer can build, safe zones, type and sound defaults.
- `references/case-studies.md`: the Lidlezz reels, what worked, what flopped and why.
- `evals/evals.json`: test prompts used with Anthropic's skill-creator.

On-screen copy is written in the audience's language, and generator prompts in English.
