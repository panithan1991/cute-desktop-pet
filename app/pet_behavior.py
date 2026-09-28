"""Unhurried, varied activities with a clock that freezes during pause/drag."""

import random

from app.behavior_selection import Activity, BehaviorMemory
from app.behavior_art import PostureTransition, SIGNATURES, gesture_pose

SIGNATURE_ACTIVITIES = {
    "wash_face": Activity("Wash face", (5, 7), 120, enter=1, exit=1),
    "sniff": Activity("Twitch nose and sniff", (4, 6), 75, enter=1, exit=1),
    "hind_stretch": Activity("Stretch hind legs", (5, 7), 150, enter=1, exit=1),
    "wag_tail": Activity("Gentle tail wag", (5, 8), 75, enter=1, exit=1),
    "sniff_ground": Activity("Sniff before walking", (5, 7), 90, enter=1, exit=1),
    "play_bow": Activity("Play bow", (5, 7), 150, enter=1, exit=1),
    "groom": Activity("Lick paw and wash face", (6, 8), 120, enter=1, exit=1),
    "knead": Activity("Knead paws", (5, 7), 150, enter=1, exit=1),
    "watch_tail": Activity("Watch tail tip", (5, 7), 120, enter=1, exit=1),
    "preen": Activity("Preen chest feathers", (6, 8), 120, enter=1, exit=1),
    "wing_stretch": Activity("Stretch each wing", (5, 7), 150, enter=1, exit=1),
    "one_leg": Activity("Rest on one leg", (7, 10), 150, enter=1, exit=1),
}

ACTIVITIES = {
    "idle": Activity("Observe", (15, 30)),
    "walk": Activity("Stroll", (20, 45), 15, enter=0.8, exit=0.8),
    "lounge": Activity("Rest lying down", (25, 50), enter=2, exit=2),
    "sleep": Activity("Long nap", (40, 90), 30, enter=3, exit=3),
    "roll": Activity("Playful roll", (6, 9), 90, enter=2, exit=2, group="play"),
    "belly_up": Activity("Relax belly up", (12, 20), 90, enter=3, exit=3, group="play"),
    "curious": Activity("Look around", (16, 22), 180, enter=8, exit=8),
}

NEXT_ACTIVITIES = {
    "walk": {"idle": 55, "lounge": 35, "sleep": 5, "roll": 3, "belly_up": 2, "curious": 1},
    "idle": {"walk": 45, "lounge": 30, "sleep": 10, "roll": 5, "belly_up": 7, "curious": 3},
    "lounge": {"sleep": 45, "idle": 25, "walk": 20, "belly_up": 5, "curious": 5},
}

PREFERENCES = {
    "bunny": {"lounge": 1.5, "sleep": 1.4, "roll": 0.7},
    "mookrata": {"walk": 1.3, "belly_up": 1.3, "roll": 1.2},
    "kitten": {"lounge": 1.4, "belly_up": 1.3},
    "bibi": {"walk": 1.3, "roll": 0.5, "belly_up": 0.5},
}


class PetBehavior:
    def __init__(self, character: str, rng: random.Random | None = None):
        self.character = character
        self.rng = rng if rng is not None else random.Random()
        self.previous = None
        self.state = "idle"
        self.elapsed = 0.0
        self.clock = 0.0
        self.activities = {**ACTIVITIES,
                           **{name: SIGNATURE_ACTIVITIES[name] for name in SIGNATURES[character]}}
        self.memory = BehaviorMemory(self.rng, self.activities)
        self.transition = PostureTransition(character)
        self.next_run = self.rng.uniform(90, 180)
        self._configure()

    def _configure(self):
        limits = self.activities[self.state].duration
        if self.character == "bunny":
            limits = (18, 35) if self.state == "walk" else limits
        elif self.character == "bibi":
            limits = (25, 45) if self.state == "walk" else limits
        self.duration = self.rng.uniform(*limits)
        # Most rests are neutral. A head tilt happens once in a rare curious rest.
        self.variant = 3 if self.state == "curious" else 1
        self.base_pace = self.rng.uniform(0.65, 0.9)
        self.run_start = None
        self.run_duration = self.rng.uniform(2.5, 4)
        if (self.state == "walk" and self.character != "bibi"
                and self.clock >= self.next_run and self.rng.random() < 0.25):
            self.run_start = self.rng.uniform(8, self.duration - 5)
            self.next_run = self.clock + self.rng.uniform(120, 240)
        self.hop_at = (self.rng.uniform(10, self.duration - 2)
                       if self.state == "walk" and self.character != "bibi"
                       and self.rng.random() < 0.12 else None)

    def force(self, state: str):
        if state not in self.activities:
            raise ValueError(f"Unknown pet behavior: {state}")
        self.memory.record(self.state, self.clock)
        self.transition.connect(self.state, state)
        self.previous, self.state = self.state, state
        self.elapsed = 0.0
        self._configure()

    def finish(self):
        # Sleep and play end lying down: keep that posture in the next rest.
        if self.state in {"sleep", "roll", "belly_up"}:
            self.force("lounge")
        elif self.state == "curious":
            self.force("idle")
        elif self.state == "sniff_ground":
            self.force("walk")
        elif self.state in SIGNATURES[self.character]:
            self.force("idle")
        else:
            options = dict(NEXT_ACTIVITIES[self.state])
            if self.state in {"idle", "lounge"}:
                options.update(dict.fromkeys(SIGNATURES[self.character], 10))
            self.force(self.memory.choose(options, self.clock,
                                          PREFERENCES[self.character]))

    def step(self, seconds: float, frozen: bool = False, advance_state: bool = True):
        if frozen:
            return
        dt = min(max(seconds, 0.0), 0.1)
        self.clock += dt
        if not advance_state:
            return
        if self.transition.active:
            self.transition.step(dt)
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish()

    @property
    def walking(self):
        return self.state == "walk" and not self.transition.active

    @property
    def phase(self):
        return "enter" if self.transition.active else self.activities[self.state].phase(self.elapsed, self.duration)

    def pose(self):
        return self.transition.pose() or gesture_pose(self.character, self.state, self.elapsed, self.duration)

    @property
    def pace(self):
        if self.run_start is None:
            return self.base_pace * self.movement_ease
        time = self.elapsed - self.run_start
        if not 0 < time < self.run_duration:
            return self.base_pace * self.movement_ease
        # Ease both acceleration and deceleration, without switching drawing clips.
        ramp = min(1.0, time / 0.6, (self.run_duration - time) / 0.6)
        eased = ramp * ramp * (3 - 2 * ramp)
        return (self.base_pace + (1.65 - self.base_pace) * eased) * self.movement_ease

    @property
    def movement_ease(self):
        if self.state != "walk":
            return 1.0
        ramp = max(0, min(1, self.elapsed / 0.8, (self.duration - self.elapsed) / 0.8))
        return 0.15 + 0.85 * ramp * ramp * (3 - 2 * ramp)

    def consume_hop(self):
        if self.hop_at is not None and self.elapsed >= self.hop_at:
            self.hop_at = None
            return True
        return False
