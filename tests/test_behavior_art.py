import random
import unittest

from PIL import Image

from app.animation_clips import ALL_POSES
from app.behavior_art import EXTRA_CLIPS, EXTRA_POSES, SIGNATURES, PostureTransition
from app.dragon_animation import DRAGON_CLIPS, DRAGON_POSES, DragonBehavior
from app.pet_behavior import PetBehavior
from app.pet_sprites import POSES, atlas_path, CELL


def frame(image, index):
    return image.crop((index%5*CELL,index//5*CELL,(index%5+1)*CELL,(index//5+1)*CELL))


class PaintedBehaviorTests(unittest.TestCase):
    def test_connecting_clip_endpoints_are_pixel_identical_to_joined_poses(self):
        for character, poses in POSES.items():
            image = Image.open(atlas_path(character,1,"darwin")).convert("RGBA")
            idle = poses.index("dragon_idle_00" if character == "dragon" else "idle_00")
            sleep = poses.index(DRAGON_CLIPS["sleep"][-1] if character == "dragon" else "sleep_14")
            travel = poses.index("dragon_takeoff_00" if character == "dragon" else
                                 "hop_00" if character == "bibi" else "walk_00")
            for clip, a, b in (("wake_stretch",sleep,idle),("travel_ready",idle,travel)):
                keys = EXTRA_CLIPS[character][clip]
                self.assertEqual(frame(image,poses.index(keys[0])).tobytes(),frame(image,a).tobytes())
                self.assertEqual(frame(image,poses.index(keys[-1])).tobytes(),frame(image,b).tobytes())

    def test_no_walking_during_waking_and_turning_and_signature_frames_are_reachable(self):
        for character in SIGNATURES:
            pet = DragonBehavior(random.Random(4)) if character == "dragon" else PetBehavior(character,random.Random(4))
            for state in SIGNATURES[character]:
                pet.force(state)
                while pet.transition.active:
                    self.assertFalse(pet.walking)
                    pet.step(.1)
                clip = EXTRA_CLIPS[character][state]
                reached = set()
                for i in range(500):
                    pet.elapsed = pet.duration*i/499
                    reached.add(pet.pose())
                self.assertEqual(reached,set(clip))
            pet.force("walk")
            while pet.transition.active:
                self.assertFalse(pet.walking)
                pet.step(.1)
            self.assertTrue(pet.walking)

    def test_lying_to_travel_routes_wake_then_turn_and_freezes_when_paused(self):
        pet = PetBehavior("bunny",random.Random(2))
        pet.force("lounge")
        while pet.transition.active:
            pet.step(.1)
        pet.force("walk")
        self.assertEqual([part[0] for part in pet.transition.queue],["wake_stretch","travel_ready"])
        before = (pet.pose(),pet.transition.elapsed,pet.clock)
        for _ in range(100):
            pet.step(.1,frozen=True)
        self.assertEqual(before,(pet.pose(),pet.transition.elapsed,pet.clock))

    def test_every_species_can_select_all_its_signatures_without_foreign_gestures(self):
        for character in SIGNATURES:
            pet = DragonBehavior(random.Random(42)) if character == "dragon" else PetBehavior(character,random.Random(42))
            visited = set()
            for _ in range(1500):
                visited.add(pet.state)
                pet.clock += pet.duration+10
                pet.transition.queue = []
                pet.finish()
            self.assertTrue(set(SIGNATURES[character]).issubset(visited))
            foreign = set().union(*(set(v) for c,v in SIGNATURES.items() if c != character))
            self.assertFalse(visited & foreign)
