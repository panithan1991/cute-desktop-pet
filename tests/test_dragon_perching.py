import random
import unittest
from pathlib import Path
from PIL import Image, ImageOps
from app.dragon_aerobatics import DragonFlightMotion
from app.dragon_animation import DragonBehavior
from app.dragon_personality import PERCH_POWERS, PERCH_CLIPS
from app.behavior_art import EXTRA_CLIPS
from app.pet_sprites import POSES

ROOT=Path(__file__).resolve().parents[1]


class DragonPerchingTests(unittest.TestCase):
    def test_direct_dragon_startup_has_a_safe_perch_default(self):
        f=DragonFlightMotion(450,680,auto_launch=False)
        self.assertIsNone(f.perch_side)
        f.mode='perch_landing';f.state='cruise'
        self.assertIsNone(f.perch_pose(DragonBehavior()))

    def test_all_three_edges_require_real_contact_then_grip_and_depart(self):
        for side in ('left','right','top'):
            f=DragonFlightMotion(450,240,auto_launch=False,rng=random.Random(5))
            f.mode='walk';f.state='cruise';f.elapsed=.2;f.cruise_duration=100
            f.direction=-1 if side=='left' else 1
            f.climb=-100 if side=='top' else 0
            if side=='top':f.x=450;f.y=26
            elif side=='left':f.x=1
            else:f.x=949
            self.assertIsNone(f.perch_pose(DragonBehavior()))
            for _ in range(5):
                f.step(.1,0,25,950,680)
                if f.state=='grabbing':break
                self.assertIsNone(f.perch_pose(DragonBehavior()))
            self.assertEqual(f.state,'grabbing');self.assertEqual(f.perch_side,side)
            contact=(f.x,f.y)
            for _ in range(17):f.step(.1,0,25,950,680)
            self.assertEqual(f.state,'perched');self.assertEqual((f.x,f.y),contact)
            before=(f.x,f.y,f.elapsed);f.paused=True;f.step(.1,0,25,950,680)
            self.assertEqual(before,(f.x,f.y,f.elapsed));f.paused=False
            f.depart()
            for _ in range(50):f.step(.1,0,25,950,680)
            self.assertEqual(f.state,'rest');self.assertEqual(f.y,680)

    def test_flying_in_open_space_never_displays_a_stationary_grip(self):
        f=DragonFlightMotion(450,400,auto_launch=False,rng=random.Random(9))
        f.mode='perch_landing';f.state='cruise';f.cruise_duration=50
        pet=DragonBehavior()
        for _ in range(20):
            self.assertIsNone(f.perch_pose(pet))
            before=(f.x,f.y);f.step(.1,0,25,2000,680)
            self.assertGreater(abs(f.x-before[0]),0)
            self.assertGreater(abs(f.y-before[1]),0)
            self.assertEqual(f.state,'cruise')

    def test_each_perch_selects_exactly_one_power_then_finishes(self):
        pet=DragonBehavior(random.Random(21));reached=set()
        for _ in range(120):
            pet.begin_perch();reached.add(pet.state)
            self.assertIn(pet.state,PERCH_POWERS)
            self.assertFalse(pet.transition.active)
            pet.clock+=pet.duration;pet.finish()
            self.assertEqual(pet.state,'idle')
            self.assertFalse(pet.transition.active)
            pet.perched=False
        self.assertEqual(reached,PERCH_POWERS)

    def test_grip_remains_at_body_clip_boundary_and_downward_cones_match(self):
        with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
            def frame(pose):
                i=POSES['dragon'].index(pose)
                return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160))
            for name in PERCH_CLIPS:
                poses=EXTRA_CLIPS['dragon'][name]
                self.assertEqual(len(poses),40)
                self.assertEqual(frame(poses[12]).tobytes(),frame(poses[-1]).tobytes())
                self.assertNotEqual(frame(poses[12]).tobytes(),frame(poses[20]).tobytes())
        for platform in ('macos','windows'):
            root=ROOT/f'assets/runtime/dragon-{platform}/fx'
            for side in ('left','right'):
                for i in range(16):
                    with Image.open(root/f'roar-cone-{side}/{i:02d}.png') as up,Image.open(root/f'roar-down-{side}/{i:02d}.png') as down:
                        self.assertEqual(ImageOps.flip(up).tobytes(),down.tobytes())

    def test_special_air_maneuver_contact_also_grips_the_edge(self):
        f=DragonFlightMotion(949,240,auto_launch=False)
        f.state='cruise';f.mode='dive_recover';f.direction=1
        f.cruise_duration=10;f.altitude=.3
        f.step(.1,0,25,950,680)
        self.assertEqual(f.state,'grabbing')
        self.assertEqual(f.perch_side,'right')

    def test_flight_join_endpoints_match_actual_wingbeat_and_landing(self):
        from app.dragon_animation import DRAGON_CLIPS
        root=ROOT/'assets/runtime/dragon-macos/body-fx/right'
        with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
            def body(pose):
                i=POSES['dragon'].index(pose)
                return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160)).tobytes()
            for phase,pose in enumerate(DRAGON_CLIPS['hover']):
                with Image.open(root/f'flight_join_{phase:02d}_00.png') as first,Image.open(root/f'flight_join_{phase:02d}_05.png') as last:
                    self.assertEqual(first.tobytes(),body(pose))
                    self.assertEqual(last.tobytes(),body(DRAGON_CLIPS['hover'][0]))
            with Image.open(root/'landing_join_00.png') as first,Image.open(root/'landing_join_05.png') as last:
                self.assertEqual(first.tobytes(),body(DRAGON_CLIPS['hover'][0]))
                self.assertEqual(last.tobytes(),body(DRAGON_CLIPS['landing'][0]))

    def test_touchdown_bridge_joins_ground_pose_to_idle_exactly(self):
        from app.dragon_animation import DRAGON_CLIPS
        root=ROOT/'assets/runtime/dragon-macos/body-fx/right'
        with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
            def pixels(pose):
                i=POSES['dragon'].index(pose)
                return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160)).tobytes()
            with Image.open(root/'touchdown_join_00.png') as first,Image.open(root/'touchdown_join_05.png') as last:
                self.assertEqual(first.tobytes(),pixels(DRAGON_CLIPS['landing'][-1]))
                self.assertEqual(last.tobytes(),pixels(DRAGON_CLIPS['idle'][0]))

    def test_interrupted_posture_transitions_preserve_the_displayed_frame(self):
        for source,target in (('sleep','fire'),('walk','sleep'),('ground_walk','fire')):
            pet=DragonBehavior(random.Random(10));pet.force(source)
            self.assertTrue(pet.transition.active)
            pet.transition.elapsed=pet.transition.queue[0][2]*.45
            before=pet.pose();pet.force(target)
            self.assertEqual(pet.pose(),before,(source,target))
            elapsed=pet.transition.elapsed
            pet.step(.1,frozen=True)
            self.assertEqual(pet.pose(),before)
            self.assertEqual(pet.transition.elapsed,elapsed)
            for _ in range(160):
                if not pet.transition.active:break
                pet.step(.1)
            self.assertFalse(pet.transition.active)

    def test_normal_flight_timeout_settles_wingbeat_before_landing(self):
        f=DragonFlightMotion(450,240,auto_launch=False)
        f.state='cruise';f.mode='walk';f.elapsed=.45;f.cruise_duration=.5
        f.climb=0
        f.step(.1,0,25,2000,680)
        self.assertEqual(f.state,'air_settle')
        for _ in range(5):f.step(.1,0,25,2000,680)
        self.assertEqual(f.state,'release_join')
        for _ in range(5):f.step(.1,0,25,2000,680)
        self.assertEqual(f.state,'landing')
