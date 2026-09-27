import unittest

from PIL import Image, ImageOps

from app.pet_animation import choose_pet_pose
from app.pet_sprites import CELL, POSES, atlas_path


def pose(character, **changes):
    state = dict(walking=False, walk_time=0.0, rest_progress=0.0,
                 rest_variant=0, airborne=False, jump_velocity=0.0,
                 landed=False, blink=False, paused=False, roll_progress=None)
    state.update(changes)
    return choose_pet_pose(character, **state)


class PetAnimationTests(unittest.TestCase):
    def test_each_pet_has_25_distinct_reachable_poses(self):
        for character, keys in POSES.items():
            with self.subTest(character=character):
                self.assertEqual(len(keys), 25)
                self.assertEqual(len(set(keys)), 25)
                reached = set()
                for variant in range(3):
                    for step in range(100):
                        reached.add(pose(character, rest_variant=variant,
                                         rest_progress=step / 100))
                for step in range(100):
                    reached.add(pose(character, walking=True, walk_time=step / 30))
                for velocity in (-200, 200):
                    reached.add(pose(character, airborne=True, jump_velocity=velocity))
                reached.add(pose(character, landed=True))
                reached.add(pose(character, paused=True))
                reached.add(pose(character, blink=True))
                if character == "bunny":
                    for step in range(100):
                        reached.add(pose(character, roll_progress=step / 100))
                self.assertEqual(reached, set(keys))

    def test_jump_and_landing_are_ordered(self):
        self.assertEqual(pose("bunny", airborne=True, jump_velocity=245), "hop_up")
        self.assertEqual(pose("bunny", airborne=True, jump_velocity=-245), "hop_air")
        self.assertEqual(pose("bunny", landed=True), "crouch")
        self.assertEqual(pose("mookrata", airborne=True, jump_velocity=300), "hop")
        self.assertEqual(pose("mookrata", airborne=True, jump_velocity=-300), "hop_two")
        self.assertEqual(pose("mookrata", landed=True), "land")

    def test_atlases_have_25_clear_frames_and_correct_left_facing(self):
        for character in POSES:
            with self.subTest(character=character):
                right = Image.open(atlas_path(character, 1, "darwin")).convert("RGBA")
                left = Image.open(atlas_path(character, -1, "darwin")).convert("RGBA")
                hard = Image.open(atlas_path(character, 1, "win32")).convert("RGBA")
                self.assertEqual(right.size, (5 * CELL, 5 * CELL))
                self.assertEqual(left.size, right.size)
                self.assertEqual(hard.size, right.size)
                self.assertEqual(set(hard.getchannel("A").tobytes()), {0, 255})
                for index in range(25):
                    box = ((index % 5) * CELL, (index // 5) * CELL,
                           (index % 5 + 1) * CELL, (index // 5 + 1) * CELL)
                    frame = right.crop(box)
                    self.assertIsNotNone(frame.getchannel("A").getbbox())
                    self.assertEqual(ImageOps.mirror(frame).tobytes(), left.crop(box).tobytes())


if __name__ == "__main__":
    unittest.main()
