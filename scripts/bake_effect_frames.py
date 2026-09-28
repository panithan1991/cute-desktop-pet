"""Small PNGs avoid Tk's slow decoding of tall transparent VFX atlases."""
from pathlib import Path
from PIL import Image,ImageOps
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
CLIPS={'cloud-flame':(240,240,48),'sky-rings':(96,96,24),
       'ember-bubble':(96,96,36),'aurora-left':(240,160,64),'aurora-right':(240,160,64),'shockwave':(240,240,32),
       'roar-cone-left':(640,360,16),'roar-cone-right':(640,360,16),
       'scale-charge':(96,96,32),
       'fury-aura':(240,200,32),
       **{f'jade-rings-{s}':(96,96,24) for s in ('left','right')},
       **{f'fire-{s}':(240,160,32) for s in ('left','right')},
       **{f'vortex-{s}':(180,200,32) for s in ('left','right')}}


def bake(names=None):
    for platform in ('macos','windows'):
        base=ROOT/f'assets/runtime/dragon-{platform}'
        for name in (names or CLIPS):
            source=base/f'{name}.png'
            if not source.exists():continue
            width,height,count=CLIPS[name]
            directory=base/'fx'/name;directory.mkdir(parents=True,exist_ok=True)
            with Image.open(source) as atlas:
                for i in range(count):
                    x,y=i%4*width,i//4*height
                    frame=atlas.crop((x,y,x+width,y+height))
                    # Keep full RGB and alpha so overlapping rings compose
                    # naturally; only one small PNG is decoded per cache miss.
                    frame.save(directory/f'{i:02d}.png',optimize=True)


def bake_body():
    from app.dragon_animation import DRAGON_CLIPS
    from app.behavior_art import EXTRA_CLIPS
    from app.pet_sprites import POSES
    from app.pet_sprites import DIRECT_DRAGON_POSES
    poses=DIRECT_DRAGON_POSES
    for platform in ('macos','windows'):
        suffix='-windows' if platform=='windows' else ''
        with Image.open(ROOT/f'assets/dragon-motion{suffix}.png') as atlas:
            for side in ('left','right'):
                directory=ROOT/f'assets/runtime/dragon-{platform}/body-fx/{side}'
                directory.mkdir(parents=True,exist_ok=True)
                for pose in poses:
                    i=POSES['dragon'].index(pose);x,y=i%5*160,i//5*160
                    frame=atlas.crop((x,y,x+160,y+160))
                    if side=='left':frame=ImageOps.mirror(frame)
                    if platform=='windows':
                        rgb=Image.new('RGB',frame.size,'#ff00ff');rgb.paste(frame,mask=frame.getchannel('A'))
                        rgb.save(directory/f'{pose}.ppm')
                    else:frame.save(directory/f'{pose}.png',optimize=True)


if __name__=='__main__':
    bake();bake_body()
