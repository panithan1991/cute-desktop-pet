"""Check that launching the downloaded Mac app paints BooBoo on screen."""

from __future__ import annotations

import sys
from PIL import Image, ImageChops


def main() -> int:
    before = Image.open(sys.argv[1]).convert("RGB")
    after = Image.open(sys.argv[2]).convert("RGB")
    if before.size != after.size:
        print(f"Screen size changed: {before.size} -> {after.size}")
        return 1

    width, height = before.size
    # BooBoo starts about one quarter across the screen and just above the Dock.
    # Keep this generous because Retina screenshots use physical pixels, while
    # Tk places windows in logical display points.
    box = (int(width * .15), int(height * .55),
           int(width * .45), int(height * .96))
    change = ImageChops.difference(before.crop(box), after.crop(box))
    changed = sum(1 for pixel in change.getdata() if max(pixel) > 35)
    print(f"Screen: {width}x{height}; pet region: {box}; changed pixels: {changed}")
    if changed < 3000:
        print("The app launched, but BooBoo was not visibly painted in the expected region.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
