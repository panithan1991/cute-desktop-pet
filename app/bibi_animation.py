"""Smooth wingbeat and grounded play clips for Bibi."""

from app.animation_clips import CLIPS, progress_pose
from app.pet_animation import resting_pose


def choose_bibi_pose(state: str, elapsed: float, paused: bool = False, *,
                     rest_state: str = "idle", rest_elapsed: float = 0,
                     rest_duration: float = 60, variant: int = 1,
                     blink: bool = False) -> str:
    if paused:
        return CLIPS["sleep"][8] if state == "rest" else CLIPS["walk"][0]
    if state == "takeoff":
        return progress_pose("hop", min(elapsed / 2.4, 1.0) * 0.55)
    if state == "cruise":
        return CLIPS["walk"][int(elapsed * 12) % len(CLIPS["walk"])]
    if state == "landing":
        return progress_pose("hop", 0.55 + min(elapsed / 2.8, 1.0) * 0.45)
    return resting_pose(rest_state, rest_elapsed, rest_duration, variant, blink)
