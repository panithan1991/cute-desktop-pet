"""Attach a detailed painted electrical corona to a stable horn-tip root."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_behavior_atlases import extract
from build_dragon_stunt_effects import blend


def build():
    cells=extract(ROOT/'assets/source/dragon-static-charge.png',4,2)
    scale=min(76/max(c.width for c in cells),70/max(c.height for c in cells))
    keys=[]
    for cell in cells:
        image=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
        data=np.asarray(image).astype(float)
        signal=data[:,:,3]*data[:,:,:3].sum(axis=2)
        signal[:int(image.height*.78)]=0
        ry,rx=np.unravel_index(np.argmax(signal),signal.shape)
        key=Image.new('RGBA',(96,96));key.alpha_composite(image,(48-rx,80-ry))
        keys.append(key)
    for platform in ('macos','windows'):
        base=ROOT/f'assets/runtime/dragon-{platform}'
        directory=base/'fx/scale-charge';directory.mkdir(parents=True,exist_ok=True)
        atlas=Image.new('RGBA',(384,768))
        for i in range(32):
            k,t=divmod(i,8);image=blend(keys[k],keys[(k+1)%4],t/8)
            if platform=='windows':image.putalpha(image.getchannel('A').point(lambda a:255 if a>=48 else 0))
            image.save(directory/f'{i:02d}.png',optimize=True)
            for part,angle in (('rear',32),('front',18)):
                rooted=Image.new('RGBA',(128,128));rooted.alpha_composite(image,(16,28))
                rooted=rooted.rotate(angle,resample=Image.Resampling.BICUBIC,center=(64,108))
                for side in ('right','left'):
                    target=base/'fx'/f'charge-{part}-{side}'
                    target.mkdir(parents=True,exist_ok=True)
                    variant=ImageOps.mirror(rooted) if side=='left' else rooted
                    if platform=='windows':variant.putalpha(variant.getchannel('A').point(lambda a:255 if a>=48 else 0))
                    variant.save(target/f'{i:02d}.png',optimize=True)
            atlas.alpha_composite(image,(i%4*96,i//4*96))
        atlas.save(base/'scale-charge.png',optimize=True)
    print('Baked 32 realistic horn corona frames')


if __name__=='__main__':build()
