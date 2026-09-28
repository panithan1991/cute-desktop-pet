from collections import OrderedDict
from pathlib import Path
import unittest
from unittest.mock import MagicMock,patch
from PIL import Image,ImageOps
from app.dragon_power_view import DragonPowerView
from app.pet_sprites import PetSprites,DIRECT_DRAGON_POSES,POSES

ROOT=Path(__file__).resolve().parents[1]


class EffectLoadingTests(unittest.TestCase):
    def test_first_effect_request_decodes_only_one_small_frame_and_reuses_it(self):
        view=DragonPowerView.__new__(DragonPowerView)
        view.window=MagicMock();view.clip_frames=OrderedDict()
        image=MagicMock();image.width.return_value=image.height.return_value=240
        with patch('app.dragon_power_view.tk.PhotoImage',return_value=image) as create, patch('app.dragon_power_view.sys.platform','win32'):
            a=view.clip_image('cloud-flame',5,240,240,48)
            self.assertIs(a,view.clip_image('cloud-flame',5,240,240,48))
            view.clip_image('cloud-flame',5,240,240,48,2)
            self.assertEqual(create.call_count,1)
            self.assertTrue(Path(create.call_args.kwargs['file']).as_posix().endswith('/fx/cloud-flame/05.png'))
            self.assertEqual(image.subsample.call_count,1)

    def test_effect_cache_is_bounded(self):
        view=DragonPowerView.__new__(DragonPowerView)
        view.window=MagicMock();view.clip_frames=OrderedDict()
        image=MagicMock();image.width.return_value=image.height.return_value=240
        with patch('app.dragon_power_view.tk.PhotoImage',return_value=image):
            for i in range(120):view.clip_image('example',i,240,240,120)
        self.assertEqual(len(view.clip_frames),96)

    def test_detached_effect_files_keep_exact_pixels_and_platform_transparency(self):
        sizes={'cloud-flame':(240,240,48),'sky-rings':(96,96,24),'fury-aura':(240,200,32),
               **{f'fire-{s}':(240,160,32) for s in ('left','right')},
               **{f'vortex-{s}':(180,200,32) for s in ('left','right')},
               **{f'jade-rings-{s}':(96,96,24) for s in ('left','right')}}
        for platform in ('macos','windows'):
            for name,(w,h,count) in sizes.items():
                base=ROOT/f'assets/runtime/dragon-{platform}'
                with Image.open(base/f'{name}.png') as atlas:
                    for i in range(count):
                        x,y=i%4*w,i//4*h
                        expected=atlas.crop((x,y,x+w,y+h))
                        with Image.open(base/f'fx/{name}/{i:02d}.png') as actual:
                            self.assertEqual(expected.tobytes(),actual.tobytes(),f'{platform}/{name}/{i}')

    def test_cloud_body_loading_skips_tall_sprite_pages(self):
        image=MagicMock();image.width.return_value=image.height.return_value=160
        with patch('app.pet_sprites.tk.PhotoImage',return_value=image) as create,patch('app.pet_sprites.sys.platform','win32'):
            sprites=PetSprites(MagicMock(),'dragon')
            sprites.get('dragon_fire_00',1)
            self.assertFalse(sprites.pages)
            self.assertIn('/body-fx/right/dragon_fire_00.ppm',Path(create.call_args.kwargs['file']).as_posix())

    def test_direct_body_frames_match_original_pixels_both_facings(self):
        for platform in ('macos','windows'):
            suffix='-windows' if platform=='windows' else ''
            with Image.open(ROOT/f'assets/dragon-motion{suffix}.png') as atlas:
                for pose in DIRECT_DRAGON_POSES:
                    i=POSES['dragon'].index(pose);x,y=i%5*160,i//5*160
                    for side in ('right','left'):
                        expected=atlas.crop((x,y,x+160,y+160))
                        if side=='left':expected=ImageOps.mirror(expected)
                        if platform=='windows':
                            rgb=Image.new('RGB',expected.size,'#ff00ff');rgb.paste(expected,mask=expected.getchannel('A'));expected=rgb
                        extension='ppm' if platform=='windows' else 'png'
                        with Image.open(ROOT/f'assets/runtime/dragon-{platform}/body-fx/{side}/{pose}.{extension}') as actual:
                            self.assertEqual(expected.tobytes(),actual.tobytes())
