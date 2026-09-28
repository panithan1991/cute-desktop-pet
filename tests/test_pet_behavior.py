import random
import unittest

from app.animation_clips import CLIPS
from app.pet_animation import resting_pose
from app.pet_behavior import PetBehavior


class PetBehaviorTests(unittest.TestCase):
    def test_long_varied_activities_for_all_four_pets(self):
        for character in ("bunny", "mookrata", "kitten", "bibi"):
            pet = PetBehavior(character, random.Random(54))
            pairs, durations, tilted = set(), set(), 0
            for _ in range(200):
                old = pet.state
                if old == "walk":
                    self.assertGreaterEqual(pet.duration, 18)
                if old == "sleep":
                    self.assertGreaterEqual(pet.duration, 40)
                tilted += pet.variant == 3
                durations.add(round(pet.duration, 1))
                pet.clock += pet.duration
                pet.finish()
                self.assertNotEqual(pet.state, old)
                pairs.add((old, pet.state))
            self.assertGreaterEqual(len(pairs), 8)
            self.assertGreater(len(durations), 50)
            self.assertLess(tilted, 30)

    def test_pause_and_drag_do_not_use_up_activity_time(self):
        pet = PetBehavior("bunny", random.Random(5))
        before = (pet.state, pet.elapsed, pet.clock, pet.duration)
        for _ in range(1000):
            pet.step(0.1, frozen=True)
        self.assertEqual(before, (pet.state, pet.elapsed, pet.clock, pet.duration))
        pet.step(3600)
        self.assertAlmostEqual(pet.elapsed, 0.1)

    def test_nap_stays_asleep_until_its_wake_up_transition(self):
        for duration in (40, 60, 90):
            middle = {resting_pose("sleep", step / 10, duration, blink=True)
                      for step in range(30, int((duration - 3) * 10))}
            self.assertEqual(middle, set(CLIPS["sleep"][8:11]))
            self.assertEqual(resting_pose("sleep", 0, duration), CLIPS["sleep"][0])
            self.assertEqual(resting_pose("sleep", duration, duration), CLIPS["sleep"][-1])

    def test_head_tilt_is_a_single_small_excursion_with_long_neutral_holds(self):
        neutral = {resting_pose("idle", step / 10, 30, variant=1) for step in range(300)}
        self.assertEqual(neutral, {CLIPS["idle"][0]})
        curious = [resting_pose("idle", step / 10, 30, variant=3) for step in range(300)]
        self.assertTrue(set(curious).issubset(set(CLIPS["idle"][:4])))
        self.assertGreater(curious.count(CLIPS["idle"][0]), 240)

    def test_ground_pets_run_occasionally_with_smooth_acceleration(self):
        for character in ("bunny", "mookrata", "kitten", "bibi"):
            pet = PetBehavior(character, random.Random(21))
            runs = []
            for _ in range(500):
                pet.force("walk")
                if pet.run_start is not None:
                    runs.append(pet.clock)
                    pet.elapsed = pet.run_start
                    self.assertEqual(pet.pace, pet.base_pace)
                    pet.elapsed += 0.3
                    self.assertGreater(pet.pace, pet.base_pace)
                    self.assertLess(pet.pace, 1.65)
                    pet.elapsed = pet.run_start + pet.run_duration / 2
                    self.assertAlmostEqual(pet.pace, 1.65)
                    pet.elapsed = pet.run_start + pet.run_duration
                    self.assertEqual(pet.pace, pet.base_pace)
                pet.clock += pet.duration
            if character == "bibi":
                self.assertEqual(runs, [])
            else:
                self.assertGreater(len(runs), 10)
                self.assertLess(len(runs), 100)
                self.assertTrue(all(b - a >= 120 for a, b in zip(runs, runs[1:])))


if __name__ == "__main__":
    unittest.main()
