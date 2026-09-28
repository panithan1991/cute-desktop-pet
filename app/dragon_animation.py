"""A sleepy dragon: small gestures, occasional short flights, and long naps."""

import random
import math

from app.behavior_selection import Activity, BehaviorMemory
from app.behavior_art import PostureTransition, gesture_pose

DRAGON_ACTIVITIES = {
    "idle": Activity("Sleepy breathing", (18, 32)),
    "sleep": Activity("Curled nap", (45, 90), 45, enter=4),
    "walk": Activity("Gentle hover", (8, 14), 90, enter=2.4, exit=2.8),
    "curious": Activity("Small head tilt", (4, 5), 240, enter=1, exit=1),
    "tail": Activity("Tail sway", (4, 6), 45, enter=1, exit=1),
    "stretch": Activity("Wing stretch", (4, 6), 60, enter=1, exit=1),
    "smoke": Activity("Volumetric smoke ring", (6, 8), 75, enter=1.5, exit=1.5),
    "fire": Activity("Golden flame breath", (5, 7), 120, enter=1, exit=1.5),
    "yawn": Activity("Sleepy yawn", (4, 6), 60, enter=1, exit=1),
    "wake": Activity("Uncurl and wake", (4, 5), enter=4),
    "hug_tail": Activity("Hug tail during a nap", (6, 9), 150, enter=1, exit=1),
    "hiccup": Activity("Tiny smoky hiccup", (4, 6), 180, enter=1, exit=1),
    "wing_blanket": Activity("Sleep under wings", (7, 10), 180, enter=1, exit=1),
    "threat": Activity("Warning glare and wing display", (5, 7), 120, enter=1.5, exit=1.5),
    "roar": Activity("Small fierce roar", (5, 7), 180, enter=1.5, exit=1.5),
    "storm_hover": Activity("Stationary wingbeats and rapid horn lightning", (7, 9), 210, enter=1, exit=1),
}

DRAGON_LENGTHS = {"idle": 8, "blink": 6, "curious": 6, "tail": 6,
                  "stretch": 6, "smoke": 43, "fire": 43, "takeoff": 10,
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
        self.clock = 0.0
        self.memory = BehaviorMemory(self.rng, DRAGON_ACTIVITIES)
        self.transition = PostureTransition("dragon")
        self.force("idle")

    def force(self, state):
        if state not in DRAGON_ACTIVITIES:
            raise ValueError(f"Unknown dragon behavior: {state}")
        if hasattr(self, "state"):
            self.memory.record(self.state, self.clock)
            # The dedicated wake activity already uncurls the body.
            self.transition.connect(self.state, state)
            if state == "wake" or self.state == "wake":
                self.transition.queue = []
        self.previous, self.state = getattr(self, "state", None), state
        self.elapsed = 0.0
        if state == "sleep" and self.previous in {"hug_tail", "wing_blanket", "sleep"}:
            self.elapsed = 4.0
        self.duration = self.rng.uniform(*DRAGON_ACTIVITIES[state].duration)
        self.blink_interval = self.rng.uniform(5, 9)

    def finish(self):
        if self.state == "sleep":
            self.force("wake")
        elif self.state in {"yawn", "hug_tail", "wing_blanket"}:
            self.force("sleep")
        elif self.state != "idle":
            self.force("idle")
        else:
            self.force(self.memory.choose({"tail": 15, "stretch": 15, "smoke": 15,
                       "fire": 8, "yawn": 15, "sleep": 15, "walk": 14, "curious": 3,
                       "hug_tail": 10, "hiccup": 6, "wing_blanket": 10,
                       "threat": 8, "roar": 6, "storm_hover": 8}, self.clock))

    def step(self, seconds, frozen=False, advance_state=True):
        if not frozen:
            dt = min(max(seconds, 0), 0.1)
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
        return "enter" if self.transition.active else DRAGON_ACTIVITIES[self.state].phase(self.elapsed, self.duration)

    def pose(self, flight_state="rest", flight_elapsed=0):
        if flight_state == "takeoff":
            return dragon_frame("takeoff", flight_elapsed / 2.4)
        if flight_state == "cruise":
            return dragon_frame("hover", (flight_elapsed % 1.8) / 1.8)
        if flight_state == "landing":
            return dragon_frame("landing", flight_elapsed / 2.8)
        connecting = self.transition.pose()
        if connecting:
            return connecting
        extra = gesture_pose("dragon", "wake_stretch" if self.state == "wake" else self.state,
                             self.elapsed, self.duration)
        if extra:
            return extra
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
