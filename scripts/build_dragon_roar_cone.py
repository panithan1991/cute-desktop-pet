"""Painted branching cone, rooted at the mouth and tilted above the desktop."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_behavior_atlases import extract
from build_dragon_stunt_effects import blend


def build():
    cells=extract(ROOT/'assets/source/dragon-roar-lightning-cone.png',4,2)
    keys=[]
    for cell in cells:
        image=cell.resize((600,round(cell.height*220/max(c.height for c in cells))),Image.Resampling.LANCZOS)
        data=np.asarray(image).astype(float)
        signal=data[:,:12,3]*(data[:,:12,:3].sum(axis=2)/765)
        ry,rx=np.unravel_index(np.argmax(signal),signal.shape)
        data[:,:rx,3]=0
        image=Image.fromarray(np.uint8(data))
        # The inverse affine shears the growing cone upward, retaining a wide
        # fan while leaving the mouth and lower desktop clear of clipping.
        key=image.transform((640,360),Image.Transform.AFFINE,
                            (1,0,rx-8,.28,1,ry-320-.28*8),Image.Resampling.BICUBIC)
        b=key.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
        if not b or min(b[0],b[1],640-b[2],360-b[3])<4:raise ValueError(f'Clipped cone: {b}')
        keys.append(key)
    for platform in ('macos','windows'):
        for side in ('left','right'):
            name=f'roar-cone-{side}'
            base=ROOT/f'assets/runtime/dragon-{platform}'
            directory=base/'fx'/name;directory.mkdir(parents=True,exist_ok=True)
            atlas=Image.new('RGBA',(2560,1440))
            for i in range(16):
                k,t=divmod(i,4);frame=blend(keys[k],keys[(k+1)%4],t/4)
                if side=='left':frame=ImageOps.mirror(frame)
                if platform=='windows':frame.putalpha(frame.getchannel('A').point(lambda a:255 if a>=48 else 0))
                frame.save(directory/f'{i:02d}.png',optimize=True)
                down=base/'fx'/f'roar-down-{side}';down.mkdir(parents=True,exist_ok=True)
                with Image.open(directory/f'{i:02d}.png') as saved_up:
                    ImageOps.flip(saved_up).save(down/f'{i:02d}.png')
                atlas.alpha_composite(frame,(i%4*640,i//4*360))
            atlas.save(base/f'{name}.png',optimize=True)
    print('Baked 16 giant mouth-rooted branching cones, both facings and platforms')


if __name__=='__main__':build()
