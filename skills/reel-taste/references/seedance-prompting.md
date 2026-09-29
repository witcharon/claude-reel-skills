# Writing prompts the generator can render

Lessons from Seedance 2.x takes. The same principles apply to other text-to-video models.

## Shape of a prompt

```
A <N>-second <single continuous shot | sequence of K shots joined by hard cuts that happen only inside <darkness/flash>>,
<POV/camera type>, photoreal real <action-camera | webcam | phone> footage, vertical 9:16, 4K 60fps look, natural motion blur, <light>. <No cuts. | No cuts other than those described.>

THE <PERSON> (the same in every shot; <seen only as hands/body, face never visible | description>): <3–5 distinctive, stable details>.
THE <KEY OBJECT> (the same in every shot): <material, colour, one distinctive detail>.
THE WORLD: <place, light, weather, background that stays simple where type will sit>.
THE LAPTOP / SCREEN: <unbranded or allowed brand>; its screen shows a dark terminal window with a few lines of small white and green monospace text and an orange asterisk icon at the top left.

SHOT 1 (0–4s), <where>: <physical actions with times>. <The screen faces the camera and nothing passes in front of it.>
<4–5s: total darkness.>
SHOT 2 (...)
...
<last 2 s>: Calm. <final state>. Hold this calm view to the end.

CAMERA: <mount>, <steady inside each shot>, no zoom, no slow motion.
AUDIO: ambient only: <diegetic sounds per shot>. No music, no voice.
AVOID: <extra hands or fingers, text, logos/brands you must avoid, a visible face (if POV), cartoon or CGI look, the outfit changing between shots, more than K shots, cuts outside the darkness, anything unsafe>.
```

## What makes takes consistent

- **One prompt, not several generations.** Keyframe or reference-image chains and separately generated parts came back inconsistent. A single multi-shot prompt (up to about 30 s) held the character and objects together. If the model cuts on its own anyway, the edit can hide it in darkness or a flash.
- **Consistency anchors.** Give the character and key objects two or three unmistakable details: tortoiseshell glasses, a bright orange bag lining, an orange-and-teal jumpsuit. Repeat the exact same words in every shot block.
- **Physical, timestamped actions.** Write "at 2.5s the right hand presses the lid down", not "he decides to leave". The model animates verbs, not intentions.
- **Cuts where the edit can hide them.** Put cuts in darkness, a flash, a whip pan or a zipper, and say so explicitly.
- **A calm ending.** The last 1.5–2 s held still gives the motion layer room for the end card.

## Screens and UI

- Ask for a **dark terminal window with small text** facing the camera and **unobstructed for the first ~2 s**. That gives a trackable plane; the real UI gets replaced on top at a realistic size.
- Never ask the model to render readable product text or logos. It will garble them; the motion layer adds them.
- Brand marks: say "unbranded … with no logo" unless the brand allows its mark. For Lidlezz the Apple logo on the MacBook is fine.

## Things the generator is bad at

- Readable text of any kind.
- Consistent faces across many shots, and crowds of distinct faces.
- Complex hand choreography: typing plus a phone plus a cup. Keep one action per beat.
- Precise counts ("exactly five lights one second apart") are only mostly respected; plan to check them.
- Camera moves that are physically ambiguous. Say where the camera is mounted: chest, helmet, webcam, inside a bag.

## Safety and taste in the prompt

- Animals and people near danger: state their calm or safe behaviour ("calm, never aggressive, never touches the person").
- No real brands, liveries, teams, logos or public figures.
- Keep faces unseen in POV concepts; it also avoids uncanny faces.

## Specs to request

- 1080p (720p softens close-ups), 24 fps, 9:16.
- Duration: 15–30 s of footage. The motion layer adds 3–6 s of end card.
