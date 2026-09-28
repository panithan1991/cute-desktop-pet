"""Bake powered wingbeats and a correctly oriented wall grip; runtime is Tk only."""
import sys, math
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.dragon_animation import DRAGON_CLIPS
from app.behavior_art import EXTRA_CLIPS
from app.dragon_air_cycle import WING_FRAMES, LIFT_POSES
from build_behavior_atlases import extract, normalize_row, tween_path, frame_at, save


def write_body(name, frames):
    for platform in ('macos','windows'):
        for side in ('left','right'):
            out = ROOT/f'assets/runtime/dragon-{platform}/body-fx/{side}'
            for i, frame in enumerate(frames):
                digits=3 if name in {'air_dive_recover','air_air_brake'} else 2
                image = ImageOps.mirror(frame) if side=='left' else frame
                if platform=='windows':
                    rgb = Image.new('RGB',image.size,'#ff00ff')
                    rgb.paste(image,mask=image.getchannel('A').point(lambda a:255 if a>=128 else 0))
                    rgb.save(out/f'{name}_{i:0{digits}d}.ppm')
                else:image.save(out/f'{name}_{i:0{digits}d}.png',optimize=True)


def build():
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        frames = [frame_at(atlas,i) for i in range(len(POSES['dragon']))]
    reference = frames[POSES['dragon'].index(DRAGON_CLIPS['hover'][0])]
    cells = extract(ROOT/'assets/source/dragon-powered-flight.png',8,4)
    keys = normalize_row(cells[:8],reference)
    # A single tail is painted throughout; optical flow interpolates its motion.
    canonical = keys[0]
    wing = tween_path(keys+[canonical],WING_FRAMES+1)[:-1]
    write_body('wingbeat',wing)
    lift = [frames[POSES['dragon'].index(p)] for p in DRAGON_CLIPS['takeoff']]
    lift[-1] = canonical
    write_body('liftoff',tween_path(lift,len(LIFT_POSES)))
    for phase,frame in enumerate(wing):
        write_body(f'wing_settle_{phase:02d}',tween_path([frame,canonical],6))
    for name in ('dive_recover','air_brake'):
        sequence=[]
        for i in range(180):
            p=i/179
            frame=wing[round((i/30)%1.5/1.5*60)%60]
            angle=(-18*math.sin(math.tau*p)*math.sin(math.pi*p) if name=='dive_recover' else 12*math.sin(math.pi*p)**2)
            sequence.append(frame.rotate(angle,resample=Image.Resampling.BICUBIC,center=(80,100)))
        sequence[0]=sequence[-1]=canonical
        write_body('air_'+name,sequence)
    for clip in ('roll_enter','roll_exit'):
        path=[frames[POSES['dragon'].index(p)] for p in EXTRA_CLIPS['dragon'][clip]]
        if clip=='roll_enter':path[0]=canonical
        else:path[-1]=canonical
        write_body('air_'+clip,tween_path(path,24))
    landing=[frames[POSES['dragon'].index(p)] for p in DRAGON_CLIPS['landing']]
    landing[0]=canonical
    write_body('air_land_fold',tween_path(landing,24))
    edge_cells = extract(ROOT/'assets/source/dragon-edge-perch.png', 8, 4)
    edge = normalize_row(edge_cells[:4], reference)
    grip, opened = edge[1], edge[2]
    wall = (tween_path([canonical, edge[0], grip], 13)
            + tween_path([grip, opened], 9)[1:] + [opened]*10
            + tween_path([opened, grip], 10)[1:])
    for pose, frame in zip(EXTRA_CLIPS['dragon']['wall_perch'], wall):
        frames[POSES['dragon'].index(pose)] = frame
    top = [frames[POSES['dragon'].index(p)] for p in EXTRA_CLIPS['dragon']['top_perch']]
    top[:13] = tween_path([canonical, top[6], top[12]], 13)
    for pose, frame in zip(EXTRA_CLIPS['dragon']['top_perch'], top): frames[POSES['dragon'].index(pose)] = frame
    save('dragon', frames)
    write_body('extra_wall_perch', wall)
    write_body('extra_top_perch', top)
    paw = grip.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()[0]
    import numpy as np
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
    (ROOT/'app/dragon_wall_layout.py').write_text('"""Tracked inward-facing paw and mouth anchors."""\nWALL_PAW_X=' + repr(paw) + '\nWALL_MOUTHS=' + repr(tuple(mouths)) + '\n', encoding='utf-8')
    preview = Image.new('RGB',(1600,960),'#dbe6ee')
    for i,frame in enumerate(wing):preview.paste(frame,(i%10*160,i//10*160),frame.getchannel('A'))
    preview.save(ROOT.parent/'dragon-powered-wingbeat-audit.png')
    print('Baked 876 powered-flight frames and a right-facing single-tail wall grip')


if __name__=='__main__':build()
