import unittest
from pathlib import Path
from struct import unpack
import zlib

from booboo_art import CELL_SIZE, DISPLAY_SCALE, POSES, _display_png, _read_rgba_png, choose_pose


SHEET = Path(__file__).resolve().parents[1] / "assets" / "booboo-sprites.png"


def pose(**changes):
    state = dict(now=1.0, walking=False, airborne=False, jump_velocity=0.0,
                 just_landed=False, blink=False, resting_remaining=0.0, paused=False)
    state.update(changes)
    return choose_pose(**state)


class BooBooPoseTests(unittest.TestCase):
    def test_all_nine_distinct_poses_are_present(self):
        self.assertEqual(set(POSES), {
            "idle", "smile", "happy", "curious", "hop_start", "hop_air",
            "hop_land", "stretch", "sleepy",
        })
        self.assertEqual(len(set(POSES.values())), 9)

    def test_sprite_sheet_has_nine_transparent_png_cells(self):
        header = SHEET.read_bytes()[:26]
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(unpack(">II", header[16:24]), (3 * CELL_SIZE, 3 * CELL_SIZE))
        self.assertEqual(header[25], 6)

    def test_hop_animates_takeoff_air_and_landing(self):
        self.assertEqual(pose(airborne=True, jump_velocity=245, blink=True), "hop_start")
        self.assertEqual(pose(airborne=True, jump_velocity=0), "hop_air")
        self.assertEqual(pose(airborne=True, jump_velocity=-245), "hop_land")
        self.assertEqual(pose(just_landed=True), "hop_land")

    def test_idle_and_rest_have_distinct_expressions(self):
        self.assertEqual(pose(), "idle")
        self.assertEqual(pose(walking=True, now=0.2), "happy")
        self.assertEqual(pose(blink=True), "smile")
        self.assertEqual(pose(resting_remaining=6.0), "curious")
        self.assertEqual(pose(resting_remaining=3.5), "stretch")
        self.assertEqual(pose(resting_remaining=1.5), "sleepy")
        self.assertEqual(pose(resting_remaining=6.0, blink=True), "curious")
        self.assertEqual(pose(paused=True, airborne=True), "sleepy")

    def test_display_frame_has_only_clear_or_opaque_alpha(self):
        width, height, pixels = _read_rgba_png(SHEET)
        self.assertEqual((width, height), (3 * CELL_SIZE, 3 * CELL_SIZE))
        png = _display_png(pixels, width, *POSES["hop_air"])
        self.assertEqual(unpack(">II", png[16:24]),
                         ((CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE,) * 2)
        idat = png.index(b"IDAT")
        length = unpack(">I", png[idat - 4:idat])[0]
        raw = zlib.decompress(png[idat + 4:idat + 4 + length])
        size = (CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE
        alphas = set()
        for row in range(size):
            start = row * (1 + size * 4)
            self.assertEqual(raw[start], 0)
            alphas.update(raw[start + 4:start + 1 + size * 4:4])
        self.assertEqual(alphas, {0, 255})


if __name__ == "__main__":
    unittest.main()
