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


@dataclass
class JumpMotion:
    """A short gravity-driven jump measured above the pet's resting level."""

    height: float = 0.0
    velocity: float = 0.0
    launch_speed: float = 340.0
    gravity: float = 1050.0

    @property
    def airborne(self) -> bool:
        return self.height > 0 or self.velocity > 0

    def jump(self) -> bool:
        if self.airborne:
            return False
        self.velocity = self.launch_speed
        return True

    def step(self, seconds: float, ceiling: float) -> None:
        seconds = min(max(seconds, 0.0), 0.1)
        if not self.airborne:
            return
        self.height += self.velocity * seconds - 0.5 * self.gravity * seconds**2
        self.velocity -= self.gravity * seconds
        if self.height >= max(0.0, ceiling):
            self.height = max(0.0, ceiling)
            self.velocity = min(self.velocity, 0.0)
        if self.height <= 0:
            self.height = 0.0
            self.velocity = 0.0

    def reset(self) -> None:
        self.height = 0.0
        self.velocity = 0.0


@dataclass
class FlightMotion:
    """Continuous diagonal flight inside the usable desktop rectangle."""

    x: float
    y: float
    dx: float = 0.88
    dy: float = -0.48
    speed: float = 145.0
    paused: bool = False

    def step(
        self, seconds: float, left: float, top: float, right: float, bottom: float
    ) -> None:
        right = max(left, right)
        bottom = max(top, bottom)
        self.x = min(max(self.x, left), right)
        self.y = min(max(self.y, top), bottom)
        if self.paused:
            return
        seconds = min(max(seconds, 0.0), 0.1)
        self.x += self.dx * self.speed * seconds
        self.y += self.dy * self.speed * seconds
        if self.x >= right:
            self.x = right
            self.dx = -abs(self.dx)
        elif self.x <= left:
            self.x = left
            self.dx = abs(self.dx)
        if self.y >= bottom:
            self.y = bottom
            self.dy = -abs(self.dy)
        elif self.y <= top:
            self.y = top
            self.dy = abs(self.dy)
