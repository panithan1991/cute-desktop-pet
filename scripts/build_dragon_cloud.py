"""Bake jade cloud accumulation and turquoise ignition, with intact alpha."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_pet_atlases import isolate
from build_behavior_atlases import extract
from build_dragon_stunt_effects import blend


def tween_path(keys,count):
    # Effects have no anatomy to protect: premultiplied continuous mixing
    # keeps translucent gas wisps intact across ignition, without a texture cut.
    frames=[]
    for i in range(count):
        t=i/(count-1)*(len(keys)-1); a=min(len(keys)-2,int(t))
        frames.append(blend(keys[a],keys[a+1],t-a))
    frames[0]=keys[0];frames[-1]=keys[-1]
    return frames


def build():
    # Generated keyframes aren't perfectly grid-aligned: extract entire
    # connected clouds rather than cutting a wisp at a guessed cell border.
    cells=extract(ROOT/'assets/source/dragon-cloud-flame-v2.png',count=12,columns=4)
    flames=extract(ROOT/'assets/source/dragon-cloud-combustion.png',count=4,columns=2)
    scale=208/max(max(im.size) for im in cells)
    keys=[]
    for cell in cells:
        resized=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
        key=Image.new('RGBA',(240,240)); key.alpha_composite(resized,((240-resized.width)//2,(240-resized.height)//2));keys.append(key)
    pure=[]
    flame_scale=208/max(max(im.size) for im in flames)
    for cell in flames:
        resized=cell.resize((round(cell.width*flame_scale),round(cell.height*flame_scale)),Image.Resampling.LANCZOS)
        key=Image.new('RGBA',(240,240));key.alpha_composite(resized,((240-resized.width)//2,(240-resized.height)//2));pure.append(key)
    # Hold the established cloud with subtle internal motion; ignition is
    # faster than emission. Shared endpoints prevent any phase discontinuity.
    held=[]
    for i in range(8):
        im=keys[3].transform((240,240),Image.Transform.AFFINE,(1,0,.65*np.sin(i*np.pi/7),0,1,.5*np.sin(i*np.pi/7)),Image.Resampling.BICUBIC)
        held.append(im)
    held[0]=held[-1]=keys[3]
    frames=tween_path(keys[:4],12)+held+tween_path([keys[3],*keys[4:8],pure[0]],12)+tween_path(pure[:3],8)+tween_path(pure[2:],8)
    frames[0]=blend(Image.new('RGBA',(240,240)),frames[0],.15)
    for i in range(41,48):
        frames[i]=blend(frames[i],Image.new('RGBA',(240,240)),((i-40)/7)**1.5)
    assert len(frames)==48
    for platform in ('macos','windows'):
        atlas=Image.new('RGBA',(960,2880))
        for i,frame in enumerate(frames):
            if platform=='windows':
                frame=frame.copy();alpha=np.asarray(frame.getchannel('A'))
                threshold=np.tile(np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])*16+8,(60,60))
                frame.putalpha(Image.fromarray(np.uint8(alpha>=threshold)*255))
            atlas.alpha_composite(frame,(i%4*240,i//4*240))
        atlas.save(ROOT/f'assets/runtime/dragon-{platform}/cloud-flame.png',optimize=True)
    preview=Image.new('RGB',(960,275),'#14222b');draw=ImageDraw.Draw(preview)
    for column,(i,label) in enumerate(((5,'Slow emission'),(18,'Cloud gathers'),(29,'Turquoise ignition'),(36,'Blue-green flame'))):
        preview.paste(frames[i],(column*240,20),frames[i].getchannel('A'));draw.text((column*240+12,8),label,fill='white')
    preview.save(ROOT/'assets/readme/dragon-cloud-flame.png')
    print('Jade cloud: 48 padded frames, both platforms, dithered Windows alpha')


if __name__=='__main__':build()
