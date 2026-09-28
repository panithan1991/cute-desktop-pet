"""Bake jade flame growth/flicker/decay from the existing fantasy flame material."""
import sys, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.behavior_art import EXTRA_CLIPS
from app.dragon_fire_layout import FIRE_NOZZLES
from build_behavior_atlases import frame_at


def mouth_at(image, fallback):
    pixels=np.asarray(image)
    # Mouth ROI stays below the amber eyes, so eyes cannot become emitters.
    roi=pixels[84:112,95:145]
    red=(roi[:,:,0]>75)&(roi[:,:,0]>roi[:,:,1]*1.6)&(roi[:,:,0]>roi[:,:,2]*1.25)&(roi[:,:,3]>100)
    ys,xs=np.where(red)
    if len(xs):return (95+int(xs.max()),84+round(float(ys.mean())))
    return fallback


def build():
    for platform in ('macos','windows'):
        base=ROOT/f'assets/runtime/dragon-{platform}'
        for side in ('right','left'):
            out=base/'fx'/f'aurora-flame-{side}';out.mkdir(parents=True,exist_ok=True)
            for i in range(32):
                with Image.open(ROOT/f'assets/runtime/dragon-macos/fx/fire-right/{i:02d}.png') as source:
                    pixels=np.asarray(source.convert('RGBA')).copy()
                r,g,b=[pixels[:,:,c].astype(float) for c in range(3)]
                # Bright ivory heart, emerald body, turquoise outer filaments.
                pixels[:,:,0]=np.uint8(np.clip(.16*r+.62*b,0,255))
                pixels[:,:,1]=np.uint8(np.clip(.92*r+.15*g,0,255))
                pixels[:,:,2]=np.uint8(np.clip(.76*g+.60*b,0,255))
                image=Image.fromarray(pixels);draw=ImageDraw.Draw(image)
                growth=min(1,(i+1)/8,(32-i)/8)
                nx,ny=FIRE_NOZZLES[i]
                # Continuous luminous throat joins the painted plume to the
                # tracked lip instead of leaving a transparent nozzle gap.
                draw.line((nx,ny,nx+10*growth,ny),fill=(145,255,190,240),width=3)
                for k in range(12):
                    t=(i*.06+k/12)%1
                    x=12+(195*t)*growth;y=80+math.sin(k*2.4+i*.12)*(8+24*t)*growth
                    opacity=round(210*(1-t)*growth)
                    draw.ellipse((x-1,y-1,x+1,y+1),fill=(165,255,204,opacity))
                if side=='left':image=ImageOps.mirror(image)
                if platform=='windows':image.putalpha(image.getchannel('A').point(lambda a:255 if a>=28 else 0))
                image.save(out/f'{i:02d}.png',optimize=True)
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        anchors={name:tuple(mouth_at(frame_at(atlas,POSES['dragon'].index(p)),(119,92)) for p in EXTRA_CLIPS['dragon'][name])
                 for name in ('aurora_breath','ember_bubbles','thunder_roar')}
    (ROOT/'app/dragon_signature_layout.py').write_text('"""Painted mouth anchors; mirror with the body at runtime."""\nSIGNATURE_MOUTHS = '+repr(anchors)+'\n',encoding='utf-8')
    print('Baked 32 growth/hold/decay jade flames, tracked signature mouths')


if __name__=='__main__':build()
