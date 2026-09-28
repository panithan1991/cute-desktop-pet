# Artwork sources

Created with the built-in ImageGen tool using the supplied animal illustrations as identity references. Each pet uses 40 painted keyframes plus 45 motion-compensated inbetweens, producing exactly 85 distinct animation frames. These are animation frames, not 85 unrelated poses.

## Prompt set

All prompts preserve the reference animal, soft painted fur/feathers, colors, markings, proportions and anatomy. They request transparent backgrounds, complete bodies, wide empty gutters, no text, borders, shadows or colored marks.

- `booboo-keyframes.png`: white Holland lop rabbit, drooping peach-pink ears, dark eyes, pink nose. 5x5 keyframes: idle/head tilt/blink; right-facing walk; side-to-belly-up roll; lying sleep/breathing; crouch/takeoff/apex/descent/landing.
- `moo-krata-keyframes.png`: Bernese puppy, black fur, white forehead/muzzle/chest, tan eyebrows/paws, floppy ears, white-tipped tail. Same five 5-frame sequences.
- `bibi-keyframes.png`: baby bald eagle, cream-white head, dark brown layered feathers, brown eyes, golden beak/feet, black claws and white tail. Same layout, with a right-facing wingbeat replacing the walk and a takeoff/landing sequence. Every feather and wingtip must fit inside the image.
- `kitten-keyframes.png`: supplied fluffy gray-brown tabby kitten, white muzzle/chest/paws, pink nose/ears and large brown eyes. Same five 5-frame sequences, preserving fur stripes.
- `*-roll.png`: 5x4 sheets, 20 consecutive gradual floor-tumble drawings for the same animal. Frames 1-5 settle onto the right side; 6-10 roll gently onto the back; 11-15 remain belly-up with relaxed paw/ear/tail wiggles; 16-20 roll onto the opposite side and settle low again. Small changes between adjacent frames, happy healthy playful expressions, full bodies with wide transparent gutters. Bibi has exactly two folded wings, two feet and one tail; mammals have four paws, two ears and one tail.

## Regenerate atlases

Install `Pillow`, `numpy` and `opencv-python`, then run `python scripts/build_pet_atlases.py` from the repository root. The script extracts whole connected subjects rather than cropping guessed grid cells, aligns each sequence at a common scale, and creates mirrored smooth-alpha Mac and binary-alpha Windows atlases. Rolling uses all 20 painted drawings directly; other clips use bounded texture warps without crossfading faces. No image-generation or image-processing library is needed by the app at runtime.
