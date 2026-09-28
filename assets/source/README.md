# Artwork sources

Created with the built-in ImageGen tool using the supplied animal illustrations as identity references. Four pets have 195 frames. The dragon has 170 base frames plus 795 gesture/transition frames (485 total). These are animation frames, not unrelated poses.

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

`dragon-belly-smoke.png` and `dragon-fury.png` supply the new resting-on-back and two-legged frontal fury keyframes. Their built-in image generation prompts are saved in `dragon-stunts-prompts.json`. `build_behavior_atlases.py` uses `build_dragon_stunts.py` to add 120 belly-up, 120 flight tuck/spin/exit, and 180 fury frames. Spin frames rotate an unchanged compact original body with rotated horn anchors; no new limbs are drawn. Run `python scripts/build_dragon_stunt_effects.py` after the other builders for sky rings, fire aura and individually anchored lightning trees; `python scripts/build_dragon_stunt_preview.py` creates static README examples. Flame nozzle coordinates are measured from the actual effect image and body lip pixels, for accurate left/right mouth alignment.

`dragon-ground-gaits.png` adds fifteen painted sitting-to-standing, walking and running keyframes from the built-in image tool; its prompt is in `dragon-ground-gaits-prompt.txt`. The behavior builder uses `build_dragon_gaits.py` for 25 ground preparation, 40 walk and 40 run frames, all with exact shared contact endpoints. The dragon now totals 1,110 body frames. The builder also refreshes the static README gait examples.

`dragon-cloud-flame-v2.png` provides padded jade-grey gas accumulation and ignition keyframes. `dragon-cloud-combustion.png` supplies the fully burning turquoise-green flames with no residual grey gas. Prompts are recorded in the matching prompt text files. Run `python scripts/build_dragon_cloud.py` to bake 48 detached effect frames per platform and the static README example. Fully consumed gas disappears, flame wisps fade to empty alpha, and falling embers use the frozen activity clock. Windows cloud sprites use simple transparent contours and a window fade to avoid slow mask construction; small smoke rings retain dithering. Existing intact exhale body frames are reused without repainting the face.

`dragon-ignition-reaction.png` supplies ten painted keyframes, expanded to 40 poses for excited eyes, a gentle wing lift and directional green specular reflections. Its prompt is saved in `dragon-ignition-reaction-prompt.txt`. `dragon-jade-rings.png` supplies eight hollow vortex keyframes; run `python scripts/build_dragon_jade_rings.py` for 24 growing, drifting, dissolving ring frames. Its prompt is in `dragon-jade-rings-prompt.txt`. All body clip endpoints share the exact canonical idle drawing.

Run `python scripts/bake_effect_frames.py` after rebuilding art to export small individual effects and exhale/reaction body frames. The updated builders also refresh their individual files automatically. Effects preserve full RGB/alpha on both platforms. Windows body frames use lossless RGB PPM with the native magenta color key; Mac body frames retain smooth-alpha PNG. `python scripts/build_dragon_cloud_scene.py` refreshes the static README scene.

The exact prompt set and selected source image paths are in `dragon-cloud-refinement-prompts.json` (built-in image generation; no API fallback).

### Dragon personality expansion

`dragon-personality-keyframes.png` contains 24 painted keys (six rows of four); `dragon-flight-keyframes.png` contains 16 flight keys. They preserve the existing black dragon identity, two wings and four paws. `dragon-personality-prompts.json` records both complete prompts and the built-in generation mode. `scripts/build_dragon_personality.py` appends eleven 40-frame clips while preserving the first 1,110 frames, then rebuilds padded mirrored platform atlases. `scripts/build_dragon_personality_effects.py` procedurally bakes ember bubbles, aurora wisps and pressure waves. `scripts/bake_effect_frames.py` exports small cached body/effect files for the app. Preview images stay static.

`dragon-signature-effects.png` adds realistic painted fire orbs, aurora wisps and electrical plasma artwork. The effect builder interpolates premultiplied alpha, loops the aurora/halo at identical endpoints, and fades individual bubbles. `scripts/build_ui_icons.py` crops and normalizes existing portraits into the small `assets/ui` directory bundled on both platforms.

`dragon-roar-lightning-cone.png` contains four branching electrical cones; `scripts/build_dragon_roar_cone.py` produces 16 mouth-aligned variations per facing/platform. The complete prompt is recorded alongside the other generation prompts. Ember bubble frames are 96×96 with a 36-frame growth/rupture/dissolution lifecycle.

`dragon-edge-perch.png` contains eight complete wall and overhead grip keyframes. The personality builder interpolates two 40-frame clips and exports them as individual runtime body frames. Prompts are stored with the source artwork.
