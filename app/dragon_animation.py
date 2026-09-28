"""A sleepy dragon: small gestures, occasional short flights, and long naps."""

import random
import math

from app.behavior_selection import Activity, BehaviorMemory
from app.behavior_art import PostureTransition, gesture_pose

DRAGON_ACTIVITIES = {
    "idle": Activity("Sleepy breathing", (8, 14)),
    "sleep": Activity("Curled nap", (45, 55), 100, enter=4),
    "walk": Activity("Soaring flight", (25, 45), 40, enter=2.4, exit=2.8),
    "curious": Activity("Small head tilt", (2.5, 4.0), 30, enter=1, exit=1),
    "tail": Activity("Tail sway", (3, 4.5), 25, enter=1, exit=1),
    "stretch": Activity("Wing stretch", (3.5, 5), 30, enter=1, exit=1),
    "smoke": Activity("Volumetric smoke ring", (4.5, 6.0), 8, enter=1.2, exit=1.2),
    "fire": Activity("Grand fantasy flame breath", (12, 16), 10, enter=1.5, exit=2),
    "yawn": Activity("Sleepy yawn", (3.0, 4.5), 60, enter=1, exit=1),
    "wake": Activity("Uncurl and wake", (4, 5), enter=4),
    "hug_tail": Activity("Hug tail during a nap", (4, 6), 60, enter=1, exit=1),
    "hiccup": Activity("Tiny smoky hiccup", (2.5, 3.5), 25, enter=1, exit=1),
    "wing_blanket": Activity("Sleep under wings", (5, 7), 60, enter=1, exit=1),
    "threat": Activity("Warning glare and wing display", (3.5, 4.8), 30, enter=1.2, exit=1.2),
    "roar": Activity("Small fierce roar", (3.5, 4.8), 35, enter=1.2, exit=1.2),
    "fury": Activity("Two-legged fiery thunder fury", (12,16), 90, enter=2, exit=2),
    "belly_smoke": Activity("Belly-up sky smoke rings", (14,18), 35, enter=3, exit=3),
    "wing_gust": Activity("Seated one-wing whirlwind", (7, 9), 32, enter=1.2, exit=1.5),
    "storm_hover": Activity("Stationary wingbeats and rapid horn lightning", (6.0, 7.5), 35, enter=1, exit=1),
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
            # Finish the remaining painted exit when a menu command interrupts
            # an upright gesture. Keep the current frame as the bridge start.
            source_pose = self.pose()
            source_clip = DRAGON_CLIPS.get(self.state)
            if source_clip is None:
                from app.behavior_art import EXTRA_CLIPS
                source_clip = EXTRA_CLIPS["dragon"].get(self.state)
            self.transition.connect(self.state, state)
            if self.state not in {"idle", "sleep", "wake", "walk", "hug_tail", "wing_blanket"} and source_clip and source_pose in source_clip:
                remainder = source_clip[source_clip.index(source_pose):]
                if len(remainder)>1:
                    self.transition.queue.insert(0,(remainder,False,max(.4,min(2.5,len(remainder)*.06))))
            if state == "wake" or self.state == "wake":
                self.transition.queue = []
        self.previous, self.state = getattr(self, "state", None), state
        self.elapsed = 0.0
        if state == "sleep" and (self.transition.active or self.previous in {"hug_tail", "wing_blanket", "sleep"}):
            self.elapsed = 4.0
        self.duration = self.rng.uniform(*DRAGON_ACTIVITIES[state].duration)
        self.blink_interval = self.rng.uniform(4, 6.5)

    def finish(self):
        if self.state == "sleep":
            self.force("wake")
        elif self.state in {"yawn", "hug_tail", "wing_blanket"}:
            self.force("sleep")
        elif self.state != "idle":
            self.force("idle")
        else:
            self.force(self.memory.choose({
                "fire": 40,
                "smoke": 38,
                "storm_hover": 24,
                "wing_gust": 18,
                "belly_smoke": 20,
                "fury": 10,
                "walk": 18,
                "threat": 15,
                "roar": 14,
                "hiccup": 12,
                "stretch": 8,
                "tail": 8,
                "curious": 6,
                "yawn": 4,
                "sleep": 3,
                "hug_tail": 3,
                "wing_blanket": 3,
            }, self.clock))

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
