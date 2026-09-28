"""A sleepy dragon: small gestures, occasional short flights, and long naps."""

import random
import math

DRAGON_LENGTHS = {"idle": 8, "blink": 6, "curious": 6, "tail": 6,
                  "stretch": 6, "smoke": 8, "fire": 8, "takeoff": 10,
                  "hover": 10, "landing": 8, "yawn": 8, "sleep": 8, "wake": 8}
DRAGON_CLIPS = {name: tuple(f"dragon_{name}_{i:02d}" for i in range(count))
                for name, count in DRAGON_LENGTHS.items()}
DRAGON_POSES = tuple(pose for frames in DRAGON_CLIPS.values() for pose in frames)


def dragon_frame(clip, progress):
    frames = DRAGON_CLIPS[clip]
    return frames[min(len(frames) - 1, int(max(0, min(1, progress)) * len(frames)))]


class DragonBehavior:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.previous = None
        self.force("idle")

    def force(self, state):
        self.previous, self.state = getattr(self, "state", None), state
        self.elapsed = 0.0
        ranges = {"idle": (18, 32), "sleep": (45, 90), "walk": (8, 14),
                  "curious": (4, 5), "tail": (4, 6), "stretch": (4, 6),
                  "smoke": (4, 6), "fire": (3, 4), "yawn": (4, 6),
                  "wake": (4, 5)}
        self.duration = self.rng.uniform(*ranges[state])
        self.blink_interval = self.rng.uniform(5, 9)

    def finish(self):
        if self.state == "sleep":
            self.force("wake")
        elif self.state == "yawn":
            self.force("sleep")
        elif self.state != "idle":
            self.force("idle")
        else:
            states = ["tail", "stretch", "smoke", "fire", "yawn", "sleep", "walk", "curious"]
            weights = [15, 15, 15, 8, 15, 15, 14, 3]
            weights = [w * (0.2 if s == self.previous else 1) for s, w in zip(states, weights)]
            self.force(self.rng.choices(states, weights=weights, k=1)[0])

    def step(self, seconds, frozen=False):
        if not frozen:
            self.elapsed += min(max(seconds, 0), 0.1)
            if self.elapsed >= self.duration:
                self.finish()

    @property
    def walking(self):
        return self.state == "walk"

    def pose(self, flight_state="rest", flight_elapsed=0):
        if flight_state == "takeoff":
            return dragon_frame("takeoff", flight_elapsed / 2.4)
        if flight_state == "cruise":
            return dragon_frame("hover", (flight_elapsed % 1.8) / 1.8)
        if flight_state == "landing":
            return dragon_frame("landing", flight_elapsed / 2.8)
        if self.state == "idle":
            blink = self.elapsed % self.blink_interval
            if self.elapsed > self.blink_interval and blink < 1.4:
                return dragon_frame("blink", blink / 1.4)
            return dragon_frame("idle", (self.elapsed % 5) / 5)
        if self.state == "sleep":
            if self.elapsed < 4:
                return dragon_frame("sleep", self.elapsed / 4)
            breath = (1 - math.cos((self.elapsed - 4) * math.tau / 8)) / 2
            return DRAGON_CLIPS["sleep"][5 + min(2, int(breath * 3))]
        if self.state == "walk":
            return DRAGON_CLIPS["idle"][0]
        return dragon_frame(self.state, self.elapsed / self.duration)
