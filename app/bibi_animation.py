"""Pose order for Bibi's ground, takeoff, flight and landing cycles."""

REST = (
    "sit", "idle", "wink", "happy", "tilt_right", "tilt_left", "curious",
    "wave", "cheer", "sleepy", "sleep", "sleep_start", "sleep",
    "wings_happy", "hover_wings", "wings_half", "wings_up", "crouch", "bow",
)
FLIGHT = (
    "fly_glide", "fly_flap", "fly_cheer", "fly_turn", "fly_glide_low",
    "fly_dive", "fly_glide", "hover_happy", "hover_wink", "hover_turn",
)


def choose_bibi_pose(state: str, elapsed: float, paused: bool = False) -> str:
    if paused:
        return "sleep" if state == "rest" else "fly_glide"
    if state == "takeoff":
        return ("crouch", "wings_half", "wings_up", "takeoff", "launch")[
            min(int(elapsed * 3.0), 4)
        ]
    if state == "cruise":
        return FLIGHT[int(elapsed * 4.0) % len(FLIGHT)]
    if state == "landing":
        return ("fly_glide_low", "fly_flap", "hover_turn", "land", "sit")[
            min(int(elapsed * 1.8), 4)
        ]
    return REST[int(elapsed * 2.2) % len(REST)]
