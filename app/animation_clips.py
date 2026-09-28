"""The same 85-frame layout for all four illustrated pets."""

CLIP_LENGTHS = {"idle": 15, "walk": 20, "roll": 20, "sleep": 15, "hop": 15}
CLIPS = {
    name: tuple(f"{name}_{index:02d}" for index in range(count))
    for name, count in CLIP_LENGTHS.items()
}
ALL_POSES = tuple(pose for clip in CLIPS.values() for pose in clip)


def progress_pose(clip: str, progress: float) -> str:
    frames = CLIPS[clip]
    progress = max(0.0, min(progress, 1.0))
    return frames[min(int(progress * len(frames)), len(frames) - 1)]
