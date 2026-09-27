"""Turn the transparent 6x5 Bibi character sheet into runtime sprite atlases."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/source/bibi-sheet.png"
CELL = 160
COLS, ROWS = 6, 5
# These three source drawings look left; normalize the right-facing atlas.
SOURCE_FACES_LEFT = {15, 16, 17}


def clean_pose(image: Image.Image) -> Image.Image:
    pixels = np.asarray(image.convert("RGBA")).copy()
    alpha = pixels[:, :, 3]
    visible = np.uint8(alpha > 18)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(visible, 8)
    if count > 1:
        biggest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        alpha[labels != biggest] = 0

    # Image generation left isolated crimson/yellow mask marks at the outside
    # of some feathers. The bird's red tongue remains because it is inset.
    mask = np.uint8(alpha > 18)
    distance = cv2.distanceTransform(mask, cv2.DIST_L2, 3)
    red = (pixels[:, :, 0] > 165) & (pixels[:, :, 1] < 115) & (pixels[:, :, 2] < 115)
    neon = (pixels[:, :, 0] > 170) & (pixels[:, :, 1] > 150) & (pixels[:, :, 2] < 75)
    alpha[(red | neon) & (distance < 8)] = 0
    pixels[:, :, 3] = alpha
    cleaned = Image.fromarray(pixels, "RGBA")
    bounds = cleaned.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("Empty Bibi pose")
    cropped = cleaned.crop(bounds)
    scale = min(150 / cropped.width, 150 / cropped.height)
    resized = cropped.resize((round(cropped.width * scale), round(cropped.height * scale)), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL, CELL))
    cell.alpha_composite(resized, ((CELL - resized.width) // 2, CELL - resized.height - 3))
    return cell


def build() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    right = Image.new("RGBA", (COLS * CELL, ROWS * CELL))
    left = Image.new("RGBA", right.size)
    for index in range(COLS * ROWS):
        col, row = index % COLS, index // COLS
        box = (
            round(col * source.width / COLS), round(row * source.height / ROWS),
            round((col + 1) * source.width / COLS), round((row + 1) * source.height / ROWS),
        )
        frame = clean_pose(source.crop(box))
        if index in SOURCE_FACES_LEFT:
            frame = ImageOps.mirror(frame)
        right.alpha_composite(frame, (col * CELL, row * CELL))
        left.alpha_composite(ImageOps.mirror(frame), (col * CELL, row * CELL))

    for image, facing in ((right, ""), (left, "-left")):
        image.save(ROOT / f"assets/bibi-motion{facing}.png", optimize=True)
        hard = image.copy()
        hard.putalpha(image.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        hard.save(ROOT / f"assets/bibi-motion{facing}-windows.png", optimize=True)

    preview = right.crop((0, 0, CELL, CELL))
    preview.save(ROOT / "assets/readme/bibi.png", optimize=True)
    icon = preview.resize((256, 256), Image.Resampling.LANCZOS)
    icon.save(ROOT / "icons/bibi.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    build()
