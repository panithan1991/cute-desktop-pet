import unittest
from pathlib import Path
from struct import unpack

from booboo_art import CELL_SIZE, POSES, choose_pose


class BooBooPoseTests(unittest.TestCase):
    def test_all_six_poses_are_present(self):
        self.assertEqual(
            set(POSES), {"idle", "smile", "happy", "curious", "hop", "sleepy"}
        )

    def test_sprite_sheet_has_six_transparent_png_cells(self):
        sheet = Path(__file__).resolve().parents[1] / "assets" / "booboo-sprites.png"
        header = sheet.read_bytes()[:26]
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(unpack(">II", header[16:24]), (3 * CELL_SIZE, 2 * CELL_SIZE))
        self.assertEqual(header[25], 6)  # RGBA; required by the clear desktop overlay

    def test_hop_wins_over_blink_and_rest(self):
        self.assertEqual(
            choose_pose(1, walking=True, airborne=True, blink=True,
                        resting_remaining=2, paused=False),
            "hop",
        )

    def test_blink_and_rest_have_distinct_expressions(self):
        self.assertEqual(
            choose_pose(1, walking=False, airborne=False, blink=True,
                        resting_remaining=2, paused=False),
            "smile",
        )
        self.assertEqual(
            choose_pose(1, walking=False, airborne=False, blink=False,
                        resting_remaining=2, paused=False),
            "curious",
        )
        self.assertEqual(
            choose_pose(1, walking=False, airborne=False, blink=False,
                        resting_remaining=.4, paused=False),
            "sleepy",
        )

    def test_pause_is_sleepy(self):
        self.assertEqual(
            choose_pose(1, walking=False, airborne=False, blink=False,
                        resting_remaining=0, paused=True),
            "sleepy",
        )


if __name__ == "__main__":
    unittest.main()
