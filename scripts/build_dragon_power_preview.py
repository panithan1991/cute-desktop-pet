"""Static README examples rendered from the same assets and effect geometry."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.behavior_art import EXTRA_CLIPS
from app.dragon_power_geometry import bolt_paths,gust_paths
from app.dragon_effect_layout import MOUTH_POSITIONS,HORN_POSITIONS


def build():
    atlas=Image.open(ROOT/'assets/dragon-motion.png').convert('RGBA')
    def body(name):
        i=POSES['dragon'].index(name)
        return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160))
    panels=[]
    for title in ('Fantasy flame','Horn lightning','One-wing whirlwind'):
        im=Image.new('RGBA',(560,330),'#18212c')
        ImageDraw.Draw(im).text((16,15),title,fill='#e6eef4')
        panels.append(im)
    index=20
    panels[0].alpha_composite(body(f'dragon_fire_{index:02d}'),(80,130))
    flame=Image.open(ROOT/'assets/readme/dragon-fantasy-fire.png').convert('RGBA')
    mx,my=MOUTH_POSITIONS[index]
    panels[0].alpha_composite(flame,(80+mx-4,130+my-80))
    panels[1].alpha_composite(body(EXTRA_CLIPS['dragon']['storm_hover'][70]),(210,160))
    draw=ImageDraw.Draw(panels[1])
    for path in bolt_paths([(210+x,160+y) for x,y in HORN_POSITIONS[70]],(560,330),30,4):
        for color,width in (('#3e4977',6),('#8b7dff',3),('#fcfaff',1)):
            draw.line(path,fill=color,width=width)
    panels[2].alpha_composite(body(EXTRA_CLIPS['dragon']['wing_gust'][30]),(350,130))
    draw=ImageDraw.Draw(panels[2])
    for path in gust_paths((392,235),(560,330),-1,.78,6):
        draw.line(path,fill='#576c81',width=3)
        draw.line(path,fill='#daeaf1',width=1)
    output=Image.new('RGB',(1680,330))
    for i,im in enumerate(panels):output.paste(im,(i*560,0))
    output.save(ROOT/'assets/readme/dragon-powers.png',optimize=True)


if __name__=='__main__':build()
