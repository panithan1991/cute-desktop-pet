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
        self.assertIsNotNone(f.perch_pose(DragonBehavior()))

    def test_all_three_edges_grip_pause_and_depart_without_teleporting(self):
        for side in ('left','right','top'):
            f=DragonFlightMotion(450,240,auto_launch=False,rng=random.Random(5))
            f.mode='perch_landing';f.state='cruise';f.cruise_duration=12;f.perch_side=side
            for _ in range(121):
                before=(f.x,f.y);f.step(.1,0,25,950,680)
                self.assertLess(abs(f.x-before[0]),15)
                self.assertLess(abs(f.y-before[1]),15)
            self.assertEqual(f.state,'perched')
            if side=='top':self.assertEqual(f.y,25)
            else:self.assertEqual(f.x,0 if side=='left' else 950)
            if side!='top':self.assertEqual(f.direction,1 if side=='left' else -1)
            before=(f.x,f.y,f.elapsed);f.paused=True;f.step(.1,0,25,950,680)
            self.assertEqual(before,(f.x,f.y,f.elapsed))
            f.paused=False
            for _ in range(100):f.step(.1,0,25,950,680)
            self.assertEqual((f.x,f.y),before[:2])
            f.depart()
            for _ in range(45):f.step(.1,0,25,950,680)
            self.assertEqual(f.state,'rest');self.assertEqual(f.y,680)

    def test_random_perched_routine_uses_only_requested_powers_and_rests(self):
        pet=DragonBehavior(random.Random(21));pet.perched=True;pet.force('idle')
        reached=set()
        for _ in range(120):
            pet.clock+=pet.duration;pet.finish();reached.add(pet.state)
            self.assertIn(pet.state,PERCH_POWERS|{'idle'})
            self.assertFalse(pet.transition.active)
        self.assertEqual(reached,PERCH_POWERS|{'idle'})

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
