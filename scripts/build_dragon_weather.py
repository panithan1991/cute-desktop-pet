"""Bake volumetric cloud animation and antialiased branching lightning."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.dragon_power_geometry import bolt_paths
from build_pet_atlases import premultiplied


def platform_image(im,platform):
    if platform=='windows':
        im=im.copy()
        im.putalpha(im.getchannel('A').point(lambda a:255 if a>=100 else 0))
    return im


def lightning_image(index,paths=None):
    scale=3
    size=(560*scale,480*scale)
    glow=Image.new('RGBA',size)
    if paths is None:paths=bolt_paths([(271,380),(289,380)],(560,480),1000+index,0)
    for image,color,multiplier in ((glow,(70,110,255,155),2.5),):
        draw=ImageDraw.Draw(image)
        for path in paths:
            width=2.1 if len(path)>=20 else 1.1 if len(path)>=12 else .55
            draw.line([(round(x*scale),round(y*scale)) for x,y in path],fill=color,width=max(1,round(width*multiplier*scale)))
    glow=glow.filter(ImageFilter.GaussianBlur(3.5*scale))
    draw=ImageDraw.Draw(glow)
    for path in paths:
        width=2.1 if len(path)>=20 else 1.1 if len(path)>=12 else .55
        coords=[(round(x*scale),round(y*scale)) for x,y in path]
        draw.line(coords,fill=(130,175,255,240),width=max(1,round(width*scale)))
        draw.line(coords,fill=(250,252,255,255),width=max(1,round(width*.48*scale)))
    return glow.resize((560,480),Image.Resampling.LANCZOS)


def build():
    source=Image.open(ROOT/'assets/source/dragon-vortex.png').convert('RGBA')
    keys=[]
    for i in range(8):
        x,y=i%4*source.width/4,i//4*source.height/2
        key=source.crop((round(x),round(y),round(x+source.width/4),round(y+source.height/2)))
        pixels=np.asarray(key).copy()
        bad=(pixels[:,:,2]>pixels[:,:,0]*1.4)&(pixels[:,:,2]>pixels[:,:,1]*1.25)
        pixels[bad]=0
        key=Image.fromarray(pixels)
        box=key.getchannel('A').point(lambda a:255 if a>24 else 0).getbbox()
        if not box:raise ValueError(f'Missing vortex {i}')
        keys.append(key.crop(box))
    scale=min(156/max(k.width for k in keys),176/max(k.height for k in keys))
    normalized=[]
    for key in keys:
        key=key.resize((round(key.width*scale),round(key.height*scale)),Image.Resampling.LANCZOS)
        im=Image.new('RGBA',(180,200));im.alpha_composite(key,((180-key.width)//2,188-key.height))
        normalized.append(im)
    loop=[]
    for i in range(8):
        loop.append(normalized[i])
        pixels=(premultiplied(normalized[i])+premultiplied(normalized[(i+1)%8]))*.5
        alpha=pixels[:,:,3:4]
        pixels[:,:,:3]=np.divide(pixels[:,:,:3],alpha,out=np.zeros_like(pixels[:,:,:3]),where=alpha>.001)
        loop.append(Image.fromarray(np.uint8(np.clip(pixels*255,0,255))))
    frames=[]
    for i in range(32):
        key=loop[i%16]
        growth=(i+1)/8 if i<8 else 1 if i<24 else (32-i)/8
        if growth<1:
            key=key.resize((round(180*growth),round(200*growth)),Image.Resampling.LANCZOS)
            frame=Image.new('RGBA',(180,200));frame.alpha_composite(key,((180-key.width)//2,200-key.height));key=frame
        frames.append(key)
    bounds=[]
    for i in range(16):
        bolt=lightning_image(i)
        bounds.append(bolt.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox())
        for platform in ('macos','windows'):
            platform_image(bolt,platform).save(ROOT/f'assets/runtime/dragon-{platform}/lightning-{i:02d}.png',optimize=True)
    for platform in ('macos','windows'):
        for side in ('right','left'):
            atlas=Image.new('RGBA',(180*4,200*8))
            for i,frame in enumerate(frames):
                frame=ImageOps.mirror(frame) if side=='left' else frame
                atlas.alpha_composite(platform_image(frame,platform),(i%4*180,i//4*200))
            atlas.save(ROOT/f'assets/runtime/dragon-{platform}/vortex-{side}.png',optimize=True)
    frames[15].save(ROOT/'assets/readme/dragon-vortex.png')
    lightning_image(4).save(ROOT/'assets/readme/dragon-lightning.png')
    (ROOT/'app/dragon_weather_layout.py').write_text(f'"""Baked lightning alpha bounds for safe placement near desktop edges."""\nLIGHTNING_BOUNDS={tuple(bounds)!r}\n',encoding='utf-8')
    print('Weather: 32 vortex frames and 16 lateral branching lightning patterns per platform')


if __name__=='__main__':build()
