"""Bake painted personality/flight poses; keep existing 1,110 frames intact."""
from pathlib import Path
import sys, math
from functools import lru_cache
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.dragon_personality import NEW_ACTIVITIES, AIR_GESTURES, PERCH_CLIPS
from app.dragon_animation import DRAGON_CLIPS
from app.pet_sprites import POSES
from build_behavior_atlases import extract, normalize_row, tween_path, frame_at, save


@lru_cache(maxsize=1)
def sequences():
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        idle=frame_at(atlas,0).convert('RGBA')
        hover=frame_at(atlas,POSES['dragon'].index(DRAGON_CLIPS['hover'][0])).convert('RGBA')
    ground=extract(ROOT/'assets/source/dragon-personality-keyframes.png',24,4)
    air=extract(ROOT/'assets/source/dragon-flight-keyframes.png',16,4)
    mapping={'proud':0,'curious_sniff':1,'happy':2,'static_charge':3,
             'ember_bubbles':4,'aurora_breath':4,'thunder_roar':5}
    result={}
    for name in NEW_ACTIVITIES:
        if name in AIR_GESTURES:
            row=list(('hover_float','dive_recover','air_brake','perch_landing')).index(name)
            keys=normalize_row(air[row*4:row*4+4],hover)
            keys[0]=hover
            if name=='perch_landing':
                keys=[hover,keys[1],keys[2],idle,idle,idle]
            else:
                keys[-1]=hover
                if name=='hover_float':keys=[hover,keys[1],keys[2],keys[1],keys[2],hover]
        else:
            row=mapping[name];keys=normalize_row(ground[row*4:row*4+4],idle)
            keys[0]=keys[-1]=idle
            if name=='happy':keys=[idle,keys[1],keys[2],keys[1],keys[2],idle]
        if name in {'ember_bubbles','aurora_breath','thunder_roar'}:
            # Mouth reaches the painted emission pose before particles begin,
            # stays open through the active interval, then closes into idle.
            entry=tween_path(keys[:3],11)[:-1]
            held=[]
            for i in range(22):
                sy=1/(1+.003*math.sin(i/21*math.tau))
                held.append(keys[2].transform((160,160),Image.Transform.AFFINE,
                            (1,0,0,0,sy,142*(1-sy)),Image.Resampling.BICUBIC))
            result[name]=entry+held+tween_path([keys[2],idle],9)[1:]
        else:result[name]=tween_path(keys,40)
    edge=extract(ROOT/'assets/source/dragon-edge-perch.png',8,4)
    for i,name in enumerate(PERCH_CLIPS):
        keys=normalize_row(edge[i*4:i*4+4],hover)
        grip=keys[1];opened=keys[2]
        result[name]=tween_path([hover,keys[0],grip],13)+tween_path([grip,opened],9)[1:]+[opened]*10+tween_path([opened,grip],10)[1:]
    return result


def build():
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        frames=[frame_at(atlas,i).convert('RGBA') for i in range(1110)]
    clips=sequences()
    for name in (*NEW_ACTIVITIES,*PERCH_CLIPS):frames.extend(clips[name])
    save('dragon',frames)
    scene=Image.new('RGB',(960,700),'#14222b');draw=ImageDraw.Draw(scene)
    for i,(name,clip) in enumerate((n,clips[n]) for n in NEW_ACTIVITIES):
        x,y=i%4*240,i//4*230
        draw.text((x+14,y+12),NEW_ACTIVITIES[name].label,fill='white')
        scene.paste(clip[23],(x+40,y+45),clip[23].getchannel('A'))
    scene.save(ROOT/'assets/readme/dragon-personality.png')
    print(f'Dragon: {len(frames)} body frames; {len(clips)} new gestures')


if __name__=='__main__':build()
