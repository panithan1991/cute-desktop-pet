"""Static README examples rendered from the same assets and effect geometry."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.behavior_art import EXTRA_CLIPS
from app.dragon_power_geometry import gust_transform
from app.dragon_fire_layout import FIRE_NOZZLES
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
    nx,ny=FIRE_NOZZLES[15]
    panels[0].alpha_composite(flame,(round(80+mx-nx),round(130+my-ny)))
    panels[1].alpha_composite(body(EXTRA_CLIPS['dragon']['storm_hover'][70]),(210,160))
    lightning=Image.open(ROOT/'assets/readme/dragon-lightning.png').convert('RGBA')
    hx,hy=HORN_POSITIONS[70][0]
    panels[1].alpha_composite(lightning,(210+hx-271,160+hy-380))
    panels[2].alpha_composite(body(EXTRA_CLIPS['dragon']['wing_gust'][30]),(350,130))
    cx,cy=gust_transform((392,235),(560,330),-1,.78)
    vortex=Image.open(ROOT/'assets/readme/dragon-vortex.png').convert('RGBA')
    panels[2].alpha_composite(vortex,(round(cx-90),round(cy-200)))
    output=Image.new('RGB',(1680,330))
    for i,im in enumerate(panels):output.paste(im,(i*560,0))
    output.save(ROOT/'assets/readme/dragon-powers.png',optimize=True)


if __name__=='__main__':build()
