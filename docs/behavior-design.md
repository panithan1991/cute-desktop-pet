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
Existing sprites limit available transitions: this system does not invent
missing turn or stand-up drawings. Add painted connecting poses when such a
transition is needed rather than mixing unrelated images.

Validation: `python -m unittest discover -s tests -q` checks cooldowns, retained
history, transition routes, gentle movement, pause behavior, all sprite bounds,
both facings, and the dragon's smoke/flame padding.
