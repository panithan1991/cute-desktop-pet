import unittest

from PIL import Image

from app.behavior_art import EXTRA_CLIPS
from app.dragon_animation import DRAGON_CLIPS
from app.pet_sprites import POSES, atlas_path
from test_behavior_art import frame


class DragonEffectTests(unittest.TestCase):
    def test_effect_clips_return_to_exact_neutral_pose_without_edge_residue(self):
        poses = POSES["dragon"]
        image = Image.open(atlas_path("dragon", 1, "darwin")).convert("RGBA")
        idle = frame(image, poses.index("dragon_idle_00"))
        for names in (DRAGON_CLIPS["smoke"], DRAGON_CLIPS["fire"],
                      EXTRA_CLIPS["dragon"]["hiccup"]):
            self.assertEqual(frame(image, poses.index(names[0])).tobytes(), idle.tobytes())
            self.assertEqual(frame(image, poses.index(names[-1])).tobytes(), idle.tobytes())
            # Beyond the resting body: emission must become visible, then fade
            # over intermediate frames rather than disappearing in one step.
            masses = [sum(frame(image, poses.index(name)).getchannel("A")
                          .crop((132, 15, 154, 130)).histogram()[a] * a / 255
                          for a in range(256)) for name in names]
            self.assertEqual(masses[0], 0)
            self.assertEqual(masses[-1], 0)
            peak = max(masses)
            self.assertGreater(peak, 1)
            self.assertGreaterEqual(sum(0 < m < peak * .9 for m in masses), 3)


if __name__ == "__main__":
    unittest.main()
