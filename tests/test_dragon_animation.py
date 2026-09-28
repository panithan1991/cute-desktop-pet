import random
import unittest

from app.dragon_animation import DRAGON_CLIPS, DRAGON_POSES, DragonBehavior
from app.pet_motion import BibiFlightMotion
from app.behavior_art import EXTRA_CLIPS


class DragonTests(unittest.TestCase):
    def test_threat_roar_and_stationary_lightning_have_reachable_frames_and_cooldowns(self):
        dragon = DragonBehavior(random.Random(6))
        for state in ("threat", "roar", "storm_hover"):
            dragon.force(state)
            while dragon.transition.active:
                dragon.step(.1)
            self.assertFalse(dragon.walking)
            reached = set()
            for i in range(400):
                dragon.elapsed = dragon.duration*i/399
                reached.add(dragon.pose())
            self.assertEqual(reached,set(EXTRA_CLIPS["dragon"][state]))
            frozen = (dragon.pose(), dragon.clock)
            dragon.step(.1,frozen=True)
            self.assertEqual(frozen,(dragon.pose(),dragon.clock))
            dragon.finish()
            self.assertEqual(dragon.state,"idle")
            self.assertEqual(dragon.memory.choose({state:1},dragon.clock),"idle")

    def test_all_100_frames_are_reachable_by_real_activities(self):
        dragon = DragonBehavior(random.Random(10))
        reached = set()
        for state in ("idle", "curious", "tail", "stretch", "smoke", "fire", "yawn", "sleep", "wake"):
            dragon.force(state)
            while dragon.transition.active:
                dragon.step(.1)
            for i in range(3000):
                dragon.elapsed = dragon.duration * i / 2999
                reached.add(dragon.pose())
        for flight, duration in (("takeoff", 2.4), ("cruise", 10), ("landing", 2.8)):
            for i in range(1000):
                reached.add(dragon.pose(flight, duration * i / 999))
        expected = set(DRAGON_POSES)-set(DRAGON_CLIPS["wake"])
        self.assertEqual(reached, expected | set(EXTRA_CLIPS["dragon"]["wake_stretch"]))

    def test_sleep_wakes_before_returning_to_idle_and_pause_freezes_effects(self):
        dragon = DragonBehavior(random.Random(3))
        dragon.force("sleep")
        while dragon.transition.active:
            dragon.step(.1)
        self.assertGreaterEqual(dragon.duration, 45)
        dragon.elapsed = 30
        self.assertIn(dragon.pose(), DRAGON_CLIPS["sleep"][5:])
        dragon.finish()
        self.assertEqual(dragon.state, "wake")
        dragon.finish()
        self.assertEqual(dragon.state, "idle")
        dragon.force("fire")
        dragon.elapsed = 1.5
        before = (dragon.pose(), dragon.elapsed)
        for _ in range(100):
            dragon.step(.1, frozen=True)
        self.assertEqual(before, (dragon.pose(), dragon.elapsed))

    def test_sleepy_dragon_hover_stays_in_work_area_and_lands(self):
        flight = BibiFlightMotion(300, 700, speed=55, auto_launch=False,
                                  altitude_range=(.72, .85), cruise_duration=10,
                                  rng=random.Random(8))
        flight.launch()
        points = []
        for _ in range(160):
            flight.step(.1, 0, 20, 900, 700)
            points.append((flight.x, flight.y))
        self.assertTrue(all(0 <= x <= 900 and 20 <= y <= 700 for x, y in points))
        self.assertLess(min(y for x, y in points), 600)
        self.assertEqual((flight.state, flight.y), ("rest", 700))
