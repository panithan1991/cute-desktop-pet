# Pet behavior

Artwork clips describe movement; named activities describe intent. A long nap
plays its entry once, holds closed-eye breathing poses, and plays its waking
frames once. Picking random frames would break this sequence.

`app/behavior_selection.py` contains the shared `Activity` specification and
`BehaviorMemory`. Each activity has a readable label, duration range, cooldown,
entry/exit durations, and an optional shared cooldown group. The selector
remembers four recent non-idle actions, so inserting a neutral rest does not
erase the previous action. Cooldowns start when an action finishes. Recently
used choices receive less weight; each pet has its own preferences.

`app/pet_behavior.py` defines the ground/bird activities and their allowed next
activities. Sleep, rolling, and belly-up play lead to `lounge`, because their
final drawings are lying down. A curious glance returns to a neutral rest.
Walking eases its speed at the start and end, and animation timing follows
movement speed. Occasional runs are short accelerations within a long walk.

`app/dragon_animation.py` defines dragon gestures separately. Yawning leads to
sleep; sleep leads through the dedicated waking clip before idle. Fire, smoke,
wing stretches, tail movements, and hovering have different cooldowns. A
neutral breathing interval bridges these gestures without immediately
repeating the same action.

Activity clocks advance only while active. Flying pets keep cooldown time
moving during flight without prematurely finishing their ground activity.
The flight controller completes takeoff, cruising, and landing before choosing
another activity. Pausing or dragging freezes both movement and behavior.

To add an activity, declare its specification, provide a compatible clip path,
and add it to allowed next choices. Use mandatory transitions where the body
posture must match; use weighted choices where several next actions fit.
`app/behavior_art.py` supplies 25-frame waking/stretching and turning clips.
Its posture transition queue connects lying, upright, and travel states;
movement and activity time wait until these connecting drawings finish.
Joining endpoints match the original poses exactly. Add painted connecting
poses when introducing a new posture.

Each pet has three signature activities with separate cooldowns. Rabbit:
face washing, sniffing, hind-leg stretch. Puppy: tail wag, ground sniff before
walking, play bow. Kitten: paw grooming, kneading, watching its tail. Eagle:
preening, alternating wing stretches, one-leg rest. Dragon: tail hug, smoky
hiccup, wing blanket. Sleeping dragon gestures lead directly into closed-eye
sleep without replaying the entry.

Dragon smoke and fire have 43 frames each, and smoky hiccups have 25.
During artwork baking, independent effects use premultiplied-alpha
interpolation. Clean body poses are never segmented by brightness or erased;
effects only alpha-composite over them. A saved clean-body atlas lets tests
verify no body alpha is lost. Smoke expands, drifts upward and dissipates;
fire stays anchored at the mouth and grows/shrinks.

Warning displays and roars have 30 frames each and separate cooldowns.
`storm_hover` has 140 frames for lift, four slow wingbeats and settling, with
twelve irregular lightning bursts lasting about 0.1–0.2 seconds each. Branches
stay coherent during a strike, change between strikes, and turn off fully
between them. `app/dragon_lightning.py` separates these exposures from the
slow body movement. It does not trigger the
travel controller, so the desktop position stays fixed. Pausing freezes the
body and baked effects together. These activities return to a neutral pose.

Dragon runtime art is split into pages of 40 frames. Tk decodes a page only
when a pose needs it, with at most two decoded pages and 80 cached frames.
This avoids decoding two very tall PNGs at startup and bounds memory during
long sessions. Packaging includes only the target platform's pages. The full
atlases remain artwork/test references; page tests compare every pixel.

Validation: `python -m unittest discover -s tests -q` checks cooldowns, retained
history, transition routes, gentle movement, pause behavior, all sprite bounds,
both facings, and the dragon's smoke/flame padding.


Dragon powers use a separate transparent native window: 32 large flame drawings, 16 rasterized lateral lightning trees stable during each exposure, and a volumetric drifting cloud vortex on the flapping wing side. All motion uses the pauseable activity clock. Flame lasts 12–16 seconds including ignition and fade; smoke/fire cooldowns are 8/10 seconds after completion. Flight preserves the higher altitude range (22–42% of the display) and 25–45 second cruise. One-wing gust adds 60 body frames and a 7–9 second activity. Interrupted upright gestures finish their remaining painted exit before starting the requested pose. Body clip endpoints share the canonical neutral pose.


DragonFlightMotion samples one Bernoulli decision (p=.5) per successful launch. A chosen cruise includes one 2–3-revolution sequence, with 1.2-second painted tuck/exit and a 3-second 90-frame revolution. The hover phase resumes at its saved phase; paused flight freezes the rotation and discharges. Two bolt trees are individually anchored to the rotated horns. Ground fury remains stationary, uses two or three lightning trees and downstroke-timed drifting vortices; its flame aura is behind the body window. Belly-up smoke emits at the three painted exhale phases, stores each mouth origin at birth, and lets rings grow, rise and dissolve independently. Windows rings use alpha dithering instead of blending a magenta matte. All new ground clip endpoints are the exact canonical seated pose.

Dragon ground travel uses separate `ground_walk` and `run` activities. The legacy `walk` identifier remains the flight launcher for compatibility. Ground walks last 18–30 seconds, rare runs 5–8 seconds with an 85-second cooldown. Actual horizontal displacement advances 44-pixel walk and 72-pixel running strides; the speed menu changes travel and paw cadence together. Ground preparation and the remaining gait cycle join sitting without moving during transitions. Edge turns wait until the painted exit completes. Pausing and dragging freeze motion.

`cloud_flame` lasts 18–22 seconds, with a 35-second cooldown. The intact flame-breath body clip plays over the first 52 percent of the activity, then plays the 40-frame illuminated reaction while the gas ignites and burns. VFX phases are ring emission (.07–.245), cloud growth (.20–.44), accumulation (.44–.56), ignition (.56–.68), pure gas flame (.68–.85) and fade (.85–.97). Once fully ignited, no grey cloud texture remains. The emission origin is captured once; body recoil cannot pull the cloud backwards. Deterministic embers rise briefly, fall under gravity and fade, using the pauseable activity clock. Scaling preserves complete cloud bounds and avoids covering the mouth at screen edges.

Belly-up smoking lasts 36–42 seconds with six consecutive exhalations. Each detached sky ring expands, rises and dissolves over six seconds, so consecutive exhalations can overlap naturally.

Each of six emitted vortex rings captures its own mouth position at birth, travels monotonically toward a fixed cloud target over 2.6 seconds, rises with buoyancy, grows, then dissolves underneath the accumulating cloud. The target is 2.5 times the canonical visible body width (98 pixels), about 245 pixels ahead of the mouth, and 65 pixels higher. A wider directional overlay leaves enough room for this separation; near desktop edges the complete effect is scaled to fit. Reaction starts at .52 of the activity: eyes open, head and wings lift, green light brightens from the flame-facing side, then fades back to the exact idle pose by .97.

Tk used to synchronously decode the full 48-frame cloud atlas, blocking the first draw for about 20.7 seconds on the local Windows machine. Individual small effect files, an LRU cache of 96 images, direct exhale/reaction body files, and simpler Windows cloud alpha masks remove the large decode and thousands of tiny transparency regions. A 100-frame local measurement after these changes had a 6.6ms median, 13.8ms p95 and 30.6ms maximum, including idle drawing updates. The tick scheduler subtracts drawing time from the 33ms frame interval. Memory stays bounded; Mac keeps smooth per-pixel alpha and no runtime image-processing dependency is added.

## Dragon personality and flight gestures

Eleven named clips add 440 painted/tweened frames (1,630 total). Seated clips begin and end in the canonical idle pose; airborne clips share the canonical hover endpoint. Two additional 40-frame clips join hover to a side or overhead grip after physical work-area contact. Mouth-open clips reach emission by 25% of their clock, breathe subtly until 80%, then close. Cooldowns and recent-history penalties apply to every new activity. A completed charge chooses horn lightning; completed elemental moves have a 35% chance of a proud/happy reaction.

Air gestures are explicit flight modes, selectable from the ground or during cruise. Hover eases horizontal speed to zero; braking smoothly crosses zero for a small retreat. Diving adds a bounded sin^4 vertical displacement with zero endpoint slope. Perching starts only after diagonal flight contacts a side or top edge; wings remain animated until that contact. Normal flight retains its existing 50% thunder-roll decision; these dedicated maneuvers do not overlap a roll. Pausing/dragging freezes all clocks.

Signature VFX use small pre-baked individual PNGs and bounded canvas primitives. Aurora uses advected layered wisps; ember bubbles drift from independent birth positions and fade away. Static charge uses detailed painted corona at the horn roots and small glints across the existing scales. Thunder roar combines expanding pressure waves and the existing rapidly branching lightning art. Windows uses coherent binary masks; Mac preserves alpha. No image processing or image generation happens at runtime. Rebuild with `python scripts/build_dragon_personality.py`, `python scripts/build_dragon_personality_effects.py`, `python scripts/bake_effect_frames.py`, and the two preview builders.

## Pet Studio

The normal native Toplevel window is independent of the transparent pet overlay. Double-click or the short context menu opens it; closing Studio hides only the controls. Three tabs expose portrait selection, grouped dragon gestures and motion settings. Existing variables/actions remain the single source of truth. Status and enabled actions refresh twice per second, without redrawing portraits. Ground gestures are disabled while airborne; flight maneuvers can be requested during cruise. Keyboard focus, native title bar and Escape-to-hide remain available. Five small portrait PNGs ship on both platforms; no runtime Pillow or new dependency is required. Opening Studio also clears a drag started by the first click, so a double-click cannot leave the pet frozen.

Thunder Roar emits three or four independent painted lightning trees rooted at the mouth. Short irregular flashes alternate with dark gaps, using the same exposure schedule as horn lightning. Complete channels are scaled near screen edges. Ember bubbles use 36 lifecycle frames: tiny emission, gradual translucent membrane expansion, irregular turbulent rupture, and dissolved remnants. Each bubble keeps its birth position and a slow rising trajectory independent of dragon recoil.

Edge perching uses two painted 40-frame clips with planted paws. One action is selected from fire, jade gas or mouth lightning, then the dragon releases its grip and lands. Dragging detaches the grip, and pause freezes both clocks.

Belly-up smoke now lasts 36–42 seconds and emits six distinct rings. The painted breath cycles are reused six times between lie-down and sit-up clips, with each ring born during exhalation and lasting six seconds. No extra body assets or runtime image processing are needed.

Edge contact now triggers a 1.2-second painted grip transition after normal diagonal flight. No random edge target or position interpolation runs during cruise. Upward velocity favors reaching the top. One randomly selected fire/gas/mouth-lightning action runs before release and landing. Mouth lightning renders 3–4 independent painted trees rooted at the mouth, with the horn-lightning flash/dark-gap cadence.

Flight transitions add 66 standalone body frames: six bridge frames for each of ten hover wingbeat phases plus a six-frame hover-to-landing bridge. They are loaded directly through the existing bounded sprite cache. Aurora breath now uses 64 pre-rendered flow frames from one painted plume, a stationary nozzle at (8,80), downstream-only periodic deformation and identical first/last frames. No source switching or image warping occurs at runtime.

Static charge uses tracked horn tips and two directional pre-baked coronas (rear 32 degrees, front 18 degrees), mirrored with the body. Each corona is rooted at the horn tip, pointing away from the head rather than into the forehead.

Transition audit: all normal landings now settle the current wingbeat, bridge into landing, then use six touchdown-to-idle frames before resuming a resting routine. Interrupted waking/lying/travel preparation returns continuously from the displayed frame to neutral before entering the next posture. Idle selection increases ordinary-flight weight from 18 to 24 and edge-flight weight from 8 to 10.

Running uses eight repaired painted keys from `assets/source/dragon-run-wings-fixed.png`, with attached wings retained through the airborne stride. The 40 interpolated frames retain the original ground-contact endpoints. `python scripts/fix_dragon_run_wings.py` rebuilds only this clip and its mirrored platform atlases; the full behavior builder uses the same repaired source.

Powered flight: `scripts/build_dragon_powered_flight.py` bakes 876 additional body frames: 60 looping wingbeats, 24 launch frames, 360 exact wing-phase bridges, 180 frames each for dive/recover and air brake, and 24 each for roll entry, roll exit and landing fold. The wing clock drives lift pulses against gravity; climbing and descending use capped velocities instead of interpolating from floor to ceiling. Preparation stays grounded, and landing slows close to the floor before folding wings.

Each successful launch makes one 50% maneuver decision, choosing equally between glide, dive/recover, air brake, hover and a two/three-turn lightning roll. Maneuvers enter from the current wingbeat through an exact bridge and resume normal flight without resetting position or the cruise clock. Every top/side contact independently chooses 50% grip or 50% reflection, with a cooldown against repeated collision draws. Left grips face/reach left; right grips face/reach right. One perched power still runs before departure and descent.

Powered-flight sources use exactly one tail per subject. Only the eight wing keys are kept in `dragon-powered-flight.png`; the corrected four grip keys come from the bottom row of `dragon-wall-grip-single-tail.png`. Runtime loads bounded small-frame caches without image warping. After rebuilding the main behavior atlas, run `python scripts/build_dragon_powered_flight.py` followed by `python scripts/build_dragon_aurora_flame.py`. Aurora uses 32 jade flame growth/hold/decay frames, spark particles, the existing fire nozzle geometry, and tracked lip positions rather than a fixed generic head coordinate.

Running dash and ground-skimming glide (`run_glide`): `scripts/build_dragon_run_glide.py` extracts, cleans, and bakes 40 high-resolution frames for macOS PNG and Windows magenta-keyed PPM. The sequence coordinates ground sprint acceleration (1.7×), an energetic leap into an aerodynamic low glide (2.3× speed with a 16px sinusoidal elevation arc), and a gentle four-paw touchdown. A dedicated Pet Studio button and bilingual context menu item let users trigger the behavior on demand.

Flight and ground polish: Ground idle transitions now feature a 20% probabilistic check to turn and face the opposite direction with smooth, realistic turn frames. Aerial maneuvers support queuing multiple actions, including Roll Lightning with horn discharges. Takeoff lift utilizes ease-in-out curve dynamics (`p²(3-2p)`), and resting postures (yawn and wing-stretch) now include natural satisfying peak holds before sighing and relaxing.

