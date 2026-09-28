import random
import unittest
from pathlib import Path
from PIL import Image
from app.dragon_cloud import cloud_frame,cloud_center,cloud_sparks,cloud_overlay_rect,gas_ring,RING_TRAVEL,CLOUD_DISTANCE,DRAGON_VISIBLE_SPAN
from app.dragon_animation import DragonBehavior,DRAGON_CLIPS
from app.dragon_power_geometry import overlay_rect


class JadeCloudTests(unittest.TestCase):
    def test_cloud_target_is_two_and_a_half_visible_body_spans_away(self):
        self.assertEqual(CLOUD_DISTANCE,2.5*DRAGON_VISIBLE_SPAN)
        for facing in (-1,1):
            origin=(960,700);rect=cloud_overlay_rect(origin,(0,0,1920,1080),facing)
            cx,cy,scale=cloud_center(origin,facing,rect)
            self.assertEqual(scale,1)
            self.assertAlmostEqual(facing*(cx+rect[0]-origin[0]),CLOUD_DISTANCE)

    def test_ring_trajectory_moves_forward_upward_then_disappears_at_cloud(self):
        for facing in (-1,1):
            origin=(500,400);target=(500+facing*CLOUD_DISTANCE,335)
            early=gas_ring(20*.07+.1,20,0,origin,target)
            late=gas_ring(20*.07+2.4,20,0,origin,target)
            self.assertGreater(facing*(late[0]-early[0]),CLOUD_DISTANCE*.75)
            self.assertLess(late[1],early[1])
            self.assertIsNone(gas_ring(20*.07+RING_TRAVEL+.01,20,0,origin,target))
            self.assertIsNone(gas_ring(0,20,0,origin,target))
            self.assertEqual(late,gas_ring(20*.07+2.4,20,0,origin,target))

    def test_excited_green_reflections_connect_to_exact_idle_endpoints(self):
        from app.pet_sprites import POSES
        from app.behavior_art import EXTRA_CLIPS
        keys=EXTRA_CLIPS['dragon']['ignition_reaction'];poses=POSES['dragon']
        with Image.open(Path(__file__).resolve().parents[1]/'assets/dragon-motion.png') as sheet:
            def pixels(pose):
                i=poses.index(pose);return sheet.crop((i%5*160,i//5*160,(i%5+1)*160,(i//5+1)*160))
            neutral=pixels('dragon_idle_00')
            self.assertEqual(pixels(keys[0]).tobytes(),neutral.tobytes())
            self.assertEqual(pixels(keys[-1]).tobytes(),neutral.tobytes())
            lit=pixels(keys[20])
            count=sum(lit.getpixel((x,y))[1]>lit.getpixel((x,y))[0]*1.2 and lit.getpixel((x,y))[3]>128 for x in range(160) for y in range(160))
            self.assertGreater(count,50)

    def test_ordered_emission_hold_ignition_burn_and_disappearance(self):
        for t,first,last in ((.3,0,11),(.48,12,19),(.6,20,31),(.8,32,39),(.9,40,47)):
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
        for t in (.0,.1,.3):
            pet.elapsed=pet.duration*t
            self.assertIn(pet.pose(),DRAGON_CLIPS['fire'])
        from app.behavior_art import EXTRA_CLIPS
        for t in (.52,.7,.99):
            pet.elapsed=pet.duration*t
            self.assertIn(pet.pose(),EXTRA_CLIPS['dragon']['ignition_reaction'])
        self.assertEqual(pet.pose(),EXTRA_CLIPS['dragon']['ignition_reaction'][-1])
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

    def test_windows_cloud_masks_avoid_expensive_checkerboard_regions(self):
        root=Path(__file__).resolve().parents[1]
        with Image.open(root/'assets/runtime/dragon-windows/cloud-flame.png') as sheet:
            for i in range(48):
                mask=sheet.crop((i%4*240,i//4*240,(i%4+1)*240,(i//4+1)*240)).getchannel('A').tobytes()
                transitions=sum(a!=b for a,b in zip(mask,mask[1:]))
                self.assertLess(transitions,1800)
