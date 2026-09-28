import unittest
from pathlib import Path

from PIL import Image

from app.dragon_lightning import STORM_FRAMES, STRIKES, flash_at
from test_behavior_art import frame


class LightningTests(unittest.TestCase):
    def test_twelve_short_strikes_have_dark_gaps_and_fast_decay(self):
        for start, length in STRIKES:
            self.assertEqual(flash_at(start-1)[1],0)
            self.assertEqual(flash_at(start+length)[1],0)
            self.assertGreater(flash_at(start+1)[1],flash_at(start)[1])
            self.assertLess(flash_at(start+2)[1],flash_at(start+1)[1])
            self.assertLessEqual(length*9/(STORM_FRAMES-1),.27)
        layers = Image.open(Path(__file__).resolve().parents[1] /
                            "assets/source/dragon-lightning-layers.png").convert("RGBA")
        active = [bool(frame(layers,i).getchannel("A").getbbox()) for i in range(STORM_FRAMES)]
        self.assertEqual(active,[flash_at(i)[1] > 0 for i in range(STORM_FRAMES)])
        self.assertEqual(sum(a and not active[i-1] for i,a in enumerate(active) if i),12)

