import math
import random
import unittest
from pathlib import Path

from PIL import Image, ImageOps
from app.dragon_animation import DragonBehavior, DRAGON_ACTIVITIES
from app.behavior_art import EXTRA_CLIPS
from app.dragon_power_geometry import fire_frame, overlay_rect, bolt_paths, gust_transform


class DragonPowerTests(unittest.TestCase):
    def test_long_flame_has_ignition_sustained_flicker_and_fade(self):
        reached = {fire_frame(i/100,14) for i in range(1401)}
        self.assertEqual(reached,set(range(32))|{None})
        self.assertTrue(all(8<=fire_frame(t,14)<=23 for t in (3,5,8,11)))
        self.assertIsNone(fire_frame(14,14))

    def test_fire_drawings_are_large_complete_and_mirrored(self):
        base = Path(__file__).resolve().parents[1]/'assets/runtime/dragon-macos'
        right,left = [Image.open(base/f'fire-{side}.png').convert('RGBA') for side in ('right','left')]
        widths = []
        for i in range(32):
            x,y = i%4*240,i//4*160
            a,b = [im.crop((x,y,x+240,y+160)) for im in (right,left)]
            self.assertEqual(ImageOps.mirror(a).tobytes(),b.tobytes())
            box = a.getchannel('A').point(lambda v:255 if v>40 else 0).getbbox()
            self.assertIsNotNone(box)
            self.assertGreaterEqual(min(box[0],box[1],240-box[2],160-box[3]),3)
            if 8<=i<24: widths.append(box[2]-box[0])
        self.assertGreater(max(widths),200)

    def test_random_lightning_stays_inside_screen_and_stable_per_flash(self):
        origin = [(270,220),(290,220)]
        a = bolt_paths(origin,(560,480),20,3)
        self.assertEqual(a,bolt_paths(origin,(560,480),20,3))
        self.assertNotEqual(a,bolt_paths(origin,(560,480),21,3))
        self.assertNotEqual(a,bolt_paths(origin,(560,480),20,4))
        for seed in range(50):
            paths=bolt_paths(origin,(560,480),seed,3)
            self.assertTrue(all(12<=x<=548 and 12<=y<=468 for path in paths for x,y in path))
            self.assertGreater(max(math.dist(path[0],path[-1]) for path in paths),150)
        for point in ((0,0),(1920,0),(0,1040),(1920,1040)):
            x,y,w,h=overlay_rect(point,(0,0,1920,1040))
            self.assertTrue(0<=x<=1920-w and 0<=y<=1040-h)

    def test_whirlwind_drifts_towards_the_flapping_wing_and_freezes(self):
        for sign in (-1,1):
            early=gust_transform((280,380),(560,480),sign,.3)
            late=gust_transform((280,380),(560,480),sign,.8)
            self.assertGreater(sign*(late[0]-early[0]),100)
            self.assertEqual(late,gust_transform((280,380),(560,480),sign,.8))
            self.assertTrue(90<=late[0]<=470 and 210<=late[1]<=468)

    def test_interrupted_gesture_starts_bridge_at_its_current_pose(self):
        pet=DragonBehavior(random.Random(8))
        pet.force('wing_gust');pet.transition.queue=[]
        pet.elapsed=pet.duration*.5
        before=pet.pose()
        pet.force('smoke')
        self.assertEqual(pet.pose(),before)
        while pet.transition.active: pet.step(.1)
        self.assertEqual(pet.pose(),'dragon_smoke_00')
        self.assertLessEqual(DRAGON_ACTIVITIES['smoke'].cooldown,8)
        self.assertLessEqual(DRAGON_ACTIVITIES['fire'].cooldown,10)

    def test_sleep_transition_does_not_restart_at_upright_pose(self):
        pet=DragonBehavior(random.Random(3))
        pet.force('sleep')
        self.assertTrue(pet.transition.active)
        while pet.transition.active: pet.step(.1)
        self.assertGreaterEqual(pet.elapsed,4)
        self.assertIn(pet.pose(),__import__('app.dragon_animation',fromlist=['DRAGON_CLIPS']).DRAGON_CLIPS['sleep'][5:])

    def test_one_wing_clip_joins_exact_neutral_body_at_both_ends(self):
        from app.pet_sprites import POSES,atlas_path
        from test_behavior_art import frame
        poses=POSES['dragon']
        atlas=Image.open(atlas_path('dragon',1,'darwin')).convert('RGBA')
        idle=frame(atlas,0).tobytes()
        clip=EXTRA_CLIPS['dragon']['wing_gust']
        for name in (clip[0],clip[-1]):
            self.assertEqual(frame(atlas,poses.index(name)).tobytes(),idle)

    def test_weather_images_have_complete_alpha_and_no_windows_magenta_matte(self):
        root=Path(__file__).resolve().parents[1]/'assets/runtime'
        for platform in ('macos','windows'):
            directory=root/f'dragon-{platform}'
            for i in range(16):
                image=Image.open(directory/f'lightning-{i:02d}.png').convert('RGBA')
                self.assertEqual(image.size,(560,480))
                bounds=image.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
                self.assertGreaterEqual(min(bounds[0],bounds[1],560-bounds[2],480-bounds[3]),5)
                if platform=='windows':self.assertLessEqual(set(image.getchannel('A').tobytes()),{0,255})
            a,b=[Image.open(directory/f'vortex-{side}.png').convert('RGBA') for side in ('right','left')]
            self.assertEqual(a.size,(720,1600))
            for i in range(32):
                x,y=i%4*180,i//4*200
                right,left=[im.crop((x,y,x+180,y+200)) for im in (a,b)]
                self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes())
                bounds=right.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
                self.assertIsNotNone(bounds)
                self.assertGreaterEqual(min(bounds[0],bounds[1],180-bounds[2],200-bounds[3]),1)
            if platform=='windows':self.assertLessEqual(set(a.getchannel('A').tobytes()),{0,255})

    def test_lightning_tree_forks_only_outwards_from_each_horn(self):
        paths=bolt_paths([(271,380),(289,380)],(560,480),3,2)
        self.assertEqual(len(paths),26)
        for side,tree in enumerate((paths[:13],paths[13:])):
            sign=-1 if side==0 else 1
            for path in tree:
                self.assertTrue(all(sign*(b[0]-a[0])>=0 for a,b in zip(path,path[1:])))
