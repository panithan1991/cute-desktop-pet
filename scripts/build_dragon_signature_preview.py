"""Still examples of the four new elemental signatures for the README."""
from pathlib import Path
import sys, math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.behavior_art import EXTRA_CLIPS
from app.dragon_personality import NEW_ACTIVITIES


def build():
    scene=Image.new('RGBA',(1600,300),'#14222b');draw=ImageDraw.Draw(scene)
    with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
        for col,state in enumerate(('ember_bubbles','static_charge','aurora_breath','thunder_roar')):
            x=col*400+12;y=125
            draw.text((col*400+12,14),NEW_ACTIVITIES[state].label,fill='white')
            i=POSES['dragon'].index(EXTRA_CLIPS['dragon'][state][20])
            body=atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160))
            mx,my=x+119,y+92;hx,hy=x+85,y+60
            scene.alpha_composite(body,(x,y))
            if state=='ember_bubbles':
                for j in range(4):
                    bubble=Image.open(ROOT/f'assets/runtime/dragon-macos/fx/ember-bubble/{5+j*4:02d}.png')
                    scene.alpha_composite(bubble,(mx+12+j*24-48,my-j*20-48))
            elif state=='aurora_breath':
                plume=Image.open(ROOT/'assets/runtime/dragon-macos/fx/aurora-right/12.png')
                plume=plume.resize((150,100),Image.Resampling.LANCZOS)
                scene.alpha_composite(plume,(mx,my-50))
            elif state=='static_charge':
                from app.dragon_charge_layout import charge_horns
                for part,(px,py) in zip(('rear','front'),charge_horns(20)):
                    corona=Image.open(ROOT/f'assets/runtime/dragon-macos/fx/charge-{part}-right/12.png').resize((64,64),Image.Resampling.LANCZOS)
                    scene.alpha_composite(corona,(round(x+px-32),round(y+py-54)))
            elif state=='thunder_roar':
                for j in range(4):
                    tree=Image.open(ROOT/f'assets/runtime/dragon-macos/tree-right-{(3+j*5)%16:02d}.png').resize((280,240),Image.Resampling.LANCZOS)
                    scene.alpha_composite(tree,(mx-140,my-190))
    scene.convert('RGB').save(ROOT/'assets/readme/dragon-signature-powers.png')
    detail=Image.new('RGBA',(960,640),'#14222b');labels=ImageDraw.Draw(detail)
    labels.text((18,12),'Thunder Roar — 3–4 rapid mouth-rooted branching channels',fill='white')
    i=POSES['dragon'].index(EXTRA_CLIPS['dragon']['thunder_roar'][20])
    body=Image.open(ROOT/'assets/dragon-motion.png').crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160))
    detail.alpha_composite(body,(22,220))
    for j in range(4):
        tree=Image.open(ROOT/f'assets/runtime/dragon-macos/tree-right-{(3+j*5)%16:02d}.png').resize((280,240),Image.Resampling.LANCZOS)
        detail.alpha_composite(tree,(22+119-140,220+92-190))
    labels.text((18,424),'Ember Bubbles — emerge, expand, rupture, dissolve',fill='white')
    for j,(k,title) in enumerate(((4,'Emerge'),(14,'Expand'),(26,'Delicate fiery membrane'),(32,'Burst and dissolve'))):
        bubble=Image.open(ROOT/f'assets/runtime/dragon-macos/fx/ember-bubble/{k:02d}.png')
        detail.alpha_composite(bubble,(j*240+60,466));labels.text((j*240+20,584),title,fill='white')
    detail.convert('RGB').save(ROOT/'assets/readme/dragon-roar-and-bubbles.png')


if __name__=='__main__':build()
