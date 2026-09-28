"""Append painted gestures and transitions; preserve the existing base frames.

Artwork baking only: Pillow, numpy, OpenCV. Runtime still uses only Tk.
"""

from pathlib import Path
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.behavior_art import EXTRA_CLIPS
from app.animation_clips import ALL_POSES
from app.dragon_animation import DRAGON_POSES, DRAGON_CLIPS
from build_pet_atlases import CELL, inbetweens, isolate

NAMES = {"bunny": "booboo", "mookrata": "moo-krata", "kitten": "kitten", "bibi": "bibi", "dragon": "dragon"}


def extract(source, count=25, columns=5):
    sheet = Image.open(source).convert("RGBA")
    rgba = np.asarray(sheet).copy()
    core = cv2.morphologyEx(np.uint8(rgba[:, :, 3] > 180), cv2.MORPH_OPEN,
                           np.ones((5, 5), np.uint8))
    _, labels, stats, centers = cv2.connectedComponentsWithStats(core, 8)
    bodies = list(np.argsort(stats[1:, cv2.CC_STAT_AREA])[-count:] + 1)
    if len(bodies) != count or min(stats[i, cv2.CC_STAT_AREA] for i in bodies) < 1000:
        raise ValueError(f"Expected {count} complete subjects: {source}")
    bodies.sort(key=lambda i: centers[i, 1])
    ordered = []
    for row in range(count // columns):
        ordered.extend(sorted(bodies[row*columns:(row+1)*columns], key=lambda i: centers[i, 0]))
    result = []
    for body in ordered:
        mask = cv2.dilate(np.uint8(labels == body), np.ones((7, 7), np.uint8))
        subject = rgba.copy()
        subject[mask == 0] = 0
        clean = isolate(Image.fromarray(subject))
        bounds = clean.getchannel("A").getbbox()
        if not bounds or min(bounds[0], bounds[1], sheet.width-bounds[2], sheet.height-bounds[3]) < 2:
            raise ValueError(f"Clipped source body: {source}, {body}")
        result.append(clean.crop(bounds))
    return result


def frame_at(atlas, index):
    return atlas.crop((index % 5*CELL, index//5*CELL,
                       (index%5+1)*CELL, (index//5+1)*CELL))


def tween_path(keys, count):
    frames = []
    base, extra = divmod(count-1, len(keys)-1)
    for i in range(len(keys)-1):
        frames.extend(inbetweens(keys[i], keys[i+1], base+(i < extra)))
    return frames + [keys[-1]]


def normalize_row(cells, reference, reference_index=0):
    bounds = reference.getchannel("A").getbbox()
    scale = min((bounds[3]-bounds[1])/cells[reference_index].height,
                132/max(c.height for c in cells), 136/max(c.width for c in cells))
    anchor_x = (bounds[0]+bounds[2])/2
    anchor_y = bounds[3]
    frames = []
    for cell in cells:
        size = (round(cell.width*scale), round(cell.height*scale))
        resized = cell.resize(size, Image.Resampling.LANCZOS)
        image = Image.new("RGBA", (CELL, CELL))
        image.alpha_composite(resized, (round(anchor_x-size[0]/2), round(anchor_y-size[1])))
        frames.append(image)
    return frames


def save(character, frames):
    name = NAMES[character]
    assert len(frames) % 5 == 0
    atlas = Image.new("RGBA", (CELL*5, CELL*(len(frames)//5)))
    left = Image.new("RGBA", atlas.size)
    for i, frame in enumerate(frames):
        b = frame.getchannel("A").point(lambda a: 255 if a > 32 else 0).getbbox()
        if not b or min(b[0], b[1], CELL-b[2], CELL-b[3]) < 6:
            raise ValueError(f"Clipped baked frame {character}:{i}: {b}")
        at = (i%5*CELL, i//5*CELL)
        atlas.alpha_composite(frame, at)
        left.alpha_composite(ImageOps.mirror(frame), at)
    for image, suffix in ((atlas, ""), (left, "-left")):
        image.save(ROOT / f"assets/{name}-motion{suffix}.png", optimize=True)
        hard = image.copy()
        hard.putalpha(image.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        hard.save(ROOT / f"assets/{name}-motion{suffix}-windows.png", optimize=True)
        if character == "dragon":
            from app.pet_sprites import PAGE_FRAMES
            for platform,source in (("macos",image),("windows",hard)):
                directory = ROOT / f"assets/runtime/dragon-{platform}"
                directory.mkdir(parents=True,exist_ok=True)
                for start in range(0,len(frames),PAGE_FRAMES):
                    y = start//5*CELL
                    end = min(source.height,y+PAGE_FRAMES//5*CELL)
                    side = "left" if suffix else "right"
                    source.crop((0,y,CELL*5,end)).save(directory/f"{side}-{start//PAGE_FRAMES:02d}.png",optimize=True)


def build(character):
    name = NAMES[character]
    atlas = Image.open(ROOT / f"assets/{name}-motion.png").convert("RGBA")
    base = DRAGON_POSES if character == "dragon" else ALL_POSES
    frames = [frame_at(atlas, i) for i in range(len(base))]
    idle = frames[0]
    sleep = frames[base.index(DRAGON_CLIPS["sleep"][-1])] if character == "dragon" else frames[69]
    travel = frames[base.index(DRAGON_CLIPS["takeoff"][0])] if character == "dragon" else frames[70 if character == "bibi" else 15]
    painted = extract(ROOT / f"assets/source/{name}-behaviors.png")
    actions = extract(ROOT / "assets/source/dragon-actions.png", count=20) if character == "dragon" else []
    previews = []
    for row, (clip, poses) in enumerate(EXTRA_CLIPS[character].items()):
        ref = sleep if clip in {"hug_tail", "wing_blanket"} else idle
        if clip == 'ignition_reaction':
            keys=normalize_row(extract(ROOT/'assets/source/dragon-ignition-reaction.png',count=10),idle)
            keys[0]=keys[-1]=idle
            frames.extend(tween_path(keys,len(poses)));continue
        if clip in {"ground_ready", "ground_walk", "run"}:
            from build_dragon_gaits import ground_sequences
            if clip == "ground_ready":
                ground = ground_sequences(idle)
            frames.extend(ground[clip]);continue
        if clip == "fury":
            from build_dragon_stunts import fury_sequence
            frames.extend(fury_sequence(idle));continue
        if clip == "belly_smoke":
            from build_dragon_stunts import belly_sequence
            frames.extend(belly_sequence(idle));continue
        if clip.startswith("roll_"):
            from build_dragon_stunts import roll_sequences
            if clip=="roll_enter":
                rolls=roll_sequences(frames[base.index(DRAGON_CLIPS["hover"][0])])
            frames.extend(rolls[clip]);continue
        if clip == "wing_gust":
            keys = normalize_row(extract(ROOT/"assets/source/dragon-wing-gust.png",count=5),idle)
            keys[0] = keys[-1] = idle
            frames.extend(tween_path(keys,len(poses)))
            continue
        cells = (actions[(row-4)*5:(row-3)*5] if row >= 5 else painted[row*5:(row+1)*5])
        keys = normalize_row(cells, ref, 4 if row == 0 else 0)
        keys[0] = sleep if row == 0 else ref
        keys[-1] = travel if clip == "travel_ready" else ref
        sequence = tween_path(keys, len(poses))
        if clip == "storm_hover":
            # Four slow wingbeats; VFX can flash much faster than the body.
            aerial = []
            for f in normalize_row(cells, ref):
                raised = Image.new("RGBA", (CELL, CELL)); raised.alpha_composite(f, (0,-10)); aerial.append(raised)
            sequence = (inbetweens(idle,aerial[0],16) + tween_path(aerial,27)*4
                        + inbetweens(aerial[-1],idle,15) + [idle])
            # Subpixel body breathing/follow-through avoids a mechanically
            # identical texture loop while the wingbeat retains its anatomy.
            for i in range(16,124):
                bob = 1.3*math.sin(i*.19)+.6*math.sin(i*.073)
                sequence[i] = sequence[i].transform((CELL,CELL), Image.Transform.AFFINE,
                                                     (1,0,0,0,1,-bob), Image.Resampling.BICUBIC)
            assert len(sequence) == len(poses)
        frames.extend(sequence)
        if row < 4:
            previews.extend(sequence)
    save(character, frames)
    demo = []
    for frame in previews:
        image = Image.new("RGB", frame.size, "#e8edf2")
        image.paste(frame, mask=frame.getchannel("A"))
        demo.append(image)
    demo[0].save(ROOT / f"assets/readme/{name}-behaviors.gif", save_all=True,
                 append_images=demo[1:], duration=180, loop=0, disposal=2)
    if character == "dragon":
        extra_start = len(base)
        for clip in ("threat", "roar", "storm_hover"):
            first = sum(len(p) for n, p in EXTRA_CLIPS[character].items()
                        if list(EXTRA_CLIPS[character]).index(n) < list(EXTRA_CLIPS[character]).index(clip))
            sequence = frames[extra_start+first:extra_start+first+len(EXTRA_CLIPS[character][clip])]
            thumbnails = []
            for f in sequence:
                bg = Image.new("RGB", f.size, "#e8edf2"); bg.paste(f, mask=f.getchannel("A")); thumbnails.append(bg)
            thumbnails[0].save(ROOT / f"assets/readme/dragon-{clip}.gif", save_all=True,
                               append_images=thumbnails[1:], duration=150, loop=0, disposal=2)
    print(f"{character}: {len(frames)} frames; 3 new gestures and 2 connecting clips")


if __name__ == "__main__":
    for character in NAMES:
        build(character)
