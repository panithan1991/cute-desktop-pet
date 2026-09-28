import unittest

from PIL import Image

from app.pet_sprites import CELL, PAGE_FRAMES, POSES, atlas_path, dragon_page_path


class DragonPagesTests(unittest.TestCase):
    def test_packaged_pages_match_full_atlas_for_every_frame_and_both_platforms(self):
        count = len(POSES["dragon"])
        for platform in ("win32","darwin"):
            for facing in (1,-1):
                atlas = Image.open(atlas_path("dragon",facing,platform)).convert("RGBA")
                for start in range(0,count,PAGE_FRAMES):
                    page = Image.open(dragon_page_path(facing,start//PAGE_FRAMES,platform)).convert("RGBA")
                    y = start//5*CELL
                    end = min(atlas.height,y+PAGE_FRAMES//5*CELL)
                    self.assertEqual(page.tobytes(),atlas.crop((0,y,CELL*5,end)).tobytes())

