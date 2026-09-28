"""A sleepy dragon: small gestures, occasional short flights, and long naps."""

import random
import math

from app.behavior_selection import Activity, BehaviorMemory
from app.behavior_art import PostureTransition, gesture_pose
from app.dragon_personality import NEW_ACTIVITIES, AIR_GESTURES, PERCH_POWERS

DRAGON_ACTIVITIES = {
    "idle": Activity("Sleepy breathing", (8, 14)),
    "sleep": Activity("Curled nap", (45, 55), 100, enter=4),
    "walk": Activity("Soaring flight", (25, 45), 40, enter=2.4, exit=2.8),
    "ground_walk": Activity("Sleepy ground stroll", (18, 30), 30),
    "run": Activity("Short playful ground run", (5, 8), 85),
    "curious": Activity("Small head tilt", (2.5, 4.0), 30, enter=1, exit=1),
    "tail": Activity("Tail sway", (3, 4.5), 25, enter=1, exit=1),
    "stretch": Activity("Wing stretch", (3.5, 5), 30, enter=1, exit=1),
    "smoke": Activity("Volumetric smoke ring", (4.5, 6.0), 8, enter=1.2, exit=1.2),
    "fire": Activity("Grand fantasy flame breath", (12, 16), 10, enter=1.5, exit=2),
    "cloud_flame": Activity("Jade smoke cloud and turquoise ignition", (18, 22), 35, enter=1.5, exit=2),
    "yawn": Activity("Sleepy yawn", (3.0, 4.5), 60, enter=1, exit=1),
    "wake": Activity("Uncurl and wake", (4, 5), enter=4),
    "hug_tail": Activity("Hug tail during a nap", (4, 6), 60, enter=1, exit=1),
    "hiccup": Activity("Tiny smoky hiccup", (2.5, 3.5), 25, enter=1, exit=1),
    "wing_blanket": Activity("Sleep under wings", (5, 7), 60, enter=1, exit=1),
    "threat": Activity("Warning glare and wing display", (3.5, 4.8), 30, enter=1.2, exit=1.2),
    "roar": Activity("Small fierce roar", (3.5, 4.8), 35, enter=1.2, exit=1.2),
    "fury": Activity("Two-legged fiery thunder fury", (12,16), 90, enter=2, exit=2),
    "belly_smoke": Activity("Belly-up six sky smoke rings", (36,42), 35, enter=3, exit=3),
    "wing_gust": Activity("Seated one-wing whirlwind", (7, 9), 32, enter=1.2, exit=1.5),
    "storm_hover": Activity("Stationary wingbeats and rapid horn lightning", (6.0, 7.5), 35, enter=1, exit=1),
}

DRAGON_ACTIVITIES.update(NEW_ACTIVITIES)

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
        self.ground_distance = 0.0
        self.turn_pending = False
        self.perched = False
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
            interrupted_ground = []
            if self.transition.active and isinstance(self.transition.queue[0][0],str) and self.transition.queue[0][0] in {'ground_ready','travel_ready','wake_stretch'}:
                from app.behavior_art import EXTRA_CLIPS
                name,reverse,seconds=self.transition.queue[0]
                frames=EXTRA_CLIPS['dragon'][name]
                ordered=frames[::-1] if reverse else frames
                index=ordered.index(source_pose)
                neutral_at_end=(name=='wake_stretch' and not reverse) or (name!='wake_stretch' and reverse)
                return_frames=ordered[index:] if neutral_at_end else ordered[:index+1][::-1]
                if len(return_frames)>1:
                    interrupted_ground=[(return_frames,False,max(.12,seconds*(len(return_frames)-1)/(len(frames)-1)))]
            source_clip = DRAGON_CLIPS.get("fire" if self.state == "cloud_flame" else self.state)
            if self.state=='wake':
                from app.behavior_art import EXTRA_CLIPS
                source_clip=EXTRA_CLIPS['dragon']['wake_stretch']
            if self.state == 'cloud_flame' and source_pose not in source_clip:
                from app.behavior_art import EXTRA_CLIPS
                source_clip=EXTRA_CLIPS['dragon']['ignition_reaction']
            if source_clip is None:
                from app.behavior_art import EXTRA_CLIPS
                source_clip = EXTRA_CLIPS["dragon"].get(self.state)
            self.transition.connect("idle" if interrupted_ground else self.state, state)
            if interrupted_ground:
                self.transition.queue = interrupted_ground + self.transition.queue
            if self.state not in {"idle", "sleep", "wake", "walk", "hug_tail", "wing_blanket", *AIR_GESTURES} and source_clip and source_pose in source_clip:
                remainder = source_clip[source_clip.index(source_pose):]
                if len(remainder)>1:
                    self.transition.queue.insert(0,(remainder,False,max(.4,min(2.5,len(remainder)*.06))))
            if state == "wake" and self.state == "sleep":
                self.transition.queue = []
        self.previous, self.state = getattr(self, "state", None), state
        self.elapsed = 0.0
        self.ground_distance = 0.0
        if state == "sleep" and (self.transition.active or self.previous in {"hug_tail", "wing_blanket", "sleep"}):
            self.elapsed = 4.0
        self.duration = self.rng.uniform(*DRAGON_ACTIVITIES[state].duration)
        self.blink_interval = self.rng.uniform(4, 6.5)
        if self.perched:
            self.transition.queue=[]
            if state=='idle':self.duration=self.rng.uniform(4,7)

    def begin_perch(self):
        self.perched=True
        choice=self.memory.choose({name:1 for name in sorted(PERCH_POWERS)},self.clock)
        self.force(choice if choice in PERCH_POWERS else self.rng.choice(sorted(PERCH_POWERS)))

    def finish(self):
        if self.perched:
            self.force('idle')
        elif self.state == 'static_charge':
            self.force('storm_hover')
        elif self.state in {'fire', 'cloud_flame', 'aurora_breath', 'ember_bubbles', 'thunder_roar'} and self.rng.random()<.35:
            self.force(self.rng.choice(('proud', 'happy')))
        elif self.state == "sleep":
            self.force("wake")
        elif self.state in {"yawn", "hug_tail", "wing_blanket"}:
            self.force("sleep")
        elif self.state != "idle":
            self.force("idle")
        else:
            self.force(self.memory.choose({
                **{name: (14 if name in {'proud','curious_sniff','happy'} else 10 if name=='perch_landing' else 8) for name in NEW_ACTIVITIES},
                "fire": 40,
                "cloud_flame": 18,
                "smoke": 38,
                "storm_hover": 24,
                "wing_gust": 18,
                "belly_smoke": 20,
                "fury": 10,
                "walk": 24,
                "ground_walk": 24,
                "run": 5,
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
        # Legacy travel name used by the shared flight launcher; ground travel
        # must never launch wings or borrow the airborne motion clock.
        return self.state in {'walk', *AIR_GESTURES} and not self.transition.active

    @property
    def grounded_travel(self):
        return self.state in {"ground_walk", "run"} and not self.transition.active

    def move_ground(self, motion, seconds, left, right):
        """Use distance, rather than elapsed time, to drive planted-paw cycles."""
        if not self.grounded_travel or motion.paused:
            return
        dt = min(max(seconds, 0), .1)
        speed = motion.speed
        motion.speed *= .55 if self.state == "ground_walk" else 1.65
        # Ease into travel; decelerate at the work-area edge before turning.
        margin = (right-motion.x) if motion.direction > 0 else (motion.x-left)
        if margin <= .3:
            self.turn_pending = True
            self.finish()
            motion.speed = speed
            return
        motion.speed *= min(1, self.elapsed / .65, max(0, (self.duration-self.elapsed)/.65), max(.08, margin / 20))
        before = motion.x
        motion.step(dt, left, right)
        self.ground_distance += abs(motion.x-before)
        motion.speed = speed

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
        if self.state == "cloud_flame":
            if self.elapsed < self.duration*.52:
                return dragon_frame("fire", self.elapsed / (self.duration * .52))
            # Painted eyes, wing movement and directional green reflections
            # brighten with ignition, then settle back to the exact idle pose.
            return gesture_pose('dragon','ignition_reaction',
                                max(0,self.elapsed-self.duration*.52),self.duration*.45)
        if self.state in {"ground_walk", "run"}:
            from app.behavior_art import EXTRA_CLIPS
            frames = EXTRA_CLIPS["dragon"][self.state]
            stride = 44 if self.state == "ground_walk" else 72
            return frames[int((self.ground_distance % stride) / stride * (len(frames)-1))]
        if self.state=='belly_smoke':
            from app.dragon_belly_timing import belly_pose_index
            from app.behavior_art import EXTRA_CLIPS
            return EXTRA_CLIPS['dragon']['belly_smoke'][belly_pose_index(self.elapsed/self.duration)]
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
