"""Pre-baked wingbeat-to-grip and release-to-landing bridges."""
JOIN_SECONDS=.42
JOIN_FRAMES=6
FLIGHT_JOIN_POSES=tuple(f'flight_join_{phase:02d}_{i:02d}' for phase in range(10) for i in range(JOIN_FRAMES))
LANDING_JOIN_POSES=tuple(f'landing_join_{i:02d}' for i in range(JOIN_FRAMES))
TOUCHDOWN_JOIN_POSES=tuple(f'touchdown_join_{i:02d}' for i in range(JOIN_FRAMES))
