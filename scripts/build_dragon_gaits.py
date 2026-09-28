"""Bake distance-driven ground gaits with shared contact and sitting joins."""
from pathlib import Path
from PIL import Image, ImageDraw
from build_behavior_atlases import extract, normalize_row, tween_path

ROOT = Path(__file__).resolve().parents[1]


def ground_sequences(idle):
    cells = extract(ROOT / 'assets/source/dragon-ground-gaits.png', count=15)
    keys = normalize_row(cells, idle)
    keys[0] = idle
    ready = tween_path(keys[:5], 25)
    ready[0] = idle
    contact = ready[-1]
    result = {'ground_ready': ready}
    for name, row in (('ground_walk', 1), ('run', 2)):
        path = keys[row*5:(row+1)*5]
        path[0] = path[-1] = contact
        result[name] = tween_path(path, 40)
        result[name][0] = result[name][-1] = contact
    preview = Image.new('RGB', (800, 360), '#e8edf2')
    draw = ImageDraw.Draw(preview)
    for row, name in enumerate(('ground_walk', 'run')):
        draw.text((12,row*180+8), 'Sleepy walk' if row==0 else 'Playful run', fill='#263449')
        for column, index in enumerate((0, 9, 19, 29, 39)):
            frame = result[name][index]
            preview.paste(frame, (column*160,row*180+20), frame.getchannel('A'))
    preview.save(ROOT / 'assets/readme/dragon-gaits.png')
    return result
