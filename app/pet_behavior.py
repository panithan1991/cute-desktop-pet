"""Unhurried, varied activities with a clock that freezes during pause/drag."""

import random


class PetBehavior:
    def __init__(self, character: str, rng: random.Random | None = None):
        self.character = character
        self.rng = rng if rng is not None else random.Random()
        self.previous = None
        self.state = "idle"
        self.elapsed = 0.0
        self.clock = 0.0
        self.next_run = self.rng.uniform(90, 180)
        self._configure()

    def _configure(self):
        ranges = {"walk": (20, 45), "idle": (15, 30),
                  "sleep": (40, 90), "roll": (5, 7)}
        if self.character == "bunny":
            ranges["walk"] = (18, 35)
        elif self.character == "bibi":
            ranges["walk"] = (25, 45)
        self.duration = self.rng.uniform(*ranges[self.state])
        # Most rests are neutral. A head tilt happens once in a rare curious rest.
        self.variant = 3 if self.state == "idle" and self.rng.random() < 0.2 else 1
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
        self.previous, self.state = self.state, state
        self.elapsed = 0.0
        self._configure()

    def finish(self):
        choices = {
            "walk": (("idle", "sleep", "roll"), (70, 25, 5)),
            "idle": (("walk", "sleep", "roll"), (65, 30, 5)),
            "sleep": (("idle", "walk"), (65, 35)),
            "roll": (("idle", "walk"), (75, 25)),
        }
        states, weights = choices[self.state]
        # Discourage the same two activities from alternating indefinitely.
        weights = [weight * (0.35 if state == self.previous else 1)
                   for state, weight in zip(states, weights)]
        self.force(self.rng.choices(states, weights=weights, k=1)[0])

    def step(self, seconds: float, frozen: bool = False):
        if frozen:
            return
        dt = min(max(seconds, 0.0), 0.1)
        self.clock += dt
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish()

    @property
    def walking(self):
        return self.state == "walk"

    @property
    def pace(self):
        if self.run_start is None:
            return self.base_pace
        time = self.elapsed - self.run_start
        if not 0 < time < self.run_duration:
            return self.base_pace
        # Ease both acceleration and deceleration, without switching drawing clips.
        ramp = min(1.0, time / 0.6, (self.run_duration - time) / 0.6)
        eased = ramp * ramp * (3 - 2 * ramp)
        return self.base_pace + (1.65 - self.base_pace) * eased

    def consume_hop(self):
        if self.hop_at is not None and self.elapsed >= self.hop_at:
            self.hop_at = None
            return True
        return False
