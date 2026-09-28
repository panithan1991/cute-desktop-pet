"""Normalize existing pet portraits for the studio; no runtime Pillow needed."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]


def build():
    target=ROOT/'assets/ui';target.mkdir(exist_ok=True)
    for name in ('booboo','moo-krata','bibi','kitten','dragon'):
        with Image.open(ROOT/f'assets/readme/{name}.png') as source:
            image=source.convert('RGBA');bounds=image.getchannel('A').getbbox()
            image=image.crop(bounds);image.thumbnail((96,96),Image.Resampling.LANCZOS)
            canvas=Image.new('RGBA',(110,110))
            canvas.alpha_composite(image,((110-image.width)//2,(110-image.height)//2))
            canvas.save(target/f'{name}.png',optimize=True)


if __name__=='__main__':build()
