"""Hollow vortex rings that grow, drift and dissolve into the gas cloud."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from build_behavior_atlases import extract
from build_dragon_cloud import tween_path
from build_dragon_stunt_effects import blend
from bake_effect_frames import bake

ROOT=Path(__file__).resolve().parents[1]


def build():
    cells=extract(ROOT/'assets/source/dragon-jade-rings.png',count=8,columns=4)
    scale=80/max(max(c.size) for c in cells)
    keys=[]
    for cell in cells:
        size=(round(cell.width*scale),round(cell.height*scale))
        frame=Image.new('RGBA',(96,96));frame.alpha_composite(cell.resize(size,Image.Resampling.LANCZOS),((96-size[0])//2,(96-size[1])//2));keys.append(frame)
    frames=tween_path(keys,24)
    for i in range(18,24):frames[i]=blend(frames[i],Image.new('RGBA',(96,96)),((i-18)/5)**1.4)
    for platform in ('macos','windows'):
        for side in ('left','right'):
            atlas=Image.new('RGBA',(384,576))
            for i,original in enumerate(frames):
                frame=ImageOps.mirror(original) if side=='left' else original.copy()
                if platform=='windows':
                    a=np.asarray(frame.getchannel('A'))
                    threshold=np.tile(np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])*16+8,(24,24))
                    frame.putalpha(Image.fromarray(np.uint8(a>=threshold)*255))
                atlas.alpha_composite(frame,(i%4*96,i//4*96))
            atlas.save(ROOT/f'assets/runtime/dragon-{platform}/jade-rings-{side}.png',optimize=True)
    bake(('jade-rings-left','jade-rings-right'))
    print('Jade vortex rings: 24 growing, hollow, mirrored frames')


if __name__=='__main__':build()
