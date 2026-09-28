"""Bake the 36 referenced dragon keyframes into 100 padded runtime frames.

Uses the existing bounded optical-flow baker. Detached smoke and flame are
retained, and their extents determine the shared scale for the whole atlas.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.dragon_animation import DRAGON_LENGTHS
from build_pet_atlases import CELL, inbetweens

KEYS = {"idle": [0, 1, 2, 3], "blink": [4, 5, 6], "curious": [7, 8, 9],
        "tail": [10, 11, 12], "stretch": [13, 14, 15], "smoke": [16, 17, 18],
        "fire": [19, 20, 21], "takeoff": [22, 23, 24], "hover": [24, 25, 26],
        "landing": [27, 28, 29], "yawn": [30, 31, 32], "sleep": [33, 34, 35],
        "wake": [35, 34, 33, 0]}


def build():
    sheet = Image.open(ROOT / "assets/source/dragon-keyframes.png").convert("RGBA")
    pixels = np.asarray(sheet).copy()
    count, labels, stats, centers = cv2.connectedComponentsWithStats(
        np.uint8(pixels[:, :, 3] > 48), 8)
    bodies = list(np.argsort(stats[1:, cv2.CC_STAT_AREA])[-36:] + 1)
    if min(stats[i, cv2.CC_STAT_AREA] for i in bodies) < 1000:
        raise ValueError("Expected 36 complete dragons")
    bodies.sort(key=lambda i: centers[i, 1])
    ordered = []
    for row in range(6):
        ordered.extend(sorted(bodies[row*6:row*6+6], key=lambda i: centers[i, 0]))
    groups = {i: [i] for i in ordered}
    for component in range(1, count):
        if component in groups or stats[component, cv2.CC_STAT_AREA] < 12:
            continue
        # Assign detached smoke/flame to its nearest complete dragon, never trim
        # at guessed row boundaries (generated sheets have slightly uneven rows).
        nearest = min(ordered, key=lambda i: np.linalg.norm(centers[i]-centers[component]))
        groups[nearest].append(component)
    cells, anchors = [], []
    for body_id in ordered:
        mask = np.uint8(np.isin(labels, groups[body_id]))
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        subject = pixels.copy()
        subject[mask == 0] = 0
        cell = Image.fromarray(subject)
        bounds = cell.getchannel("A").getbbox()
        if min(bounds[0], bounds[1], sheet.width-bounds[2], sheet.height-bounds[3]) < 2:
            raise ValueError("Dragon/effect touches source edge; redraw before baking")
        body = stats[body_id]
        anchors.append((body[0]+body[2]/2-bounds[0], body[1]+body[3]-bounds[1]))
        cells.append(cell.crop(bounds))
    # A single scale for every pose/effect, anchored on the body rather than smoke.
    scale = min(min(68 / max(ax-b[0], b[2]-ax, 1), 132 / max(ay-b[1], 1))
                for cell, (ax, ay) in zip(cells, anchors)
                for b in [cell.getchannel("A").getbbox()])
    normalized = []
    for cell, (ax, ay) in zip(cells, anchors):
        resized = cell.resize((round(cell.width*scale), round(cell.height*scale)), Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (CELL, CELL))
        frame.alpha_composite(resized, (round(80-ax*scale), round(144-ay*scale)))
        normalized.append(frame)
    frames = []
    for clip, length in DRAGON_LENGTHS.items():
        keys = KEYS[clip]
        base, extra = divmod(length - 1, len(keys) - 1)
        for segment in range(len(keys)-1):
            frames.extend(inbetweens(normalized[keys[segment]], normalized[keys[segment+1]],
                                    base + (segment < extra)))
        frames.append(normalized[keys[-1]])
    assert len(frames) == sum(DRAGON_LENGTHS.values())
    atlas = Image.new("RGBA", (CELL*5, CELL*(len(frames)//5)))
    left = Image.new("RGBA", atlas.size)
    for i, frame in enumerate(frames):
        bounds = frame.getchannel("A").point(lambda a: 255 if a > 32 else 0).getbbox()
        assert min(bounds[0], bounds[1], CELL-bounds[2], CELL-bounds[3]) >= 6, (i, bounds)
        position = (i % 5 * CELL, i // 5 * CELL)
        atlas.alpha_composite(frame, position)
        left.alpha_composite(ImageOps.mirror(frame), position)
    for image, suffix in ((atlas, ""), (left, "-left")):
        image.save(ROOT / f"assets/dragon-motion{suffix}.png", optimize=True)
        hard = image.copy()
        hard.putalpha(image.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        hard.save(ROOT / f"assets/dragon-motion{suffix}-windows.png", optimize=True)
    frames[0].save(ROOT / "assets/readme/dragon.png")
    frames[0].resize((256, 256), Image.Resampling.LANCZOS).save(ROOT / "icons/dragon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    demo = []
    for frame in frames:
        background = Image.new("RGB", frame.size, "#e8edf2")
        background.paste(frame, mask=frame.getchannel("A"))
        demo.append(background)
    demo[0].save(ROOT / "assets/readme/dragon.gif", save_all=True, append_images=demo[1:],
                 duration=130, loop=0, disposal=2)
    print(f"Dragon: {len(frames)} base frames; all dragon, smoke and flame bounds padded")


if __name__ == "__main__":
    build()
