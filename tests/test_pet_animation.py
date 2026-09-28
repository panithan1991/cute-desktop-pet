import unittest

from PIL import Image, ImageOps

from app.animation_clips import CLIPS
from app.animation_clips import ALL_POSES
from app.bibi_animation import choose_bibi_pose
from app.pet_animation import choose_pet_pose
from app.pet_sprites import CELL, POSES, atlas_path


def pose(character, **changes):
    state = dict(walking=False, walk_time=0.0, rest_progress=0.0,
                 rest_variant=0, airborne=False, jump_velocity=0.0,
                 landed=False, blink=False, paused=False, roll_progress=None)
    state.update(changes)
    return choose_pet_pose(character, **state)


class PetAnimationTests(unittest.TestCase):
    def test_ground_pets_reach_all_85_frames(self):
        for character in ("bunny", "mookrata", "kitten"):
            reached = set()
            for step in range(300):
                progress = step / 299
                reached.add(pose(character, rest_variant=1, rest_progress=progress))
                reached.add(pose(character, rest_variant=0, rest_progress=progress))
                reached.add(pose(character, walking=True, walk_time=step / 60))
                reached.add(pose(character, roll_progress=progress))
                reached.add(pose(character, airborne=True, jump_progress=progress))
            self.assertEqual(reached, set(ALL_POSES))

    def test_jump_sequence_follows_ascent_and_descent(self):
        for character in ("bunny", "mookrata", "kitten"):
            self.assertEqual(pose(character, airborne=True, jump_progress=0), CLIPS["hop"][0])
            self.assertEqual(pose(character, airborne=True, jump_progress=0.5), CLIPS["hop"][7])
            self.assertEqual(pose(character, landed=True), CLIPS["hop"][-1])
            self.assertEqual(pose(character, paused=True), CLIPS["sleep"][8])

    def test_atlases_have_85_unique_padded_frames_and_mirrored_facings(self):
        for character, keys in POSES.items():
            with self.subTest(character=character):
                expected = 485 if character == "dragon" else 195
                self.assertEqual(len(keys), expected)
                right = Image.open(atlas_path(character, 1, "darwin")).convert("RGBA")
                left = Image.open(atlas_path(character, -1, "darwin")).convert("RGBA")
                hard = Image.open(atlas_path(character, 1, "win32")).convert("RGBA")
                hard_left = Image.open(atlas_path(character, -1, "win32")).convert("RGBA")
                self.assertEqual(right.size, (5 * CELL, expected // 5 * CELL))
                self.assertEqual(left.size, right.size)
                self.assertEqual(hard.size, right.size)
                self.assertEqual(set(hard.getchannel("A").tobytes()), {0, 255})
                unique = set()
                for index in range(expected):
                    box = ((index % 5) * CELL, (index // 5) * CELL,
                           (index % 5 + 1) * CELL, (index // 5 + 1) * CELL)
                    frame = right.crop(box)
                    bounds = frame.getchannel("A").point(lambda a: 255 if a > 32 else 0).getbbox()
                    self.assertIsNotNone(bounds)
                    # Guard against the reported cropped head, wing, ear or paw.
                    self.assertGreaterEqual(min(bounds[0], bounds[1], CELL-bounds[2], CELL-bounds[3]), 6,
                                            f"{character}: clipped frame {index}")
                    unique.add(frame.tobytes())
                    self.assertEqual(ImageOps.mirror(frame).tobytes(), left.crop(box).tobytes())
                    self.assertEqual(ImageOps.mirror(hard.crop(box)).tobytes(), hard_left.crop(box).tobytes())
                # Reused exact endpoints keep the joining poses identical.
                self.assertGreaterEqual(len(unique), expected-35)

    def test_bibi_uses_flight_and_rest_clips_without_forced_play_after_every_nap(self):
        reached = set()
        for state, duration in (("takeoff", 2.4), ("cruise", 30), ("landing", 2.8)):
            for step in range(1000):
                reached.add(choose_bibi_pose(state, duration * step / 999))
        self.assertTrue(set(CLIPS["walk"] + CLIPS["hop"]).issubset(reached))
        for step in range(1000):
            reached.add(choose_bibi_pose("rest", 0, rest_state="roll",
                                         rest_elapsed=6 * step / 999, rest_duration=6))
        self.assertTrue(set(CLIPS["roll"]).issubset(reached))
        self.assertIn(choose_bibi_pose("rest", 80, rest_state="sleep",
                                      rest_elapsed=40, rest_duration=80), CLIPS["sleep"][8:11])


if __name__ == "__main__":
    unittest.main()
