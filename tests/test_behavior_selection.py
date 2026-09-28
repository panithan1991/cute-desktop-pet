import random
import unittest

from app.behavior_selection import Activity, BehaviorMemory
from app.dragon_animation import DragonBehavior
from app.pet_animation import resting_pose
from app.pet_behavior import PetBehavior
from app.animation_clips import CLIPS


class BehaviorSelectionTests(unittest.TestCase):
    def test_recent_actions_remain_in_memory_across_neutral_rests(self):
        actions = {"idle": Activity("Rest", (10, 20)),
                   "fire": Activity("Flame", (3, 4), 120),
                   "tail": Activity("Tail", (4, 6), 30)}
        memory = BehaviorMemory(random.Random(3), actions)
        memory.record("fire", 10)
        memory.record("idle", 20)
        for _ in range(100):
            self.assertEqual(memory.choose({"fire": 1000, "tail": 1}, 30), "tail")
        self.assertEqual(list(memory.recent), ["fire"])
        self.assertTrue(any(memory.choose({"fire": 1000, "tail": 1}, 131) == "fire"
                            for _ in range(20)))

    def test_belly_up_and_roll_share_a_play_cooldown(self):
        pet = PetBehavior("kitten", random.Random(2))
        pet.force("roll")
        pet.clock += pet.duration
        pet.finish()
        self.assertEqual(pet.state, "lounge")
        for _ in range(100):
            self.assertEqual(pet.memory.choose({"roll": 100, "belly_up": 100, "idle": 1}, pet.clock), "idle")

    def test_ground_sleep_and_play_end_in_matching_lying_posture(self):
        for state in ("sleep", "roll", "belly_up"):
            pet = PetBehavior("bunny", random.Random(4))
            pet.force(state)
            pet.finish()
            self.assertEqual(pet.state, "lounge")
            self.assertEqual(resting_pose(pet.state, 0, pet.duration), CLIPS["sleep"][0])
        pet.force("walk")
        self.assertEqual(pet.phase, "enter")
        low = pet.pace
        pet.elapsed = 2
        self.assertEqual(pet.phase, "loop")
        self.assertGreater(pet.pace, low)
        pet.elapsed = pet.duration - .1
        self.assertEqual(pet.phase, "exit")
        self.assertLess(pet.pace, low * 2)

    def test_dragon_does_not_repeat_last_action_after_every_idle_break(self):
        dragon = DragonBehavior(random.Random(12))
        actions = []
        for _ in range(300):
            if dragon.state not in {"idle", "wake"}:
                actions.append(dragon.state)
            dragon.clock += dragon.duration
            dragon.finish()
        self.assertGreaterEqual(len(set(actions)), 7)
        repeats = sum(a == b for a, b in zip(actions, actions[1:]))
        self.assertLess(repeats, len(actions) * .12)

    def test_flight_clock_advances_cooldowns_without_changing_activity(self):
        for pet in (PetBehavior("bibi", random.Random(1)), DragonBehavior(random.Random(1))):
            pet.force("walk")
            pet.step(.1, advance_state=False)
            self.assertEqual(pet.elapsed, 0)
            self.assertAlmostEqual(pet.clock, .1)
            pet.step(.1, frozen=True, advance_state=False)
            self.assertAlmostEqual(pet.clock, .1)
