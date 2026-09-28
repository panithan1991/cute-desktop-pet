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


Dragon powers use a separate transparent native window: 32 large flame drawings, randomly branched lightning stable during each exposure, and a procedural drifting vortex on the flapping wing side. All motion uses the pauseable activity clock. Flame lasts 12–16 seconds including ignition and fade; smoke/fire cooldowns are 8/10 seconds after completion. Flight preserves the higher altitude range (22–42% of the display) and 25–45 second cruise. One-wing gust adds 60 body frames and a 7–9 second activity. Interrupted upright gestures finish their remaining painted exit before starting the requested pose. Body clip endpoints share the canonical neutral pose.
