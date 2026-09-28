import random
import unittest
from pathlib import Path
from PIL import Image
from app.dragon_cloud import cloud_frame,cloud_center,cloud_sparks
from app.dragon_animation import DragonBehavior,DRAGON_CLIPS
from app.dragon_power_geometry import overlay_rect


class JadeCloudTests(unittest.TestCase):
    def test_ordered_emission_hold_ignition_burn_and_disappearance(self):
        for t,first,last in ((.2,0,11),(.45,12,19),(.6,20,31),(.8,32,39),(.9,40,47)):
            self.assertTrue(first<=cloud_frame(t*20,20)<=last)
        self.assertIsNone(cloud_frame(0,20))
        self.assertIsNone(cloud_frame(20,20))

    def test_entire_cloud_stays_inside_small_and_large_desktops(self):
        for bounds in ((0,0,1920,1080),(-1280,-300,0,720),(0,0,300,220)):
            for facing in (-1,1):
                for origin in ((bounds[0]+20,bounds[1]+20),(bounds[2]-20,bounds[3]-20)):
                    rect=overlay_rect(origin,bounds)
                    cx,cy,scale=cloud_center(origin,facing,rect)
                    self.assertGreaterEqual(cx-120/scale,0)
                    self.assertGreaterEqual(cy-120/scale,0)
                    self.assertLessEqual(cx+120/scale,rect[2])
                    self.assertLessEqual(cy+120/scale,rect[3])

    def test_sparks_are_clock_deterministic_and_fall_after_initial_lift(self):
        self.assertEqual(cloud_sparks(14,20,11),cloud_sparks(14,20,11))
        self.assertEqual(cloud_sparks(5,20,11),[])
        self.assertEqual(cloud_sparks(20,20,11),[])
        first=cloud_sparks(11.41,20,11)[0]
        later=cloud_sparks(12.9,20,11)[0]
        self.assertGreater(later[1],first[1])
        self.assertLess(later[2],first[2])

    def test_detached_ignition_keeps_original_body_then_returns_to_sitting(self):
        pet=DragonBehavior(random.Random(3));pet.force('cloud_flame')
        pet.transition.queue=[]
        for t in (.0,.1,.3,.7,.99):
            pet.elapsed=pet.duration*t
            self.assertIn(pet.pose(),DRAGON_CLIPS['fire'])
        self.assertEqual(pet.pose(),DRAGON_CLIPS['fire'][-1])
        before=(pet.pose(),pet.elapsed);pet.step(.1,frozen=True)
        self.assertEqual(before,(pet.pose(),pet.elapsed))

    def test_baked_cloud_padding_alpha_and_final_empty_frame(self):
        root=Path(__file__).resolve().parents[1]
        for platform in ('windows','macos'):
            with Image.open(root/f'assets/runtime/dragon-{platform}/cloud-flame.png') as sheet:
                self.assertEqual(sheet.size,(960,2880))
                if platform=='windows':self.assertEqual(set(sheet.getchannel('A').tobytes()),{0,255})
                for i in range(48):
                    frame=sheet.crop((i%4*240,i//4*240,(i%4+1)*240,(i//4+1)*240))
                    box=frame.getchannel('A').getbbox()
                    if i==47:self.assertIsNone(box)
                    elif box:self.assertGreaterEqual(min(box[0],box[1],240-box[2],240-box[3]),12)

    def test_fully_burned_gas_contains_no_dark_grey_cloud_and_phases_join(self):
        root=Path(__file__).resolve().parents[1]
        with Image.open(root/'assets/runtime/dragon-macos/cloud-flame.png') as sheet:
            def frame(i):return sheet.crop((i%4*240,i//4*240,(i%4+1)*240,(i//4+1)*240))
            for a,b in ((11,12),(19,20),(31,32),(39,40)):
                self.assertEqual(frame(a).tobytes(),frame(b).tobytes())
            for i in range(32,47):
                image=frame(i);dark_grey=opaque=0
                for y in range(240):
                    for x in range(240):
                        r,g,b,a=image.getpixel((x,y))
                        if a>128:
                            opaque+=1
                            dark_grey+=abs(r-g)<15 and abs(g-b)<15 and max(r,g,b)<185
                self.assertLessEqual(dark_grey/max(1,opaque),.005)
