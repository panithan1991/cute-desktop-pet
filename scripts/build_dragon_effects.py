"""Bake painted emission/drift/dissipation, keeping the dragon texture singular."""

from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.dragon_animation import DRAGON_POSES, DRAGON_CLIPS
from app.behavior_art import EXTRA_POSES, EXTRA_CLIPS
from build_behavior_atlases import frame_at, save
from build_pet_atlases import CELL, inbetweens, premultiplied


def effect_keys():
    image = Image.open(ROOT / "assets/source/dragon-effects.png").convert("RGBA")
    pixels = np.asarray(image).copy()
    _, labels, stats, centers = cv2.connectedComponentsWithStats(np.uint8(pixels[:,:,3] > 48), 8)
    bodies = list(np.argsort(stats[1:,cv2.CC_STAT_AREA])[-18:] + 1)
    bodies.sort(key=lambda i: centers[i,1])
    ordered = []
    for row in range(3):
        ordered.extend(sorted(bodies[row*6:row*6+6], key=lambda i: centers[i,0]))
    groups = {i:[i] for i in ordered}
    for c in range(1, len(stats)):
        if c not in groups and stats[c,cv2.CC_STAT_AREA] > 15:
            near = min(ordered, key=lambda i: np.linalg.norm(centers[i]-centers[c]))
            groups[near].append(c)
    cells, anchors = [], []
    for c in ordered:
        mask = cv2.dilate(np.uint8(np.isin(labels,groups[c])),np.ones((3,3),np.uint8))
        subject = pixels.copy(); subject[mask == 0] = 0
        # Determine the body anchor independently of bright attached flame/smoke.
        dark = np.uint8((subject[:,:,3] > 180) & (subject[:,:,:3].mean(axis=2) < 150))
        _, _, solid, _ = cv2.connectedComponentsWithStats(dark,8)
        body = solid[1+np.argmax(solid[1:,cv2.CC_STAT_AREA])]
        cell = Image.fromarray(subject)
        bounds = cell.getchannel("A").getbbox()
        if min(bounds[0], bounds[1], image.width-bounds[2], image.height-bounds[3]) < 2:
            raise ValueError("Effect touches source edge")
        cells.append(cell.crop(bounds))
        anchors.append((body[0]+body[2]/2-bounds[0],body[1]+body[3]-bounds[1],body[3]))
    return cells, anchors


def normalize(cells, anchors, idle):
    b = idle.getchannel("A").getbbox()
    scale = min((b[3]-b[1])/np.median([a[2] for a in anchors]),
                *[min(68/max(ax,cell.width-ax,1),132/max(ay,1))
                  for cell,(ax,ay,_) in zip(cells,anchors)])
    frames = []
    for cell,(ax,ay,_) in zip(cells,anchors):
        resized = cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
        frame = Image.new("RGBA",(CELL,CELL))
        frame.alpha_composite(resized,(round(80-ax*scale),round(b[3]-ay*scale)))
        frames.append(frame)
    return frames


def split_effect(frame, idle):
    p = np.asarray(frame).copy()
    bounds = idle.getchannel("A").getbbox()
    y,x = np.mgrid[:CELL,:CELL]
    region = (x > bounds[2]-16) & (y > bounds[1]+(bounds[3]-bounds[1])*.2) & (y < bounds[3]-10)
    rgb = p[:,:,:3].astype(float)
    bright = (rgb.mean(axis=2) > 110) | ((rgb[:,:,0] > 150) & (rgb[:,:,0] > rgb[:,:,2]*1.5))
    mask = region & bright & (p[:,:,3] > 0)
    effect = p.copy(); effect[~mask] = 0
    return premultiplied(Image.fromarray(effect)), mask


def centroid(effect):
    alpha = effect[:,:,3]
    y,x = np.mgrid[:CELL,:CELL]
    total = alpha.sum()
    return (float((x*alpha).sum()/total),float((y*alpha).sum()/total)) if total > .01 else None


def effects_between(a,b,count,idle,drifting):
    # Warp one body texture, then interpolate only the isolated effects. This
    # avoids double faces while emission alpha changes smoothly from/to zero.
    bodies = inbetweens(a,b,count)
    ea, ma = split_effect(a,idle); eb, mb = split_effect(b,idle)
    ca, cb = centroid(ea), centroid(eb)
    frames = []
    for i,body in enumerate(bodies):
        t = i/count
        wa,wb = ea,eb
        if drifting and ca and cb:
            target = (ca[0]*(1-t)+cb[0]*t,ca[1]*(1-t)+cb[1]*t)
            def shift(e,c):
                matrix = np.float32([[1,0,target[0]-c[0]],[0,1,target[1]-c[1]]])
                return cv2.warpAffine(e,matrix,(CELL,CELL),flags=cv2.INTER_LINEAR)
            wa,wb = shift(ea,ca),shift(eb,cb)
        fx = wa*(1-t)+wb*t
        pixels = np.asarray(body).copy()
        _, mask = split_effect(body,idle)
        pixels[mask | ma | mb] = 0
        base = premultiplied(Image.fromarray(pixels))
        result = fx+base*(1-fx[:,:,3:4])
        alpha = result[:,:,3:4]
        result[:,:,:3] = np.divide(result[:,:,:3],alpha,out=np.zeros_like(result[:,:,:3]),where=alpha>.001)
        frames.append(Image.fromarray(np.uint8(np.clip(result*255,0,255))))
    return frames


def build():
    poses = DRAGON_POSES+EXTRA_POSES["dragon"]
    atlas = Image.open(ROOT / "assets/dragon-motion.png").convert("RGBA")
    frames = [frame_at(atlas,i) for i in range(len(poses))]
    idle = frames[0]
    cells, anchors = effect_keys()
    painted = normalize(cells,anchors,idle)
    demos = []
    for row,clip in enumerate(("smoke","fire","hiccup")):
        names = EXTRA_CLIPS["dragon"][clip] if clip == "hiccup" else DRAGON_CLIPS[clip]
        keys = painted[row*6:row*6+6]
        keys[0] = idle; keys[-1] = idle
        sequence = []
        base, extra = divmod(len(names)-1,5)
        for i in range(5):
            sequence.extend(effects_between(keys[i],keys[i+1],base+(i<extra),idle,clip!="fire"))
        sequence[0] = idle
        sequence.append(idle)
        for name,frame in zip(names,sequence):
            frames[poses.index(name)] = frame
        demos.extend(sequence)
    save("dragon",frames)
    previews = []
    for frame in demos:
        background = Image.new("RGB",frame.size,"#e8edf2")
        background.paste(frame,mask=frame.getchannel("A")); previews.append(background)
    previews[0].save(ROOT / "assets/readme/dragon-effects.gif",save_all=True,
                     append_images=previews[1:],duration=150,loop=0,disposal=2)
    print("Dragon smoke/fire/hiccup: painted emission, drift, and alpha fade baked")


if __name__ == "__main__":
    build()
