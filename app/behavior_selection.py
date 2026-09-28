"""Named activities and a weighted selector that remembers recent behavior."""

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Activity:
    label: str
    duration: tuple[float, float]
    cooldown: float = 0
    enter: float = 0
    exit: float = 0
    group: str = ""

    def phase(self, elapsed, duration):
        if elapsed < self.enter:
            return "enter"
        if duration - elapsed <= self.exit:
            return "exit"
        return "loop"


class BehaviorMemory:
    def __init__(self, rng, activities):
        self.rng, self.activities = rng, activities
        self.recent = deque(maxlen=4)
        self.ready_at = {}

    def record(self, state, clock):
        spec = self.activities[state]
        if state not in {"idle", "wake"}:
            self.recent.append(state)
        # Cooldowns start after the activity, not while it is still playing.
        self.ready_at[state] = clock + spec.cooldown
        if spec.group:
            self.ready_at[spec.group] = clock + spec.cooldown

    def choose(self, options, clock, preferences=None):
        states, weights = [], []
        preferences = preferences or {}
        for state, weight in options.items():
            spec = self.activities[state]
            if clock < max(self.ready_at.get(state, 0), self.ready_at.get(spec.group, 0)):
                continue
            # The latest non-idle action stays in memory across neutral rests.
            penalty = 0.12 if self.recent and self.recent[-1] == state else 1
            penalty *= 0.55 ** self.recent.count(state)
            states.append(state)
            weights.append(weight * preferences.get(state, 1) * penalty)
        if not states:
            return "idle"
        return self.rng.choices(states, weights=weights, k=1)[0]
