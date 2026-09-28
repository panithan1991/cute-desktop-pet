"""Smooth wingbeat and grounded play clips for Bibi."""

from app.animation_clips import CLIPS, progress_pose


def choose_bibi_pose(state: str, elapsed: float, paused: bool = False) -> str:
    if paused:
        return CLIPS["sleep"][8] if state == "rest" else CLIPS["walk"][0]
    if state == "takeoff":
        return progress_pose("hop", min(elapsed / 2.4, 1.0) * 0.55)
    if state == "cruise":
        return CLIPS["walk"][int(elapsed * 20) % len(CLIPS["walk"])]
    if state == "landing":
        return progress_pose("hop", 0.55 + min(elapsed / 2.8, 1.0) * 0.45)
    if elapsed < 4.0:
        return progress_pose("idle", elapsed / 4.0)
    if elapsed < 10.0:
        return progress_pose("sleep", (elapsed - 4.0) / 6.0)
    return progress_pose("roll", (elapsed - 10.0) / 3.2)
