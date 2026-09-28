"""Continuous clip timing for the rabbit, puppy and kitten."""

import math

from app.animation_clips import CLIPS, progress_pose


def resting_pose(state: str, elapsed: float, duration: float, variant: int = 1,
                 blink: bool = False) -> str:
    """Enter/leave sleep once; hold closed eyes instead of replaying a whole nap."""
    if state == "roll":
        return progress_pose("roll", elapsed / max(duration, 0.001))
    if state == "sleep":
        if elapsed < 3:
            return CLIPS["sleep"][min(7, int(elapsed / 3 * 8))]
        if duration - elapsed < 3:
            return CLIPS["sleep"][min(14, 11 + int((3 - max(0, duration - elapsed)) / 3 * 4))]
        # These three drawings all have closed eyes. A slow breath never wakes it.
        breath = (1 - math.cos((elapsed - 3) * math.tau / 7)) / 2
        return CLIPS["sleep"][8 + min(2, int(breath * 3))]
    if variant == 3 and 8 <= elapsed < 14:
        # One small excursion and return, rather than repeated left/right tilts.
        progress = (elapsed - 8) / 6
        return CLIPS["idle"][min(3, int(math.sin(progress * math.pi) * 4))]
    if blink:
        return CLIPS["idle"][9]
    return CLIPS["idle"][0]


def choose_pet_pose(
    character: str, *, walking: bool, walk_time: float, rest_progress: float,
    rest_variant: int, airborne: bool, jump_velocity: float, landed: bool,
    blink: bool, paused: bool, roll_progress: float | None = None,
    jump_progress: float | None = None,
    rest_time: float | None = None,
    rest_state: str | None = None, rest_duration: float = 60,
    pace: float = 1.0,
) -> str:
    if paused:
        return CLIPS["sleep"][8]
    if airborne:
        progress = jump_progress if jump_progress is not None else (0.3 if jump_velocity > 0 else 0.7)
        return progress_pose("hop", progress)
    if landed:
        return CLIPS["hop"][-1]
    if roll_progress is not None:
        return progress_pose("roll", roll_progress)
    if walking:
        return CLIPS["walk"][int(walk_time * 12 * pace) % len(CLIPS["walk"])]
    # Blinks belong to the idle clip instead of unrelated full-body drawings.
    clip = "idle" if rest_variant % 3 == 1 else "sleep"
    if rest_time is not None:
        return resting_pose(rest_state or clip, rest_time, rest_duration, rest_variant, blink)
    if blink and clip == "idle":
        return CLIPS["idle"][9]
    return progress_pose(clip, rest_progress)
