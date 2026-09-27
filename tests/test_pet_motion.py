import unittest

from pet_motion import PetMotion


class PetMotionTests(unittest.TestCase):
    def test_turns_around_at_both_edges(self):
        pet = PetMotion(x=96, speed=50)
        pet.step(0.1, 0, 100)
        self.assertEqual((pet.x, pet.direction), (100, -1))
        pet.x = 2
        pet.step(0.1, 0, 100)
        self.assertEqual((pet.x, pet.direction), (0, 1))

    def test_pause_keeps_position(self):
        pet = PetMotion(x=40, paused=True)
        pet.step(0.1, 0, 100)
        self.assertEqual(pet.x, 40)

    def test_resume_does_not_jump_across_screen(self):
        pet = PetMotion(x=20, speed=100)
        pet.step(60, 0, 100)
        self.assertEqual(pet.x, 30)

    def test_dragged_position_is_clamped_into_work_area(self):
        pet = PetMotion(x=200, paused=True)
        pet.step(0, 10, 100)
        self.assertEqual(pet.x, 100)


if __name__ == "__main__":
    unittest.main()
