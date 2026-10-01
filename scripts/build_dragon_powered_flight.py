"""Bake powered wingbeats and a correctly oriented wall grip; runtime is Tk only."""
import sys, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.dragon_animation import DRAGON_CLIPS
from app.behavior_art import EXTRA_CLIPS
from app.dragon_air_cycle import WING_FRAMES, WING_PERIOD, LIFT_POSES
from build_behavior_atlases import extract, normalize_row, tween_path, frame_at, save


def clean_alpha_for_windows(image, low_threshold=False):
    """Clean, smooth contour thresholding for Windows Tkinter -transparentcolor #ff00ff.
    Removes Bayer dithering artifacts and bright edge flickering pixels."""
    arr = np.asarray(image).copy()
    a = arr[:, :, 3]
    mask = (a >= (64 if low_threshold else 96)).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if num_labels > 1:
        largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        mask = (labels == largest).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    
    rgb = arr[:, :, :3].copy()
    filled = (mask > 0) & (a < 96)
    rgb[filled] = [35, 33, 38]

    kernel = np.ones((3, 3), np.uint8)
    boundary = (mask - cv2.erode(mask, kernel)) > 0
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    bright_boundary = boundary & (lum > 140)
    rgb[bright_boundary] = np.clip(rgb[bright_boundary].astype(float) * 0.5 + np.array([35, 33, 38]) * 0.5, 0, 255).astype(np.uint8)

    hard = Image.fromarray(np.dstack([rgb, mask * 255]), mode="RGBA")
    return hard


def write_body(name, frames):
    for platform in ('macos','windows'):
        for side in ('left','right'):
            out = ROOT/f'assets/runtime/dragon-{platform}/body-fx/{side}'
            for i, frame in enumerate(frames):
                digits=3 if name in {'air_dive_recover','air_air_brake'} else 2
                if platform=='windows':
                    hard = clean_alpha_for_windows(frame)
                    image = ImageOps.mirror(hard) if side=='left' else hard
                    rgb = Image.new('RGB',image.size,'#ff00ff')
                    rgb.paste(image,mask=image.getchannel('A'))
                    rgb.save(out/f'{name}_{i:0{digits}d}.ppm')
                else:
                    image = ImageOps.mirror(frame) if side=='left' else frame
                    image.save(out/f'{name}_{i:0{digits}d}.png',optimize=True)


def build():
    CELL = 160
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        frames = [frame_at(atlas,i) for i in range(len(POSES['dragon']))]
    reference = frames[POSES['dragon'].index(DRAGON_CLIPS['hover'][0])]

    # 1. Use authentic flight motion sheets (Images 1-3: dragon-flight-motion-1, 2, 3)
    cells1 = extract(ROOT / 'assets/source/dragon-flight-motion-1.png', 25, 5)
    norm1 = normalize_row(cells1, reference)

    cells2 = extract(ROOT / 'assets/source/dragon-flight-motion-2.png', 25, 5)
    norm2 = normalize_row(cells2, reference)

    cells3 = extract(ROOT / 'assets/source/dragon-flight-motion-3.png', 25, 5)
    norm3 = normalize_row(cells3, reference)

    all_norm = norm1 + norm2 + norm3
    canonical = all_norm[0]

    def resample_cycle(frames, count):
        n = len(frames)
        res = []
        for i in range(count):
            t = i * n / count
            idx0 = int(t) % n
            idx1 = (idx0 + 1) % n
            frac = t - int(t)
            if frac < 0.001:
                res.append(frames[idx0])
            else:
                res.append(Image.blend(frames[idx0], frames[idx1], frac))
        return res

    wing = resample_cycle(all_norm, WING_FRAMES)
    wing[0] = canonical

    write_body('wingbeat', wing)
    lift = [frames[POSES['dragon'].index(p)] for p in DRAGON_CLIPS['takeoff']]
    lift[-1] = canonical
    liftoff_frames = tween_path(lift, len(LIFT_POSES))
    liftoff_frames[-1] = canonical
    write_body('liftoff', liftoff_frames)
    for phase, frame in enumerate(wing):
        settle_clip = tween_path([frame, canonical], 6)
        settle_clip[0] = frame
        settle_clip[-1] = canonical
        write_body(f'wing_settle_{phase:02d}', settle_clip)
    for name in ('dive_recover', 'air_brake'):
        sequence = []
        for i in range(180):
            p = i / 179
            frame = wing[round((i / 30) % WING_PERIOD / WING_PERIOD * 60) % 60]
            angle = (-18 * math.sin(math.tau * p) * math.sin(math.pi * p) if name == 'dive_recover' else 12 * math.sin(math.pi * p) ** 2)
            sequence.append(frame.rotate(angle, resample=Image.Resampling.BICUBIC, center=(80, 100)))
        sequence[0] = sequence[-1] = canonical
        write_body('air_' + name, sequence)

    for clip in ('roll_enter', 'roll_exit'):
        path = [frames[POSES['dragon'].index(p)] for p in EXTRA_CLIPS['dragon'][clip]]
        if clip == 'roll_enter':
            path[0] = canonical
            seq = tween_path(path, 24)
            seq[0] = canonical
        else:
            path[-1] = canonical
            seq = tween_path(path, 24)
            seq[-1] = canonical
        write_body('air_' + clip, seq)

    landing = [frames[POSES['dragon'].index(p)] for p in DRAGON_CLIPS['landing']]
    landing[0] = canonical
    landing_seq = tween_path(landing, 24)
    landing_seq[0] = canonical
    write_body('air_land_fold', landing_seq)

    edge_cells = extract(ROOT / 'assets/source/dragon-edge-perch.png', 8, 4)
    edge = normalize_row(edge_cells[:4], reference)
    grip, opened = edge[1], edge[2]
    wall = (tween_path([canonical, edge[0], grip], 13)
            + tween_path([grip, opened], 9)[1:] + [opened] * 10
            + tween_path([opened, grip], 10)[1:])
    wall[0] = canonical
    for pose, frame in zip(EXTRA_CLIPS['dragon']['wall_perch'], wall):
        frames[POSES['dragon'].index(pose)] = frame
    top = [frames[POSES['dragon'].index(p)] for p in EXTRA_CLIPS['dragon']['top_perch']]
    top[:13] = tween_path([canonical, top[6], top[12]], 13)
    top[0] = canonical
    for pose, frame in zip(EXTRA_CLIPS['dragon']['top_perch'], top):
        frames[POSES['dragon'].index(pose)] = frame

    for platform in ('macos', 'windows'):
        for side in ('left', 'right'):
            out = ROOT / f'assets/runtime/dragon-{platform}/body-fx/{side}'
            for name, seq in (('extra_wall_perch', wall), ('extra_top_perch', top)):
                for i, frame in enumerate(seq):
                    if platform == 'windows':
                        hard = frame.copy()
                        hard.putalpha(frame.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
                        image = ImageOps.mirror(hard) if side == 'left' else hard
                        rgb = Image.new('RGB', image.size, '#ff00ff')
                        rgb.paste(image, mask=image.getchannel('A'))
                        rgb.save(out / f'{name}_{i:02d}.ppm')
                    else:
                        image = ImageOps.mirror(frame) if side == 'left' else frame
                        image.save(out / f'{name}_{i:02d}.png', optimize=True)
    if '--save-atlas' in sys.argv:
        save('dragon', frames)

    paw = grip.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()[0]
    mouths = []
    for frame in wall:
        arr = np.asarray(frame)
        roi = arr[:85, 75:135]
        alpha = roi[:, :, 3]
        ys, xs = np.where(alpha > 120)
        if len(xs):
            max_x = int(xs.max())
            snout_y = int(ys[xs >= max_x - 3].mean())
            mouths.append((int(75 + max_x - 4), int(snout_y + 3)))
        else:
            mouths.append((105, 65))
    (ROOT / 'app/dragon_wall_layout.py').write_text(
        '"""Tracked inward-facing paw and mouth anchors."""\nWALL_PAW_X=' + repr(paw) + '\nWALL_MOUTHS=' + repr(tuple(mouths)) + '\n',
        encoding='utf-8'
    )
    preview = Image.new('RGB', (1600, 960), '#dbe6ee')
    for i, frame in enumerate(wing):
        preview.paste(frame, (i % 10 * 160, i // 10 * 160), frame.getchannel('A'))
    preview.save(ROOT.parent / 'dragon-powered-wingbeat-audit.png')
    print('Baked powered-flight frames and updated hover fire with organic flame tips.')


if __name__ == '__main__':
    build()
