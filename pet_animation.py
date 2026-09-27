"""Pose timing shared by both animated desktop pets."""

from __future__ import annotations


REST_POSES = {
    "bunny": (
        ("sit", "tilt", "groom", "loaf", "sleep"),
        ("idle", "curious", "sniff", "alert", "yawn"),
        ("happy", "wave", "stretch", "playbow", "blink"),
    ),
    "mookrata": (
        ("idle", "happy", "tilt_left", "awake_rest", "sleep"),
        ("happy_sit", "paw_up", "tilt_right", "curled_sleep", "stretch"),
        ("sniff_low", "sniff_air", "sniff_close", "playbow", "playbow_two"),
    ),
}
WALK_POSES = {
    "bunny": ("side_idle", "run_a", "run_b", "run_a"),
    "mookrata": ("stand_3q", "trot_a", "run_a", "trot_b", "run_b", "stand_side"),
}
ROLL_POSES = ("crouch", "roll_a", "roll_b", "roll_c", "dizzy", "playbow")


def choose_pet_pose(
    character: str,
    *,
    walking: bool,
    walk_time: float,
    rest_progress: float,
    rest_variant: int,
    airborne: bool,
    jump_velocity: float,
    landed: bool,
    blink: bool,
    paused: bool,
    roll_progress: float | None = None,
) -> str:
    """Choose coherent pose sequences; neither pet slides backward."""
    if paused:
        return "loaf" if character == "bunny" else "curled_sleep"
    if airborne:
        if character == "bunny":
            return "hop_up" if jump_velocity > 85 else "hop_air"
        return "hop" if jump_velocity > 85 else "hop_two"
    if landed:
        return "crouch" if character == "bunny" else "land"
    if character == "bunny" and roll_progress is not None:
        return ROLL_POSES[min(int(roll_progress * len(ROLL_POSES)), len(ROLL_POSES) - 1)]
    if walking:
        sequence = WALK_POSES[character]
        return sequence[int(walk_time * (6.8 if character == "bunny" else 8.5)) % len(sequence)]
    sequence = REST_POSES[character][rest_variant % len(REST_POSES[character])]
    index = min(int(max(0.0, min(rest_progress, 1.0)) * len(sequence)), len(sequence) - 1)
    pose = sequence[index]
    if blink and pose in {"idle", "sit", "happy", "happy_sit"}:
        return "blink" if character == "bunny" else "tilt"
    return pose
