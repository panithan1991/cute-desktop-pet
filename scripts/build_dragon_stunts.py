"""Bake belly-up rest and a complete, bounded somersault cycle."""
import math
from pathlib import Path
from PIL import Image
import numpy as np
from build_pet_atlases import isolate,inbetweens
from build_behavior_atlases import normalize_row,tween_path

ROOT=Path(__file__).resolve().parents[1]


def belly_sequence(idle):
    source=Image.open(ROOT/'assets/source/dragon-belly-smoke.png').convert('RGBA')
    cells=[];boxes=[]
    for i in range(8):
        x,y=i%4*source.width//4,i//4*source.height//2
        cell=isolate(source.crop((x,y,x+source.width//4,y+source.height//2)))
        box=cell.getchannel('A').getbbox();boxes.append(box);cells.append(cell.crop(box))
    keys=normalize_row(cells,idle);keys[0]=keys[-1]=idle
    # Annotated mouth centers in source-cell coordinates, normalized using the
    # same scale/ground anchor as the body, never a whole-body bounding guess.
    raw=((353,258),(387,323),(217,241),(252,213),(237,169),(240,170),(407,299),(390,217))
    b=idle.getchannel('A').getbbox();ax=(b[0]+b[2])/2;ay=b[3]
    scale=min((b[3]-b[1])/cells[0].height,132/max(c.height for c in cells),136/max(c.width for c in cells))
    mouthkeys=[(round(ax-c.width*scale/2+(p[0]-box[0])*scale),round(ay-c.height*scale+(p[1]-box[1])*scale)) for c,p,box in zip(cells,raw,boxes)]
    # Entry, three small breath cycles, and return to sitting.
    paths=((keys[:4],mouthkeys[:4],24),([keys[3],keys[4],keys[5],keys[3]],[mouthkeys[3],mouthkeys[4],mouthkeys[5],mouthkeys[3]],24),([keys[3],keys[6],keys[7]],[mouthkeys[3],mouthkeys[6],mouthkeys[7]],24))
    frames=[];mouths=[]
    for path,anchors,count in (paths[0],paths[1],paths[1],paths[1],paths[2]):
        segment=tween_path(path,count)
        for i,frame in enumerate(segment):
            t=i/(count-1)*(len(anchors)-1);a=min(len(anchors)-2,int(t));f=t-a
            mouth=tuple(anchors[a][j]*(1-f)+anchors[a+1][j]*f for j in (0,1))
            if 24<=len(frames)<96:
                breath=.42*math.sin(len(frames)*.27)
                frame=frame.transform((160,160),Image.Transform.AFFINE,(1,0,0,0,1,breath),Image.Resampling.BICUBIC)
                mouth=(mouth[0],mouth[1]-breath)
            frames.append(frame);mouths.append(mouth)
    frames[0]=frames[-1]=idle
    (ROOT/'app/dragon_belly_layout.py').write_text(f'"""Painted belly-up mouth anchors."""\nBELLY_MOUTHS={tuple(mouths)!r}\n',encoding='utf-8')
    return frames


def roll_sequences(hover):
    box=hover.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
    crop=hover.crop(box)
    scale=min(1,142/math.hypot(crop.width,crop.height))
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=((160-crop.width)/2,(160-crop.height)/2)
    compact=Image.new('RGBA',(160,160));compact.alpha_composite(crop,tuple(round(v) for v in offset))
    head=hover.getchannel('A').crop((68,5,102,90)).point(lambda a:255 if a>80 else 0).getbbox()
    hornsrc=((76,head[1]+11),(94,head[1]+11))
    horns=[((x-box[0])*scale+round(offset[0]),(y-box[1])*scale+round(offset[1])) for x,y in hornsrc]
    result={'roll_enter':tween_path([hover,compact],15),'roll_loop':[],'roll_exit':tween_path([compact,hover],15)}
    result["roll_enter"][0]=hover
    result["roll_enter"][-1]=compact
    result["roll_exit"][0]=compact
    result["roll_exit"][-1]=hover
    layout={}
    for name,a,b in (('roll_enter',hornsrc,horns),('roll_exit',horns,hornsrc)):
        layout[name]=tuple(tuple(tuple(p[j]*(1-i/14)+q[j]*i/14 for j in (0,1)) for p,q in zip(a,b)) for i in range(15))
    rotated=[]
    for i in range(90):
        angle=i*4;rad=math.radians(angle)
        result['roll_loop'].append(compact.rotate(angle,resample=Image.Resampling.BICUBIC,center=(80,80)))
        rotated.append(tuple((80+(x-80)*math.cos(rad)+(y-80)*math.sin(rad),80-(x-80)*math.sin(rad)+(y-80)*math.cos(rad)) for x,y in horns))
    result["roll_loop"][0]=compact
    layout['roll_loop']=tuple(rotated)
    (ROOT/'app/dragon_roll_layout.py').write_text(f'"""Horn anchors rotate with the entire unchanged body."""\nROLL_HORNS={layout!r}\n',encoding='utf-8')
    return result


def fury_sequence(idle):
    from build_behavior_atlases import extract
    keys=normalize_row(extract(ROOT/'assets/source/dragon-fury.png',count=8,columns=4),idle)
    keys[0]=keys[-1]=idle
    frames=tween_path(keys[:4],30)
    for repeat in range(4):
        for frame in tween_path([keys[3],keys[4],keys[5],keys[4],keys[3]],30):
            breath=.3*math.sin(len(frames)*.23)
            frames.append(frame.transform((160,160),Image.Transform.AFFINE,(1,0,0,0,1,breath),Image.Resampling.BICUBIC))
    frames.extend(tween_path([keys[3],keys[6],idle],30))
    horns=[]
    for frame in frames:
        head=frame.getchannel('A').crop((66,5,102,100)).point(lambda a:255 if a>80 else 0).getbbox()
        horns.append(((70,head[1]+17),(96,head[1]+17)))
    (ROOT/'app/dragon_fury_layout.py').write_text(f'"""Frontal fury horn anchors."""\nFURY_HORNS={tuple(horns)!r}\n',encoding='utf-8')
    return frames
