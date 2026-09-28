"""Bake optical-flow body bridges; no runtime image processing."""
import sys
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.dragon_animation import DRAGON_CLIPS
from app.dragon_flight_joins import JOIN_FRAMES
from build_behavior_atlases import frame_at,tween_path

def build():
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        hover=[frame_at(atlas,POSES['dragon'].index(p)) for p in DRAGON_CLIPS['hover']]
        landing=frame_at(atlas,POSES['dragon'].index(DRAGON_CLIPS['landing'][0]))
        landed=frame_at(atlas,POSES['dragon'].index(DRAGON_CLIPS['landing'][-1]))
        idle=frame_at(atlas,POSES['dragon'].index(DRAGON_CLIPS['idle'][0]))
    sequences={f'flight_join_{k:02d}':tween_path([frame,hover[0]],JOIN_FRAMES) for k,frame in enumerate(hover)}
    sequences['landing_join']=tween_path([hover[0],landing],JOIN_FRAMES)
    sequences['touchdown_join']=tween_path([landed,idle],JOIN_FRAMES)
    for platform in ('macos','windows'):
        for side in ('left','right'):
            out=ROOT/f'assets/runtime/dragon-{platform}/body-fx/{side}'
            for name,frames in sequences.items():
                for i,frame in enumerate(frames):
                    if side=='left':frame=ImageOps.mirror(frame)
                    if platform=='windows':
                        rgb=Image.new('RGB',frame.size,'#ff00ff')
                        alpha=frame.getchannel('A').point(lambda a:255 if a>=128 else 0)
                        rgb.paste(frame,mask=alpha);rgb.save(out/f'{name}_{i:02d}.ppm')
                    else:frame.save(out/f'{name}_{i:02d}.png',optimize=True)
    print('Baked 72 flight bridge frames, mirrored for both platforms')

if __name__=='__main__':build()
