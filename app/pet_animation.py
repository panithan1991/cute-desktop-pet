"""Continuous clip timing for the rabbit, puppy and kitten."""

from app.animation_clips import CLIPS, progress_pose


def choose_pet_pose(
    character: str, *, walking: bool, walk_time: float, rest_progress: float,
    rest_variant: int, airborne: bool, jump_velocity: float, landed: bool,
    blink: bool, paused: bool, roll_progress: float | None = None,
    jump_progress: float | None = None,
    rest_time: float | None = None,
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
        return CLIPS["walk"][int(walk_time * 18) % len(CLIPS["walk"])]
    # Blinks belong to the idle clip instead of unrelated full-body drawings.
    clip = "idle" if rest_variant % 3 == 1 else "sleep"
    if blink and clip == "idle":
        return CLIPS["idle"][9]
    if rest_time is not None:
        return progress_pose(clip, (rest_time % 2.2) / 2.2)
    return progress_pose(clip, rest_progress)
