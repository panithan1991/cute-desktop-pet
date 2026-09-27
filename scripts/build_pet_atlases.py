"""Turn the supplied transparent BooBoo and Moo Krata art into Tk-ready atlases.

Build-time dependencies only: Pillow and opencv-python. No image package is
needed to run the app. The original high-resolution drawings stay in the
artist's folders; these compact atlases are the distributable source assets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps


CELL = 160
COLUMNS = 5
BOOBOO_KEYS = (
    "idle", "blink", "happy", "sleep", "hop_up", "hop_air",
    "curious", "tilt", "stretch", "sit", "side_idle", "run_a",
    "run_b", "crouch", "roll_a", "roll_b", "roll_c", "dizzy",
    "playbow", "wave", "groom", "yawn", "sniff", "alert", "loaf",
)
MOO_KEYS = (
    "idle", "happy", "playbow", "hop", "run_a", "run_b",
    "tilt", "sleep", "stand_3q", "stand_side", "paw_up",
    "tilt_left", "tilt_right", "sniff_low", "sniff_air",
    "happy_sit", "awake_rest", "curled_sleep", "stretch",
    "playbow_two", "trot_a", "trot_b", "hop_two", "land",
    "sniff_close",
)


def ordered_pngs(folder: Path) -> list[Path]:
    return sorted(
        folder.glob("*.png"),
        key=lambda path: (path.name.split(" PM-")[0], int(path.stem.rsplit("-", 1)[-1])),
    )


def clean_and_fit(image: Image.Image, *, crop_first: bool = False) -> Image.Image:
    image = image.convert("RGBA")
    pixels = np.asarray(image)
    alpha = pixels[:, :, 3]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (alpha >= 40).astype(np.uint8), connectivity=8,
    )
    if count < 2:
        raise ValueError("No visible character in sprite frame")
    main = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    # Retain anti-aliased pixels around the largest connected character and
    # remove detached noise from generated PNGs.
    keep = cv2.dilate((labels == main).astype(np.uint8),
                      np.ones((5, 5), np.uint8), iterations=1)
    cleaned = pixels.copy()
    cleaned[:, :, 3] = np.where(keep, alpha, 0)
    image = Image.fromarray(cleaned, "RGBA")
    if crop_first:
        bbox = image.getchannel("A").getbbox()
        image = image.crop(bbox)
        scale = min((CELL - 4) / image.width, (CELL - 4) / image.height)
        image = image.resize((round(image.width * scale), round(image.height * scale)),
                             Image.Resampling.LANCZOS)
        centered = Image.new("RGBA", (CELL, CELL))
        centered.alpha_composite(image, ((CELL - image.width) // 2, CELL - 2 - image.height))
        image = centered
    else:
        image = image.resize((CELL, CELL), Image.Resampling.LANCZOS)
    bbox = image.getchannel("A").point(lambda value: 255 if value > 20 else 0).getbbox()
    if bbox is None:
        raise ValueError("Character vanished after resizing")
    # Share a fixed source scale across poses. Only translate, never stretch,
    # so the animal does not grow and shrink between animation frames.
    dx = (CELL - (bbox[2] - bbox[0])) // 2 - bbox[0]
    dy = (CELL - 2) - bbox[3]
    frame = Image.new("RGBA", (CELL, CELL))
    frame.alpha_composite(image, (dx, dy))
    return frame


def component_cells(path: Path, columns: int, rows: int) -> list[Image.Image]:
    """Extract each connected animal without cutting paws at nominal grid lines."""
    sheet = Image.open(path).convert("RGBA")
    pixels = np.asarray(sheet)
    count, labels, stats, centers = cv2.connectedComponentsWithStats(
        (pixels[:, :, 3] >= 40).astype(np.uint8), connectivity=8,
    )
    components = sorted(range(1, count),
                        key=lambda index: int(stats[index, cv2.CC_STAT_AREA]),
                        reverse=True)[:columns * rows]
    if len(components) != columns * rows:
        raise ValueError(f"Expected {columns * rows} isolated poses in {path}")
    components.sort(key=lambda index: (
        min(rows - 1, int(centers[index, 1] * rows / sheet.height)),
        centers[index, 0],
    ))
    frames = []
    for index in components:
        x, y, w, h, _ = stats[index]
        x0, y0 = max(0, x - 3), max(0, y - 3)
        x1, y1 = min(sheet.width, x + w + 3), min(sheet.height, y + h + 3)
        region = pixels[y0:y1, x0:x1].copy()
        mask = cv2.dilate((labels[y0:y1, x0:x1] == index).astype(np.uint8),
                          np.ones((5, 5), np.uint8), iterations=1)
        region[:, :, 3] = np.where(mask, region[:, :, 3], 0)
        frames.append(Image.fromarray(region, "RGBA"))
    return frames


def make_atlas(frames: list[Image.Image], target: Path) -> None:
    rows = (len(frames) + COLUMNS - 1) // COLUMNS
    smooth = Image.new("RGBA", (CELL * COLUMNS, CELL * rows))
    for index, image in enumerate(frames):
        frame = clean_and_fit(image, crop_first=index >= (20 if "booboo" in target.stem else 8))
        smooth.alpha_composite(frame, ((index % COLUMNS) * CELL,
                                       (index // COLUMNS) * CELL))
    target.parent.mkdir(parents=True, exist_ok=True)
    smooth.save(target, optimize=True)
    hard = smooth.copy()
    hard.putalpha(smooth.getchannel("A").point(lambda value: 255 if value >= 128 else 0))
    hard.save(target.with_name(target.stem + "-windows.png"), optimize=True)
    for source, suffix in ((smooth, "-left"), (hard, "-left-windows")):
        mirrored = Image.new("RGBA", source.size)
        for index in range(len(frames)):
            x = (index % COLUMNS) * CELL
            y = (index // COLUMNS) * CELL
            tile = source.crop((x, y, x + CELL, y + CELL))
            mirrored.alpha_composite(ImageOps.mirror(tile), (x, y))
        mirrored.save(target.with_name(target.stem + suffix + ".png"), optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booboo", type=Path, required=True)
    parser.add_argument("--moo", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("assets"))
    args = parser.parse_args()
    for folder, original_count, extra, keys, filename in (
        (args.booboo, 20,
         component_cells(args.output / "generated" / "booboo-extra-sheet.png", 5, 1),
         BOOBOO_KEYS, "booboo-motion.png"),
        (args.moo, 8,
         component_cells(args.output / "generated" / "moo-extra-sheet.png", 4, 4)
         + [Image.open(args.output / "generated" / "moo-sniff.png")],
         MOO_KEYS, "moo-krata-motion.png"),
    ):
        files = ordered_pngs(folder)
        if len(files) != original_count or len(files) + len(extra) != len(keys):
            raise ValueError(f"Expected {original_count} original images in {folder}, found {len(files)}")
        frames = [Image.open(path) for path in files] + extra
        make_atlas(frames, args.output / filename)
        if filename == "moo-krata-motion.png":
            icon_path = args.output.parent / "icons" / "moo-krata.png"
            icon_path.parent.mkdir(parents=True, exist_ok=True)
            clean_and_fit(frames[0]).resize((256, 256), Image.Resampling.LANCZOS).save(icon_path)
        print(f"Built {filename} from {len(frames)} poses")


if __name__ == "__main__":
    main()
