"""Bake 40 painted keyframes and 45 inbetweens into 85 runtime frames.

Artwork regeneration only: pip install Pillow numpy opencv-python.
The application and packaged builds do not need these libraries.
"""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CELL = 160
NAMES = {"bunny": "booboo", "mookrata": "moo-krata", "bibi": "bibi", "kitten": "kitten"}
CLIPS = (("idle", 15), ("walk", 20), ("roll", 20), ("sleep", 15), ("hop", 15))


def isolate(image):
    rgba = np.asarray(image.convert("RGBA")).copy()
    alpha = rgba[:, :, 3]
    # Generated alpha sometimes includes almost-transparent mask speckles.
    # Identify the solid subject, then retain its original soft fur perimeter.
    core = np.uint8(alpha > 200)
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(core, 8)
    if count < 2:
        raise ValueError("Missing subject")
    component = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mask = cv2.dilate(np.uint8(labels == component), np.ones((5, 5), np.uint8)) > 0
    alpha[~mask | (alpha < 48)] = 0
    # Pure mask red/yellow are not the warm pink noses or golden beaks.
    r, g, b = (rgba[:, :, i] for i in range(3))
    mask_marks = ((r > 240) & (g < 35) & (b < 35)) | ((r > 240) & (g > 235) & (b < 30))
    alpha[mask_marks] = 0
    rgba[:, :, 3] = alpha
    rgba[alpha == 0, :3] = 0
    return Image.fromarray(rgba)


def extract_subjects(source, count=25):
    image = Image.open(source).convert("RGBA")
    rgba = np.asarray(image).copy()
    # Generated sheets do not always obey an exact grid. Extract complete
    # connected subjects from the WHOLE sheet so wings/heads cannot be cut at
    # a guessed cell boundary, then order them by row and column.
    core = cv2.morphologyEx(np.uint8(rgba[:, :, 3] > 200), cv2.MORPH_OPEN,
                           np.ones((5, 5), np.uint8))
    _, labels, stats, centers = cv2.connectedComponentsWithStats(core, 8)
    ids = list(np.argsort(stats[1:, cv2.CC_STAT_AREA])[-count:] + 1)
    if len(ids) != count or min(stats[i, cv2.CC_STAT_AREA] for i in ids) < 1000:
        raise ValueError(f"Expected {count} complete subjects in {source}")
    for component in ids:
        x, y, width, height = stats[component, :4]
        if min(x, y, image.width - x - width, image.height - y - height) <= 0:
            raise ValueError(f"Subject touches source boundary in {source}; redraw it before baking")
    ids.sort(key=lambda i: centers[i, 1])
    rows = []
    for row in range(count // 5):
        cells = []
        group = sorted(ids[row * 5:row * 5 + 5], key=lambda i: centers[i, 0])
        for component in group:
            subject = rgba.copy()
            mask = cv2.dilate(np.uint8(labels == component), np.ones((7, 7), np.uint8)) > 0
            subject[~mask] = 0
            clean = isolate(Image.fromarray(subject))
            cells.append(clean.crop(clean.getchannel("A").getbbox()))
        rows.extend(cells)
    return rows


def normalize(cells):
    # One transform per sequence prevents the body changing size each frame.
    scale = min(136 / max(c.width for c in cells), 136 / max(c.height for c in cells))
    result = []
    for cell in cells:
        size = (round(cell.width * scale), round(cell.height * scale))
        cropped = cell.resize(size, Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (CELL, CELL))
        frame.alpha_composite(cropped, ((CELL - size[0]) // 2, CELL - size[1] - 14))
        result.append(frame)
    return result


def premultiplied(image):
    value = np.asarray(image).astype(np.float32) / 255
    value[:, :, :3] *= value[:, :, 3:4]
    return value


def inbetweens(a, b, count):
    """Motion-compensated tweening without blending two faces together."""
    pa, pb = premultiplied(a), premultiplied(b)
    def gray(p):
        composited = p[:, :, :3] + (1 - p[:, :, 3:4]) * 0.75
        return cv2.cvtColor(np.uint8(np.clip(composited * 255, 0, 255)), cv2.COLOR_RGB2GRAY)
    flow = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    forward = flow.calc(gray(pa), gray(pb), None)
    backward = flow.calc(gray(pb), gray(pa), None)
    # Keep local texture warps small; large viewpoint changes should use
    # painted keyframes, not a flow field that stretches faces or tears ears.
    for field in (forward, backward):
        magnitude = np.linalg.norm(field, axis=2, keepdims=True)
        field *= np.minimum(1.0, 9.0 / np.maximum(magnitude, 0.001))
        field[:] = cv2.GaussianBlur(field, (5, 5), 1.0)
    y, x = np.mgrid[0:CELL, 0:CELL].astype(np.float32)
    frames = [a]
    for index in range(1, count):
        t = index / count
        def inverse(field, amount):
            mx, my = x.copy(), y.copy()
            for _ in range(4):
                sampled = cv2.remap(field, mx, my, cv2.INTER_LINEAR)
                mx, my = x - sampled[:, :, 0] * amount, y - sampled[:, :, 1] * amount
            return mx, my
        ax, ay = inverse(forward, t)
        bx, by = inverse(backward, 1 - t)
        wa = cv2.remap(pa, ax, ay,
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        wb = cv2.remap(pb, bx, by,
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        # One texture per tween keeps eyes, nostrils and talons singular.
        blended = wa if t <= 0.5 else wb
        alpha = blended[:, :, 3:4]
        blended[:, :, :3] = np.divide(blended[:, :, :3], alpha,
                                     out=np.zeros_like(blended[:, :, :3]), where=alpha > 0.001)
        pixels = np.uint8(np.clip(blended * 255, 0, 255))
        pixels[pixels[:, :, 3] < 10] = 0
        frames.append(Image.fromarray(pixels))
    return frames


def build(character):
    name = NAMES[character]
    painted = extract_subjects(ROOT / f"assets/source/{name}-keyframes.png")
    rows = [normalize(painted[i:i+5]) for i in range(0, 25, 5)]
    roll = normalize(extract_subjects(ROOT / f"assets/source/{name}-roll.png", 20))
    frames = []
    for row, (clip, length) in zip(rows, CLIPS):
        if clip == "roll":
            frames.extend(roll)
            continue
        count = length // 5
        for index in range(5):
            frames.extend(inbetweens(row[index], row[(index + 1) % 5], count))
    assert len(frames) == 85
    atlas = Image.new("RGBA", (CELL * 5, CELL * 17))
    mirrored = Image.new("RGBA", atlas.size)
    for index, frame in enumerate(frames):
        at = ((index % 5) * CELL, (index // 5) * CELL)
        atlas.alpha_composite(frame, at)
        mirrored.alpha_composite(ImageOps.mirror(frame), at)
    for image, suffix in ((atlas, ""), (mirrored, "-left")):
        image.save(ROOT / f"assets/{name}-motion{suffix}.png", optimize=True)
        hard = image.copy()
        hard.putalpha(image.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        hard.save(ROOT / f"assets/{name}-motion{suffix}-windows.png", optimize=True)
    frames[0].save(ROOT / f"assets/readme/{name}.png", optimize=True)
    frames[0].resize((256, 256), Image.Resampling.LANCZOS).save(
        ROOT / f"icons/{'mookrata' if character == 'mookrata' else name}.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    demo = []
    for frame in frames:
        background = Image.new("RGB", frame.size, "#e8edf2")
        background.paste(frame, mask=frame.getchannel("A"))
        demo.append(background)
    demo[0].save(ROOT / f"assets/readme/{name}.gif", save_all=True, append_images=demo[1:],
                 duration=70, loop=0, optimize=False, disposal=2)
    print(f"{character}: 85 frames, 5 clips, padded 800x2720 atlas")


if __name__ == "__main__":
    for character in NAMES:
        build(character)
