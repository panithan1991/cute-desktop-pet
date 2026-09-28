"""Bake independent VFX layers over intact dragon poses; never erase body pixels."""

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.dragon_animation import DRAGON_POSES, DRAGON_CLIPS
from app.behavior_art import EXTRA_POSES, EXTRA_CLIPS
from app.dragon_lightning import STORM_FRAMES, flash_at
from build_behavior_atlases import extract, frame_at, normalize_row, tween_path, save
from build_pet_atlases import CELL, premultiplied


def effect_keys():
    """Only effects are present in this source; the face never enters a mask."""
    image = Image.open(ROOT / "assets/source/dragon-vfx.png").convert("RGBA")
    result = []
    for row in range(3):
        cells = []
        for col in range(6):
            box = (round(col*image.width/6), round(row*image.height/3),
                   round((col+1)*image.width/6), round((row+1)*image.height/3))
            cell = image.crop(box)
            # Discard sparse colored alpha dust from the generation mask.
            a = np.asarray(cell).copy()
            bad = (a[:,:,0] > a[:,:,1]*1.8) & (a[:,:,1] < 50) & (a[:,:,2] < 60)
            a[bad] = 0
            cell = Image.fromarray(a)
            b = cell.getchannel("A").point(lambda x: 255 if x > 24 else 0).getbbox()
            if not b:
                raise ValueError(f"Missing effect {row}:{col}")
            cells.append(cell.crop(b))
        result.append(cells)
    return result


def effect_layer(keys, progress, clip, mouth):
    # Interpolate premultiplied alpha; changing plume size and drift are
    # independent of the body. No brightness-based body segmentation.
    emission = max(0, min(1, (progress-.12)/.75))
    pos = emission*5
    i = min(4, int(pos)); t = pos-i
    envelope = min(1, max(0, (progress-.08)/.16), max(0, (1-progress)/.22))
    if envelope <= 0:
        return Image.new("RGBA", (CELL, CELL))
    if clip == "fire":
        width = 8+37*math.sin(math.pi*emission)**.7
        drift = 0
    else:
        width = (10+30*math.sin(math.pi*emission)**.5) if clip == "smoke" else (7+18*math.sin(math.pi*emission)**.6)
        drift = 12*emission
    height = min(32 if clip == "smoke" else 26, width*.75)
    left = min(150-round(width), round(mouth[0]+drift))
    top = round(mouth[1]-height/2-8*emission*(clip != "fire"))
    layers = []
    for key in (keys[i], keys[i+1]):
        resized = key.resize((round(width), round(height)), Image.Resampling.LANCZOS)
        layer = Image.new("RGBA", (CELL, CELL)); layer.alpha_composite(resized, (left, top))
        layers.append(premultiplied(layer))
    pixels = (layers[0]*(1-t)+layers[1]*t)*envelope
    alpha = pixels[:,:,3:4]
    pixels[:,:,:3] = np.divide(pixels[:,:,:3], alpha, out=np.zeros_like(pixels[:,:,:3]), where=alpha>.001)
    return Image.fromarray(np.uint8(np.clip(pixels*255, 0, 255)))


def lightning_layer(body, progress):
    """Short bright strikes with stable branches during each exposure."""
    layer = Image.new("RGBA", (CELL, CELL))
    strike, strength, growth = flash_at(round(progress*(STORM_FRAMES-1)))
    if strength == 0:
        return layer
    rng = random.Random(903+strike*53)
    head = body.getchannel("A").crop((68,5,102,90)).point(lambda a: 255 if a > 80 else 0).getbbox()
    y = head[1]+11
    paths = []
    for side in (-1, 1):
        origin = (85+side*9, y)
        path = [origin]
        for j in range(1, 7):
            path.append((origin[0]+side*j*7+rng.uniform(-4,4),
                         max(9, y-j*5+rng.uniform(-4,4))))
        path = path[:max(3, round(len(path)*growth))]
        paths.append(path)
        paths.append([path[3], (path[3][0]+side*5, max(9,path[3][1]-9)),
                      (path[3][0]+side*12, max(8,path[3][1]-13))])
    draw = ImageDraw.Draw(layer)
    for path in paths:
        draw.line(path, fill=(90,165,255,round(145*strength)), width=5)
    layer = layer.filter(ImageFilter.GaussianBlur(1.4))
    draw = ImageDraw.Draw(layer)
    for path in paths:
        draw.line(path, fill=(155,205,255,round(240*strength)), width=2)
        draw.line(path, fill=(255,252,245,round(255*strength)), width=1)
        x,y0 = path[0]
        draw.ellipse((x-2,y0-2,x+2,y0+2), fill=(205,230,255,round(220*strength)))
    return layer


def preview(frames, name, duration=140):
    demo = []
    for f in frames:
        bg = Image.new("RGB", f.size, "#293642"); bg.paste(f, mask=f.getchannel("A")); demo.append(bg)
    demo[0].save(ROOT / f"assets/readme/{name}.gif", save_all=True, append_images=demo[1:],
                 duration=duration, loop=0, disposal=2)


def build():
    poses = DRAGON_POSES+EXTRA_POSES["dragon"]
    atlas = Image.open(ROOT / "assets/dragon-motion.png").convert("RGBA")
    frames = [frame_at(atlas, i) for i in range(len(poses))]
    idle = frames[0]
    body_keys = normalize_row(extract(ROOT / "assets/source/dragon-actions.png", count=20)[:5], idle)
    body_keys[0] = body_keys[-1] = idle
    effects = effect_keys()
    clean_bodies, demos = [], []
    for clip, row in (("smoke",1), ("fire",0), ("hiccup",2)):
        names = EXTRA_CLIPS["dragon"][clip] if clip == "hiccup" else DRAGON_CLIPS[clip]
        bodies = tween_path(body_keys, len(names))
        sequence = []
        for j, (name, body) in enumerate(zip(names, bodies)):
            progress = j/(len(names)-1)
            # Make room for the complete plume without shrinking the face.
            shift = round(16*min(1, progress/.2, (1-progress)/.2))
            clean = Image.new("RGBA", (CELL,CELL)); clean.alpha_composite(body, (-shift,0))
            bounds = clean.getchannel("A").point(lambda a: 255 if a > 80 else 0).getbbox()
            mouth = (bounds[2]-8, bounds[1]+round((bounds[3]-bounds[1])*.5))
            fx = effect_layer(effects[row], progress, clip, mouth)
            result = Image.alpha_composite(clean, fx)
            frames[poses.index(name)] = result
            clean_bodies.append(clean); sequence.append(result)
        demos.extend(sequence)
    # Store the untouched body reference so regression tests detect any future
    # erased face/scale pixel, rather than merely checking the canvas bounds.
    reference = Image.new("RGBA", (CELL*5, CELL*23))
    for i, f in enumerate(clean_bodies):
        reference.alpha_composite(f,(i%5*CELL,i//5*CELL))
    reference.save(ROOT / "assets/source/dragon-effect-bodies.png", optimize=True)
    storm_names = EXTRA_CLIPS["dragon"]["storm_hover"]
    storm = []
    lightning = Image.new("RGBA", (CELL*5,CELL*(STORM_FRAMES//5)))
    for i, name in enumerate(storm_names):
        body = frames[poses.index(name)]
        fx = lightning_layer(body,i/(len(storm_names)-1))
        lightning.alpha_composite(fx,(i%5*CELL,i//5*CELL))
        result = Image.alpha_composite(body,fx)
        frames[poses.index(name)] = result; storm.append(result)
    save("dragon", frames)
    lightning.save(ROOT / "assets/source/dragon-lightning-layers.png", optimize=True)
    preview(demos, "dragon-effects")
    preview(storm, "dragon-storm_hover", duration=60)
    print(f"Dragon: {len(frames)} frames, intact face layers, fire/smoke and horn lightning")


if __name__ == "__main__":
    build()
