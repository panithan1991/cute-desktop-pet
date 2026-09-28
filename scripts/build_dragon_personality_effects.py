"""Pre-render continuous elemental VFX; no image processing runs in the app."""
from pathlib import Path
import sys, math
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

SIZES={'ember-bubble':(96,96,36),'aurora-right':(240,160,64),'aurora-left':(240,160,64),
       'shockwave':(240,240,32)}


@lru_cache(maxsize=1)
def painted_effects():
    from build_behavior_atlases import extract
    from build_dragon_stunt_effects import blend
    cells=extract(ROOT/'assets/source/dragon-signature-effects.png',12,4)
    result={}
    for row,name in enumerate(('ember-bubble','aurora-right')):
        w,h,count=SIZES[name];group=cells[row*4:row*4+4]
        scale=min((w-24)/max(c.width for c in group),(h-18)/max(c.height for c in group))
        keys=[]
        for cell in group:
            image=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
            key=Image.new('RGBA',(w,h))
            key.alpha_composite(image,(8 if name=='aurora-right' else (w-image.width)//2,(h-image.height)//2))
            keys.append(key)
        if name=='aurora-right':
            # One painted plume, anchored at its bright narrow nozzle. Moving
            # flow stays downstream; the source and first pixels never drift.
            import cv2
            original=keys[0]
            data=np.asarray(original).astype(np.float32)/255
            rx=int(np.flatnonzero(data[:,:,3].max(axis=0)>.3)[0])
            ry=int(np.argmax(data[:,rx,3]*data[:,rx,:3].sum(axis=1)))
            anchored=original.transform((w,h),Image.Transform.AFFINE,
                (1,0,rx-8,0,1,ry-80),Image.Resampling.BICUBIC)
            rgba=np.asarray(anchored).astype(np.float32)/255
            rgba[:,:,:3]*=rgba[:,:,3:4]
            yy,xx=np.mgrid[:h,:w].astype(np.float32)
            influence=np.clip((xx-24)/80,0,1)
            frames=[]
            for i in range(count):
                phase=i/(count-1)*math.tau
                dx=1.3*np.sin(yy*.08-phase)*influence
                dy=(2.2*np.sin(xx*.045-phase)+1.1*np.sin(xx*.09-phase*2))*influence
                flowed=cv2.remap(rgba,xx-dx,yy-dy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
                flowed=np.clip(flowed,0,1)
                flowed[:,:,:3]/=np.maximum(flowed[:,:,3:4],.0001)
                frames.append(Image.fromarray(np.uint8(np.clip(flowed,0,1)*255)))
            frames[-1]=frames[0].copy()
            result[name]=frames
            continue
        frames=[]
        for i in range(count):
            t=i/(count-1)*4;k=min(3,int(t));amount=t-k
            image=blend(keys[k],keys[(k+1)%4],amount)
            if name=='ember-bubble':
                life=i/(count-1)
                yy,xx=np.mgrid[:h,:w];r=np.sqrt((xx-w/2)**2+(yy-h/2)**2)
                # A translucent membrane lets the desktop show through, while
                # the painted fiery surface remains bright around the rim.
                alpha=np.asarray(image.getchannel('A')).astype(float)
                alpha*=np.clip(.25+(r/(min(w,h)*.35))**2,.25,1)
                image.putalpha(Image.fromarray(np.uint8(alpha)))
                growth=.18+.82*min(1,life/.80)
                size=(max(1,round(w*growth)),max(1,round(h*growth)))
                small=image.resize(size,Image.Resampling.LANCZOS)
                expanded=Image.new('RGBA',(w,h));expanded.alpha_composite(small,((w-size[0])//2,(h-size[1])//2))
                if life>.8:
                    burst=(life-.8)/.2
                    # Irregular turbulent holes replace rigid pie slices.
                    # Surviving flame filaments spread gently and dissolve.
                    scale=1/(1+.10*burst)
                    expanded=expanded.transform((w,h),Image.Transform.AFFINE,
                                (scale,0,w/2*(1-scale),0,scale,h/2*(1-scale)),Image.Resampling.BICUBIC)
                    turbulence=(.52+.24*np.sin(xx*.21+yy*.17+burst*2)+.16*np.sin(xx*.43-yy*.31)+.08*np.sin(xx*.09-yy*.11))
                    dissolve=np.clip((turbulence-(.12+.8*burst))/.22,0,1)*(1-burst)**.6
                    mask=np.asarray(expanded.getchannel('A')).astype(float)*dissolve
                    expanded.putalpha(Image.fromarray(np.uint8(mask)))
                fade=min(1,life/.08)
                expanded.putalpha(expanded.getchannel('A').point(lambda a:round(a*fade)))
                image=expanded
            frames.append(image)
        frames[-1]=keys[0] if name!='ember-bubble' else Image.new('RGBA',(w,h))
        result[name]=frames
    return result


def render(name,index):
    w,h,count=SIZES[name];t=index/max(1,count-1)
    if name in {'ember-bubble','aurora-right','aurora-left'}:
        image=painted_effects()['aurora-right' if name=='aurora-left' else name][index].copy()
        return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if name=='aurora-left' else image
    image=Image.new('RGBA',(w,h));d=ImageDraw.Draw(image)
    r=8+100*t;opacity=round(230*(1-t)**1.5)
    for k in range(5,0,-1):
        q=r+k;d.ellipse((120-q,120-q,120+q,120+q),outline=(105,190,255,opacity//(k+1)),width=2)
    d.ellipse((120-r,120-r,120+r,120+r),outline=(215,240,255,opacity),width=2)
    return image


def build():
    for platform in ('macos','windows'):
        base=ROOT/f'assets/runtime/dragon-{platform}'
        for name,(w,h,count) in SIZES.items():
            directory=base/'fx'/name;directory.mkdir(parents=True,exist_ok=True)
            atlas=Image.new('RGBA',(4*w,math.ceil(count/4)*h))
            for i in range(count):
                image=render(name,i)
                if platform=='windows':
                    image.putalpha(image.getchannel('A').point(lambda a:255 if a>=28 else 0))
                image.save(directory/f'{i:02d}.png',optimize=True)
                atlas.alpha_composite(image,(i%4*w,i//4*h))
            atlas.save(base/f'{name}.png',optimize=True)
    print('Baked ember bubbles, aurora wisps and expanding thunder shockwaves')


if __name__=='__main__':build()
