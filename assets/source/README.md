# Artwork sources

Created with the built-in ImageGen tool using the supplied animal illustrations as identity references. Four pets have 195 frames. The dragon has 170 base frames plus 375 gesture/transition frames (485 total). These are animation frames, not unrelated poses.

## Prompt set

All prompts preserve the reference animal, soft painted fur/feathers, colors, markings, proportions and anatomy. They request transparent backgrounds, complete bodies, wide empty gutters, no text, borders, shadows or colored marks.

- `booboo-keyframes.png`: white Holland lop rabbit, drooping peach-pink ears, dark eyes, pink nose. 5x5 keyframes: idle/head tilt/blink; right-facing walk; side-to-belly-up roll; lying sleep/breathing; crouch/takeoff/apex/descent/landing.
- `moo-krata-keyframes.png`: Bernese puppy, black fur, white forehead/muzzle/chest, tan eyebrows/paws, floppy ears, white-tipped tail. Same five 5-frame sequences.
- `bibi-keyframes.png`: baby bald eagle, cream-white head, dark brown layered feathers, brown eyes, golden beak/feet, black claws and white tail. Same layout, with a right-facing wingbeat replacing the walk and a takeoff/landing sequence. Every feather and wingtip must fit inside the image.
- `kitten-keyframes.png`: supplied fluffy gray-brown tabby kitten, white muzzle/chest/paws, pink nose/ears and large brown eyes. Same five 5-frame sequences, preserving fur stripes.
- `*-roll.png`: 5x4 sheets, 20 consecutive gradual floor-tumble drawings for the same animal. Frames 1-5 settle onto the right side; 6-10 roll gently onto the back; 11-15 remain belly-up with relaxed paw/ear/tail wiggles; 16-20 roll onto the opposite side and settle low again. Small changes between adjacent frames, happy healthy playful expressions, full bodies with wide transparent gutters. Bibi has exactly two folded wings, two feet and one tail; mammals have four paws, two ears and one tail.

## Regenerate atlases

Install `Pillow`, `numpy` and `opencv-python`, then run `python scripts/build_pet_atlases.py` from the repository root. The script extracts whole connected subjects rather than cropping guessed grid cells, aligns each sequence at a common scale, and creates mirrored smooth-alpha Mac and binary-alpha Windows atlases. Rolling uses all 20 painted drawings directly; other clips use bounded texture warps without crossfading faces. No image-generation or image-processing library is needed by the app at runtime.

Then run, in order:

```sh
python scripts/build_dragon_atlas.py
python scripts/build_behavior_atlases.py
python scripts/build_dragon_effects.py
```

`*-behaviors.png` contains five rows of five painted keyframes: waking/stretching, three species-specific gestures, and preparing to travel. The builder appends 110 frames and preserves canonical joining endpoints. `behavior-prompts.json` records the original prompts; `anatomy-repair-prompts.json` records corrections to lifted paws and folded wings. Raised forepaws must replace their grounded counterparts; mammals have four legs and two ears, birds two feet and two wings, dragons four legs and two wings.

`dragon-vfx.png` contains 18 independent effects without a dragon body. `dragon-actions.png` contains 20 clean exhale, threat, roar and wingbeat keyframes. `dragon-v09-prompts.json` records their generation and padding prompts. The effects builder runs last; it composites smoke over intact body poses, exports mouth/horn anchors for the independent large power overlay, and saves `dragon-effect-bodies.png` as a pixel-loss regression reference. Older combined-effect sources document the earlier artwork only. Review final frames visually for anatomy; bounds tests cannot count limbs.

Dragon atlas saves also produce `assets/runtime/dragon-{windows,macos}/` pages. Ship those platform-specific pages in apps; the full dragon atlas is only a reference. Each page has at most 40 frames to keep Tk startup fast.

`dragon-wing-gust.png` contains five one-wing seated keyframes, expanded into 60 poses with neutral endpoints. `dragon-wing-gust-prompt.txt` records the built-in generation prompt. `dragon-fantasy-fire.png` supplies 16 large flame textures, baked into 32 ignition/flicker/fade drawings per platform and direction; its prompt is recorded alongside it. `python scripts/build_dragon_power_preview.py` refreshes the static README examples.

`dragon-vortex.png` contains eight looping volumetric smoke keyframes from the built-in image tool. Its prompt is in `dragon-vortex-prompt.txt`. Run `python scripts/build_dragon_weather.py` to bake 32 vortex frames and 16 antialiased lightning trees per platform. Lightning trunks spread outwards from the horns, recursively fork into thinner twigs, and use a blue bloom around the white plasma core. Weather images load lazily, adapt to desktop edges, and use the activity clock.
