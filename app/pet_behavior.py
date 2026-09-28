"""Unhurried, varied activities with a clock that freezes during pause/drag."""

import random

from app.behavior_selection import Activity, BehaviorMemory

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
        self.memory = BehaviorMemory(self.rng, ACTIVITIES)
        self.next_run = self.rng.uniform(90, 180)
        self._configure()

    def _configure(self):
        limits = ACTIVITIES[self.state].duration
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
        if state not in ACTIVITIES:
            raise ValueError(f"Unknown pet behavior: {state}")
        self.memory.record(self.state, self.clock)
        self.previous, self.state = self.state, state
        self.elapsed = 0.0
        self._configure()

    def finish(self):
        # Sleep and play end lying down: keep that posture in the next rest.
        if self.state in {"sleep", "roll", "belly_up"}:
            self.force("lounge")
        elif self.state == "curious":
            self.force("idle")
        else:
            self.force(self.memory.choose(NEXT_ACTIVITIES[self.state], self.clock,
                                          PREFERENCES[self.character]))

    def step(self, seconds: float, frozen: bool = False, advance_state: bool = True):
        if frozen:
            return
        dt = min(max(seconds, 0.0), 0.1)
        self.clock += dt
        if not advance_state:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish()

    @property
    def walking(self):
        return self.state == "walk"

    @property
    def phase(self):
        return ACTIVITIES[self.state].phase(self.elapsed, self.duration)

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
        if not self.walking:
            return 1.0
        ramp = max(0, min(1, self.elapsed / 0.8, (self.duration - self.elapsed) / 0.8))
        return 0.15 + 0.85 * ramp * ramp * (3 - 2 * ramp)

    def consume_hop(self):
        if self.hop_at is not None and self.elapsed >= self.hop_at:
            self.hop_at = None
            return True
        return False
