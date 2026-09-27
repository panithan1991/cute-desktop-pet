"""Build the README animation previews from the same 25-pose desktop atlases."""

from pathlib import Path
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CELL = 160


def save_preview(atlas_name: str, output_name: str,
                 poses: list[int], durations: list[int]) -> None:
    atlas = Image.open(ASSETS / atlas_name).convert("RGBA")
    frames = []
    for pose in poses:
        box = ((pose % 5) * CELL, (pose // 5) * CELL,
               (pose % 5 + 1) * CELL, (pose // 5 + 1) * CELL)
        sprite = atlas.crop(box)
        frame = Image.new("RGB", (180, 180), "#edf3f8")
        draw = ImageDraw.Draw(frame)
        draw.ellipse((30, 161, 150, 172), fill="#d6dde5")
        frame.paste(sprite, (10, 4), sprite)
        frames.append(frame)
    frames[0].save(ASSETS / output_name, save_all=True,
                   append_images=frames[1:], duration=durations,
                   loop=0, optimize=True)


def main() -> None:
    save_preview("booboo-motion.png", "booboo-animation.gif",
                 [0, 1, 0, 7, 20, 24, 3, 24, 8, 9, 0],
                 [650, 180, 400, 800, 750, 1100, 1100, 800, 700, 600, 500])
    save_preview("booboo-motion.png", "booboo-hop.gif",
                 [10, 11, 12, 11, 4, 5, 13, 10],
                 [300, 140, 140, 120, 140, 180, 200, 350])
    save_preview("moo-krata-motion.png", "mookrata-animation.gif",
                 [0, 1, 10, 11, 16, 17, 18, 7, 0],
                 [650, 450, 650, 750, 800, 1000, 750, 1000, 650])
    save_preview("moo-krata-motion.png", "mookrata-run.gif",
                 [8, 20, 4, 21, 5, 9, 20, 4, 21, 5],
                 [320, 120, 110, 120, 110, 200, 120, 110, 120, 110])


if __name__ == "__main__":
    main()
