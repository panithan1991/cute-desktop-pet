"""Small, testable movement model for the desktop pet."""

from dataclasses import dataclass


@dataclass
class PetMotion:
    x: float
    direction: int = 1
    speed: float = 65.0
    paused: bool = False

    def step(self, seconds: float, left: float, right: float) -> None:
        """Move within a horizontal work area, turning around at either edge."""
        if right < left:
            right = left
        self.x = min(max(self.x, left), right)
        if self.paused:
            return

        # A resumed computer must not make the pet jump across the desktop.
        seconds = min(max(seconds, 0.0), 0.1)
        self.x += self.direction * self.speed * seconds
        if self.x >= right:
            self.x = right
            self.direction = -1
        elif self.x <= left:
            self.x = left
            self.direction = 1
