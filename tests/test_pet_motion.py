import unittest

from pet_motion import FlightMotion, JumpMotion, PetMotion


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


class JumpMotionTests(unittest.TestCase):
    def test_jump_rises_then_lands(self):
        jump = JumpMotion()
        self.assertTrue(jump.jump())
        self.assertFalse(jump.jump())
        jump.step(0.1, 500)
        self.assertGreater(jump.height, 0)
        for _ in range(20):
            jump.step(0.05, 500)
        self.assertEqual((jump.height, jump.velocity), (0, 0))

    def test_jump_respects_top_of_screen(self):
        jump = JumpMotion()
        jump.jump()
        for _ in range(5):
            jump.step(0.05, 18)
        self.assertLessEqual(jump.height, 18)


class FlightMotionTests(unittest.TestCase):
    def test_flight_moves_in_two_dimensions_and_reflects_at_edges(self):
        ship = FlightMotion(x=94, y=2, dx=1, dy=-1, speed=100)
        ship.step(0.1, 0, 0, 100, 100)
        self.assertEqual((ship.x, ship.y), (100, 0))
        self.assertLess(ship.dx, 0)
        self.assertGreater(ship.dy, 0)
        ship.step(0.1, 0, 0, 100, 100)
        self.assertLess(ship.x, 100)
        self.assertGreater(ship.y, 0)

    def test_paused_ship_keeps_both_coordinates(self):
        ship = FlightMotion(x=40, y=60, paused=True)
        ship.step(0.1, 0, 0, 100, 100)
        self.assertEqual((ship.x, ship.y), (40, 60))


if __name__ == "__main__":
    unittest.main()
