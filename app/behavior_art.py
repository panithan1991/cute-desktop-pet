"""Painted gestures and reversible posture transitions for each illustrated pet."""

SIGNATURES = {
    "bunny": ("wash_face", "sniff", "hind_stretch"),
    "mookrata": ("wag_tail", "sniff_ground", "play_bow"),
    "kitten": ("groom", "knead", "watch_tail"),
    "bibi": ("preen", "wing_stretch", "one_leg"),
    "dragon": ("hug_tail", "hiccup", "wing_blanket"),
}
EXTRA_CLIPS = {
    character: {name: tuple(f"extra_{name}_{i:02d}" for i in range(length))
                for name, length in [("wake_stretch", 25),
                                     *[(name, 20) for name in signatures],
                                     ("travel_ready", 25)]}
    for character, signatures in SIGNATURES.items()
}
EXTRA_CLIPS["dragon"]["hiccup"] = tuple(f"extra_hiccup_{i:02d}" for i in range(25))
for name, length in (("threat", 30), ("roar", 30), ("storm_hover", 140), ("wing_gust", 60), ("belly_smoke", 120), ("roll_enter", 15), ("roll_loop", 90), ("roll_exit", 15), ("fury", 180), ("ground_ready", 25), ("ground_walk", 40), ("run", 40), ("ignition_reaction", 40)):
    EXTRA_CLIPS["dragon"][name] = tuple(f"extra_{name}_{i:02d}" for i in range(length))
from app.dragon_personality import NEW_ACTIVITIES, PERCH_CLIPS
for name in (*NEW_ACTIVITIES, *PERCH_CLIPS):
    EXTRA_CLIPS['dragon'][name] = tuple(f'extra_{name}_{i:02d}' for i in range(40))
EXTRA_POSES = {character: tuple(pose for clip in clips.values() for pose in clip)
               for character, clips in EXTRA_CLIPS.items()}


def gesture_pose(character, state, elapsed, duration):
    clips = EXTRA_CLIPS[character]
    if state not in clips:
        return None
    clip = clips[state]
    progress = max(0, min(1, elapsed / max(duration, 0.001)))
    return clip[min(len(clip) - 1, int(progress * len(clip)))]


def posture(state):
    if state in {"ground_walk", "run"}:
        return "ground_travel"
    if state in {"sleep", "lounge", "roll", "belly_up", "hug_tail", "wing_blanket"}:
        return "lying"
    if state in {"walk", "hover_float", "dive_recover", "air_brake", "perch_landing"}:
        return "travel"
    return "upright"


class PostureTransition:
    """Join activities through painted body poses; never move while turning."""
    def __init__(self, character):
        self.character = character
        self.queue = []
        self.elapsed = 0.0

    def connect(self, source, target):
        self.queue, self.elapsed = [], 0.0
        start, end = posture(source), posture(target)
        if start == end:
            return
        if start == "travel":
            self.queue.append(("travel_ready", True, 2.4))
        if start == "ground_travel":
            self.queue.append(("ground_ready", True, 1.8))
        if start == "lying":
            self.queue.append(("wake_stretch", False, 4.5))
        if end == "lying":
            self.queue.append(("wake_stretch", True, 4.5))
        if end == "travel":
            self.queue.append(("travel_ready", False, 2.4))
        if end == "ground_travel":
            self.queue.append(("ground_ready", False, 1.8))

    @property
    def active(self):
        return bool(self.queue)

    def step(self, seconds):
        if self.queue:
            self.elapsed += seconds
            if self.elapsed >= self.queue[0][2]:
                self.queue.pop(0)
                self.elapsed = 0.0

    def pose(self):
        if not self.queue:
            return None
        name, reverse, duration = self.queue[0]
        frames = EXTRA_CLIPS[self.character][name] if isinstance(name,str) else name
        index = min(len(frames)-1, int(self.elapsed / duration * len(frames)))
        return frames[len(frames)-1-index if reverse else index]
