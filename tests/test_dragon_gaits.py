import random
import unittest
from PIL import Image, ImageOps
from app.behavior_art import EXTRA_CLIPS
from app.dragon_animation import DragonBehavior
from app.pet_motion import PetMotion
from app.pet_sprites import POSES, atlas_path, CELL


class DragonGaitTests(unittest.TestCase):
    def ready(self, state):
        pet = DragonBehavior(random.Random(5))
        pet.force(state)
        while pet.transition.active:
            pet.step(.1)
        pet.elapsed = 1
        return pet

    def test_ground_travel_never_requests_flight_and_has_distinct_speeds(self):
        distances = []
        for state in ('ground_walk', 'run'):
            pet = self.ready(state); motion = PetMotion(400)
            for _ in range(10):
                pet.move_ground(motion, .1, 0, 2000)
            self.assertFalse(pet.walking)
            self.assertTrue(pet.grounded_travel)
            distances.append(motion.x-400)
            self.assertAlmostEqual(pet.ground_distance, motion.x-400)
        self.assertAlmostEqual(distances[1]/distances[0], 3)

    def test_pause_and_painted_connections_prevent_translation(self):
        pet = DragonBehavior(random.Random(4)); motion = PetMotion(400)
        pet.force('ground_walk')
        self.assertEqual(pet.transition.queue[0][0], 'ground_ready')
        pet.move_ground(motion, .1, 0, 1000)
        self.assertEqual(motion.x, 400)
        while pet.transition.active: pet.step(.1)
        motion.paused = True
        before = (pet.pose(), pet.clock, pet.ground_distance)
        pet.step(.1, frozen=True); pet.move_ground(motion, .1, 0, 1000)
        self.assertEqual(before, (pet.pose(), pet.clock, pet.ground_distance))
        self.assertEqual(motion.x, 400)
        pet.finish()
        self.assertEqual(pet.transition.queue[-1][0], 'ground_ready')
        self.assertTrue(pet.transition.queue[-1][1])

    def test_stride_depends_on_distance_and_edge_turn_waits_for_exit(self):
        pet = self.ready('ground_walk'); motion = PetMotion(999.9)
        pet.move_ground(motion, .1, 0, 1000)
        self.assertTrue(pet.turn_pending)
        self.assertEqual(motion.direction, 1)
        self.assertEqual(pet.state, 'idle')
        self.assertLessEqual(motion.x, 1000)
        pet = self.ready('run')
        pet.ground_distance = 18; a = pet.pose()
        pet.elapsed += 3
        self.assertEqual(a, pet.pose())
        pet.ground_distance += 72
        self.assertEqual(a, pet.pose())

    def test_gait_and_sitting_endpoints_share_identical_pixels(self):
        poses = POSES['dragon']
        with Image.open(atlas_path('dragon', 1, 'darwin')) as sheet:
            def pixels(pose):
                i = poses.index(pose)
                return sheet.crop((i%5*CELL,i//5*CELL,(i%5+1)*CELL,(i//5+1)*CELL)).tobytes()
            ready = EXTRA_CLIPS['dragon']['ground_ready']
            self.assertEqual(pixels(ready[0]), pixels('dragon_idle_00'))
            for state in ('ground_walk', 'run'):
                clip = EXTRA_CLIPS['dragon'][state]
                self.assertEqual(pixels(ready[-1]), pixels(clip[0]))
                self.assertEqual(pixels(clip[0]), pixels(clip[-1]))

    def test_both_new_behaviors_can_be_selected(self):
        pet = DragonBehavior(random.Random(42)); seen = set()
        for _ in range(800):
            seen.add(pet.state)
            pet.clock += 50
            pet.transition.queue = []
            pet.finish()
        self.assertTrue({'ground_walk', 'run'}.issubset(seen))

    def test_repaired_running_frames_are_uncropped_and_mirrored(self):
        with Image.open(atlas_path('dragon', 1, 'darwin')) as right, \
                Image.open(atlas_path('dragon', -1, 'darwin')) as left:
            for pose in EXTRA_CLIPS['dragon']['run']:
                index = POSES['dragon'].index(pose)
                box = (index % 5*CELL, index // 5*CELL,
                       index % 5*CELL+CELL, index // 5*CELL+CELL)
                frame = right.crop(box)
                bounds = frame.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()
                self.assertIsNotNone(bounds, pose)
                self.assertGreaterEqual(min(bounds[0], bounds[1], CELL-bounds[2], CELL-bounds[3]), 6, pose)
                self.assertEqual(ImageOps.mirror(frame).tobytes(), left.crop(box).tobytes(), pose)

    def test_interrupted_ground_entry_preserves_current_painted_pose(self):
        pet = DragonBehavior(random.Random(3))
        pet.force('ground_walk')
        pet.step(.1); pet.step(.1)
        before = pet.pose()
        pet.force('fire')
        self.assertEqual(pet.pose(), before)
