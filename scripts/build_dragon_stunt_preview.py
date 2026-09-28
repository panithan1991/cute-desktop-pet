"""Static examples of the belly-up, somersault and fury activities."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.pet_sprites import POSES
from app.dragon_belly_layout import BELLY_MOUTHS
from app.dragon_roll_layout import ROLL_HORNS
from app.dragon_fury_layout import FURY_HORNS


def build():
    atlas=Image.open(ROOT/'assets/dragon-motion.png').convert('RGBA')
    def body(name):
        i=POSES['dragon'].index(name)
        return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160))
    panels=[Image.new('RGBA',(560,360),'#18212c') for _ in range(3)]
    for panel,title in zip(panels,('Chill sky rings','2–3 thunder somersaults','Fury')):
        ImageDraw.Draw(panel).text((16,15),title,fill='#e6eef4')
    panels[0].alpha_composite(body('extra_belly_smoke_48'),(200,180))
    mx,my=BELLY_MOUTHS[48]
    ring=Image.open(ROOT/'assets/readme/dragon-sky-ring.png').convert('RGBA')
    for drift in (50,115):panels[0].alpha_composite(ring,(round(200+mx-48),round(180+my-48-drift)))
    panels[1].alpha_composite(body('extra_roll_loop_22'),(200,160))
    for side,(hx,hy) in zip(('left','right'),sorted(ROLL_HORNS['roll_loop'][22])):
        tree=Image.open(ROOT/f'assets/runtime/dragon-macos/tree-{side}-04.png').convert('RGBA')
        panels[1].alpha_composite(tree,(round(200+hx-280),round(160+hy-380)))
    aura=Image.open(ROOT/'assets/readme/dragon-fury-aura.png').convert('RGBA')
    panels[2].alpha_composite(aura,(160,130))
    for side,(hx,hy) in zip(('left','right'),FURY_HORNS[70]):
        tree=Image.open(ROOT/f'assets/runtime/dragon-macos/tree-{side}-04.png').convert('RGBA')
        panels[2].alpha_composite(tree,(round(200+hx-280),round(180+hy-380)))
    vortex=Image.open(ROOT/'assets/readme/dragon-vortex.png').convert('RGBA').resize((90,100),Image.Resampling.LANCZOS)
    for x in (120,355):panels[2].alpha_composite(vortex,(x,220))
    panels[2].alpha_composite(body('extra_fury_70'),(200,180))
    output=Image.new('RGB',(1680,360))
    for i,panel in enumerate(panels):output.paste(panel,(i*560,0))
    output.save(ROOT/'assets/readme/dragon-stunts.png',optimize=True)


if __name__=='__main__':build()
