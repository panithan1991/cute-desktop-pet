"""Independent upward rings, flame aura and individually anchored bolt trees."""
from pathlib import Path
import sys,math
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.dragon_power_geometry import bolt_paths
from build_dragon_effects import effect_keys
from build_pet_atlases import premultiplied
from build_dragon_weather import lightning_image,platform_image


def blend(a,b,t):
    pixels=premultiplied(a)*(1-t)+premultiplied(b)*t
    alpha=pixels[:,:,3:4]
    pixels[:,:,:3]=np.divide(pixels[:,:,:3],alpha,out=np.zeros_like(pixels[:,:,:3]),where=alpha>.001)
    return Image.fromarray(np.uint8(np.clip(pixels*255,0,255)))


def atlas(frames,name,columns):
    w,h=frames[0].size
    for platform in ('macos','windows'):
        image=Image.new('RGBA',(columns*w,len(frames)//columns*h))
        for i,frame in enumerate(frames):
            if name=='sky-rings' and platform=='windows':
                frame=frame.copy();a=np.asarray(frame.getchannel('A'))
                threshold=np.tile(np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])*16+8,(h//4,w//4))
                frame.putalpha(Image.fromarray(np.uint8(a>=threshold)*255))
            else:frame=platform_image(frame,platform)
            image.alpha_composite(frame,(i%columns*w,i//columns*h))
        image.save(ROOT/f'assets/runtime/dragon-{platform}/{name}.png',optimize=True)


def build():
    keys=effect_keys()[1]
    rings=[]
    for i in range(24):
        p=i/23;at=p*5;k=min(4,int(at));t=at-k
        size=round(18+38*p)
        a,b=[key.rotate(90,expand=True).resize((size,size),Image.Resampling.LANCZOS) for key in (keys[k],keys[k+1])]
        ring=Image.new('RGBA',(96,96));ring.alpha_composite(blend(a,b,t),((96-size)//2,(96-size)//2))
        envelope=max(0,min(1,p/.15,(1-p)/.3))
        ring.putalpha(ring.getchannel('A').point(lambda v:round(v*envelope)))
        rings.append(ring)
    atlas(rings,'sky-rings',4)
    fire=Image.open(ROOT/'assets/runtime/dragon-macos/fire-right.png').convert('RGBA')
    aura=[]
    for i in range(32):
        n=8+i%16;key=fire.crop((n%4*240,n//4*160,n%4*240+240,n//4*160+160)).rotate(90,expand=True)
        image=Image.new('RGBA',(240,200))
        for x,y,w,h in ((56,52,70,145),(116,50,70,145),(65,105,110,90),(88,40,65,100)):
            image.alpha_composite(key.resize((w,h),Image.Resampling.LANCZOS),(x+round(2*math.sin(i*.7+x)),y))
        aura.append(image)
    atlas(aura,'fury-aura',4)
    tree_bounds=[]
    for index in range(16):
        paths=bolt_paths([(271,380),(289,380)],(560,480),1000+index,0)
        images={}
        for side,group,offset in (('left',paths[:13],9),('right',paths[13:],-9)):
            shifted=[[(x+offset,y) for x,y in path] for path in group]
            images[side]=lightning_image(index,shifted)
        images['up']=images['left'].rotate(-90,resample=Image.Resampling.BICUBIC,center=(280,380))
        tree_bounds.append({side:im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox() for side,im in images.items()})
        for side,im in images.items():
            for platform in ('macos','windows'):
                platform_image(im,platform).save(ROOT/f'assets/runtime/dragon-{platform}/tree-{side}-{index:02d}.png',optimize=True)
    (ROOT/'app/dragon_stunt_effect_layout.py').write_text(f'"""Bounds of individually anchored lightning trees."""\nTREE_BOUNDS={tuple(tree_bounds)!r}\n',encoding='utf-8')
    rings[10].save(ROOT/'assets/readme/dragon-sky-ring.png')
    aura[10].save(ROOT/'assets/readme/dragon-fury-aura.png')
    print('Stunt effects: 24 sky rings, 32 flame aura frames, 16 trees per direction/platform')


if __name__=='__main__':build()
