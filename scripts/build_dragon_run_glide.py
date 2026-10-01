"""Bake running and ground-skimming glide behavior (วิ่งแล้วร่อนใกล้พื้น) for desktop pet."""
from pathlib import Path
import sys
import math
import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from build_behavior_atlases import inbetweens, tween_path
from build_dragon_powered_flight import clean_alpha_for_windows, write_body

CELL = 160


def extract_cleaned_cells(source_path):
    """Extract and mat all 30 cells from the 6x5 sprite sheet."""
    arr = np.array(Image.open(source_path))
    h_total, w_total = arr.shape[:2]
    
    cleaned = []
    # 6 rows, 5 columns
    cell_h = h_total / 6.0
    cell_w = w_total / 5.0
    
    for r in range(6):
        for c in range(5):
            y0 = int(r * cell_h) + 2
            y1 = int((r + 1) * cell_h) - 2
            x0 = int(c * cell_w) + 2
            x1 = int((c + 1) * cell_w) - 2
            
            cell = arr[y0:y1, x0:x1].copy().astype(np.float32)
            
            # Sample edge pixels for local background color
            edge_pixels = np.vstack([
                cell[:4, :].reshape(-1, 3),
                cell[-4:, :].reshape(-1, 3),
                cell[:, :4].reshape(-1, 3),
                cell[:, -4:].reshape(-1, 3)
            ])
            bg = np.median(edge_pixels, axis=0)
            
            diff = np.linalg.norm(cell - bg, axis=2)
            r_chan, g_chan, b_chan = cell[:, :, 0], cell[:, :, 1], cell[:, :, 2]
            
            # Background is dark slate blue
            is_bg = (b_chan > r_chan + 12) & (diff < 28)
            
            alpha = np.clip((diff - 8.0) / 14.0 * 255.0, 0, 255)
            alpha[is_bg] = 0
            
            # Keep connected components with area >= 30 (body, paws, smoke/wind fx)
            core = (alpha > 40).astype(np.uint8)
            num, labels, stats, _ = cv2.connectedComponentsWithStats(core)
            keep = np.zeros_like(core)
            for i in range(1, num):
                if stats[i, cv2.CC_STAT_AREA] >= 30:
                    keep[labels == i] = 1
            keep = cv2.dilate(keep, np.ones((3, 3), np.uint8))
            alpha[keep == 0] = 0
            
            alpha = cv2.morphologyEx(alpha.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
            rgba = np.dstack([cell.clip(0, 255).astype(np.uint8), alpha])
            cleaned.append(rgba)
            
    return cleaned


def normalize_and_compose(cleaned_cells):
    """Normalize cells to 160x160 with accurate ground placement and glide height."""
    scale = 0.76
    composed = []
    
    for idx, cell in enumerate(cleaned_cells):
        r, c = divmod(idx, 5)
        h, w = cell.shape[:2]
        rw = round(w * scale)
        rh = round(h * scale)
        res = cv2.resize(cell, (rw, rh), interpolation=cv2.INTER_LANCZOS4)
        
        res_a = res[:, :, 3]
        res_ys, res_xs = np.where(res_a > 64)
        if len(res_ys):
            max_y = res_ys.max()
            mean_x = res_xs.mean()
        else:
            max_y = rh - 1
            mean_x = rw / 2.0
            
        # Ground height logic:
        # Rows 0-1 (run): paws on ground (y=144)
        # Row 2 (leap): ascending to y=138
        # Rows 3-4 (glide): skimming ground at y=138
        # Row 5 (glide to land): y=140 to 142
        if r < 2:
            target_ground = 144
        elif r == 2:
            target_ground = round(144 - (c / 4.0) * 6.0)
        elif r < 5:
            target_ground = 138
        else:
            target_ground = round(138 + (c / 4.0) * 4.0)
            
        px = round(78 - mean_x)
        py = round(target_ground - max_y)
        
        px = max(4, min(CELL - rw - 4, px))
        py = max(4, min(CELL - rh - 4, py))
        
        canvas = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        res_im = Image.fromarray(res)
        canvas.paste(res_im, (px, py), res_im)
        composed.append(canvas)
        
    return composed


def build_fluid_run_glide_sequence(composed_30):
    """
    Produce a 40-frame silky smooth run-and-glide cycle with in-betweens:
    - 0..11: Ground sprint (12 frames)
    - 12..18: Leap and wing unfurling (7 frames)
    - 19..34: Ground-skimming glide with aero trails (16 frames)
    - 35..39: Soft touchdown landing back to sprint start (5 frames)
    """
    run_keys = composed_30[0:10]
    leap_keys = composed_30[10:15]
    glide_keys = composed_30[15:30]
    
    # Smooth paths using inbetweens
    sprint_frames = tween_path(run_keys, 13)
    leap_frames = tween_path(leap_keys, 8)[1:]
    glide_frames = tween_path(glide_keys, 16)[1:]
    landing_frames = tween_path([glide_keys[-1], run_keys[0]], 6)[1:]
    
    sequence = sprint_frames + leap_frames + glide_frames + landing_frames
    assert len(sequence) == 40, f"Expected 40 frames, got {len(sequence)}"
    return sequence


def write_run_glide(frames):
    """Write extra_run_glide frames for Windows and macOS."""
    for platform in ('macos', 'windows'):
        for side in ('left', 'right'):
            out = ROOT / f'assets/runtime/dragon-{platform}/body-fx/{side}'
            out.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(frames):
                if platform == 'windows':
                    hard = clean_alpha_for_windows(frame, low_threshold=True)
                    image = ImageOps.mirror(hard) if side == 'left' else hard
                    rgb = Image.new('RGB', image.size, '#ff00ff')
                    rgb.paste(image, mask=image.getchannel('A'))
                    rgb.save(out / f'extra_run_glide_{i:02d}.ppm')
                else:
                    image = ImageOps.mirror(frame) if side == 'left' else frame
                    image.save(out / f'extra_run_glide_{i:02d}.png', optimize=True)


def build():
    source_path = ROOT / 'assets/source/dragon-run-glide.jpg'
    if not source_path.exists():
        raise FileNotFoundError(f"Missing {source_path}")
        
    cleaned = extract_cleaned_cells(source_path)
    composed = normalize_and_compose(cleaned)
    sequence = build_fluid_run_glide_sequence(composed)
    
    write_run_glide(sequence)
    
    # Save preview gif
    scratch = ROOT / 'scratch'
    scratch.mkdir(exist_ok=True)
    sequence[0].save(scratch / 'run_glide_40_fluid.gif', save_all=True,
                     append_images=sequence[1:], duration=60, loop=0)
    print(f'Baked {len(sequence)} run_glide frames for macOS and Windows successfully.')


if __name__ == '__main__':
    build()
