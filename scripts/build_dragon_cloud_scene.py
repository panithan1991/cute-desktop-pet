"""Static examples of ring transport and the illuminated ignition reaction."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.dragon_animation import DragonBehavior,DRAGON_CLIPS
from app.pet_sprites import POSES
from app.dragon_cloud import cloud_frame,gas_ring,RING_BIRTHS,cloud_sparks,CLOUD_DISTANCE
from app.dragon_effect_layout import MOUTH_POSITIONS


def build():
    body=Image.open(ROOT/'assets/dragon-motion.png').convert('RGBA')
    cloud=Image.open(ROOT/'assets/runtime/dragon-macos/cloud-flame.png').convert('RGBA')
    ring=Image.open(ROOT/'assets/runtime/dragon-macos/jade-rings-right.png').convert('RGBA')
    scene=Image.new('RGBA',(1100,350),'#14222b');draw=ImageDraw.Draw(scene)
    for column,(fraction,title) in enumerate(((.24,'Smoke rings gather 2.5 body lengths away'),(.70,'Excited eyes and green reflections during ignition'))):
        pet=DragonBehavior();pet.force('cloud_flame');pet.transition.queue=[];pet.duration=20;pet.elapsed=20*fraction
        i=POSES['dragon'].index(pet.pose());sprite=body.crop((i%5*160,i//5*160,(i%5+1)*160,(i//5+1)*160))
        ox,oy=column*550+16,180
        scene.alpha_composite(sprite,(ox,oy));draw.text((column*550+16,12),title,fill='white')
        first=int(RING_BIRTHS[0]/.52*len(DRAGON_CLIPS['fire']))
        origin=(ox+MOUTH_POSITIONS[first][0],oy+MOUTH_POSITIONS[first][1]);target=(origin[0]+CLOUD_DISTANCE,origin[1]-65)
        for j,birth in enumerate(RING_BIRTHS):
            anchor=MOUTH_POSITIONS[min(42,int(birth/.52*43))]
            position=gas_ring(pet.elapsed,20,j,(ox+anchor[0],oy+anchor[1]),target)
            if position:
                x,y,k=position;image=ring.crop((k%4*96,k//4*96,(k%4+1)*96,(k//4+1)*96))
                scene.alpha_composite(image,(round(x-48),round(y-48)))
        k=cloud_frame(pet.elapsed,20)
        image=cloud.crop((k%4*240,k//4*240,(k%4+1)*240,(k//4+1)*240))
        scene.alpha_composite(image,(round(target[0]-120),round(target[1]-120)))
        for dx,dy,fade in cloud_sparks(pet.elapsed,20,14):
            x,y=target[0]+dx,target[1]+dy;r=1+fade
            draw.ellipse((x-r,y-r,x+r,y+r),fill='#9dffe2')
    scene.convert('RGB').save(ROOT/'assets/readme/dragon-cloud-scene.png')


if __name__=='__main__':build()
