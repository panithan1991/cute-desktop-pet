"""Small, testable movement model for the desktop pet."""

from dataclasses import dataclass, field
import math
import random


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


@dataclass
class BibiFlightMotion:
    """A grounded bird that climbs into the upper desktop, cruises in 2D, and lands."""

    x: float
    y: float
    direction: int = 1
    speed: float = 95.0
    paused: bool = False
    state: str = "rest"
    elapsed: float = 0.0
    start_y: float = 0.0
    landing_y: float = 0.0
    auto_launch: bool = True
    cruise_duration: float = 30.0
    rest_duration: float = 60.0
    altitude: float = 0.18
    wave_speed: float = 0.5
    rng: random.Random = field(default_factory=random.Random, repr=False)

    def launch(self) -> bool:
        if self.paused or self.state != "rest":
            return False
        self.state = "takeoff"
        self.elapsed = 0.0
        self.start_y = self.y
        self.altitude = self.rng.uniform(0.14, 0.28)
        self.wave_speed = self.rng.uniform(0.35, 0.65)
        return True

    def reset(self, x: float, ground: float) -> None:
        self.x, self.y = x, ground
        self.state = "rest"
        self.elapsed = 0.0

    def step(self, seconds: float, left: float, top: float, right: float, ground: float) -> None:
        right = max(left, right)
        ground = max(top, ground)
        self.x = min(max(self.x, left), right)
        self.y = min(max(self.y, top), ground)
        if self.paused:
            return
        dt = min(max(seconds, 0.0), 0.1)
        self.elapsed += dt
        if self.state == "rest":
            self.y = ground
            if self.auto_launch and self.elapsed >= self.rest_duration:
                self.launch()
            return

        horizontal = 0.65 if self.state in {"takeoff", "landing"} else 1.0
        self.x += self.direction * self.speed * horizontal * dt
        if self.x >= right:
            self.x, self.direction = right, -1
        elif self.x <= left:
            self.x, self.direction = left, 1

        # Vary the cruising height while staying above the desktop midpoint.
        high = top + (ground - top) * self.altitude
        if self.state == "takeoff":
            progress = min(self.elapsed / 2.4, 1.0)
            eased = progress * progress * (3 - 2 * progress)
            self.y = self.start_y + (high - self.start_y) * eased
            if progress >= 1:
                self.state, self.elapsed = "cruise", 0.0
        elif self.state == "cruise":
            amplitude = min(64.0, (ground - top) * 0.08)
            self.y = high + amplitude * math.sin(self.elapsed * self.wave_speed)
            if self.elapsed >= self.cruise_duration:
                self.state, self.elapsed = "landing", 0.0
                self.landing_y = self.y
        else:
            progress = min(self.elapsed / 2.8, 1.0)
            eased = progress * progress * (3 - 2 * progress)
            self.y = self.landing_y + (ground - self.landing_y) * eased
            if progress >= 1:
                self.state, self.elapsed = "rest", 0.0
                self.y = ground
