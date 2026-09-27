import unittest

from power_effects import (
    AutoPowerTimer,
    EFFECT_LINGER_SECONDS,
    POWER_STYLES,
    SPECIAL_POWERS,
    PowerEffectView,
    launch_power,
)
from make_preview import SvgCanvas


class PowerEffectTests(unittest.TestCase):
    def test_auto_timer_supports_three_five_and_six_second_intervals(self):
        timer = AutoPowerTimer(5, 105)
        self.assertFalse(timer.due(104.99))
        self.assertTrue(timer.due(105))
        self.assertFalse(timer.due(109.99))
        self.assertTrue(timer.due(110))
        for seconds in (3, 5, 6):
            with self.subTest(seconds=seconds):
                timer.reset(200, seconds)
                self.assertFalse(timer.due(200 + seconds - 0.01))
                self.assertTrue(timer.due(200 + seconds))
                self.assertFalse(timer.due(200 + seconds))
        with self.assertRaises(ValueError):
            timer.reset(200, 4)

    def test_delayed_timer_casts_once_without_backlog(self):
        timer = AutoPowerTimer(3, 103)
        self.assertTrue(timer.due(120))
        self.assertFalse(timer.due(120))
        self.assertEqual(timer.next_at, 123)

    def test_every_character_launches_a_distinct_power_from_its_art(self):
        self.assertEqual(len(POWER_STYLES), 7)
        self.assertNotIn("bunny", POWER_STYLES)
        with self.assertRaises(ValueError):
            launch_power("bunny", 300, 400, facing=1)
        for character, style in POWER_STYLES.items():
            with self.subTest(character=character):
                effect = launch_power(character, 300, 400, facing=1)
                self.assertEqual(effect.kind, style.kind)
                self.assertEqual(effect.x + effect.width / 2, 300 + style.origin_x)
                self.assertEqual(effect.y + effect.height / 2, 400 + style.origin_y)

    def test_wizard_light_starts_at_staff_tip_and_tornado_drifts_left(self):
        bolt = launch_power("astral", 300, 400, facing=1)
        self.assertEqual((bolt.x + 32, bolt.y + 32, bolt.direction), (336, 425, -1))
        tornado = launch_power("astral", 300, 400, facing=1, special=True)
        self.assertEqual(tornado.kind, "tornado")
        self.assertGreater(tornado.height, bolt.height)
        first_x = tornado.x
        self.assertTrue(tornado.step(0.1, (0, 0, 1000, 1000)))
        self.assertLess(tornado.x, first_x)
        with self.assertRaises(ValueError):
            launch_power("cat", 300, 400, facing=1, special=True)

    def test_each_named_special_power_uses_its_own_effect(self):
        self.assertEqual(set(SPECIAL_POWERS), {"guardian", "moss", "astral", "ember"})
        for character, (kind, label) in SPECIAL_POWERS.items():
            with self.subTest(character=character):
                effect = launch_power(character, 300, 400, facing=1, special=True)
                self.assertEqual(effect.kind, kind)
                self.assertTrue(label)
                self.assertGreater(effect.lifetime, 0)
        self.assertEqual(
            launch_power("ember", 300, 400, facing=-1, special=True).direction, -1
        )

    def test_tree_visibly_grows_after_summoning(self):
        effect = launch_power("moss", 300, 400, facing=1, special=True)
        seed = SvgCanvas()
        PowerEffectView._draw_tree(seed, effect)
        effect.step(0.1, (0, 0, 1000, 1000))
        sapling = SvgCanvas()
        PowerEffectView._draw_tree(sapling, effect)
        self.assertGreater(len(sapling.parts), len(seed.parts))

    def test_fire_begins_at_the_helmet_and_specials_draw(self):
        right = launch_power("ember", 300, 400, facing=1, special=True)
        left = launch_power("ember", 300, 400, facing=-1, special=True)
        self.assertLessEqual(abs(right.x - (300 + 92)), 12)
        self.assertLessEqual(abs(left.x + left.width - (300 + 92)), 2)
        for character, renderer in (
            ("guardian", PowerEffectView._draw_lightning),
            ("ember", PowerEffectView._draw_fire),
            ("astral", PowerEffectView._draw_tornado),
        ):
            with self.subTest(character=character):
                canvas = SvgCanvas()
                renderer(canvas, launch_power(character, 300, 400, 1, special=True))
                self.assertGreater(len(canvas.parts), 3)

    def test_ship_fires_from_the_nose_in_either_direction(self):
        right = launch_power("ship", 300, 400, facing=-1, ship_dx=1)
        left = launch_power("ship", 300, 400, facing=1, ship_dx=-1)
        self.assertEqual((right.x + 32, right.direction), (465, 1))
        self.assertEqual((left.x + 32, left.direction), (319, -1))

    def test_every_power_lingers_four_seconds_after_its_animation(self):
        for character in POWER_STYLES:
            with self.subTest(character=character):
                effect = launch_power(character, 300, 400, facing=1)
                self.assertEqual(effect.linger_seconds, EFFECT_LINGER_SECONDS)
        for character in SPECIAL_POWERS:
            with self.subTest(special=character):
                effect = launch_power(character, 300, 400, facing=1, special=True)
                self.assertEqual(effect.linger_seconds, EFFECT_LINGER_SECONDS)

    def test_power_holds_position_then_expires_and_stays_visible_at_edge(self):
        effect = launch_power("guardian", 200, 300, facing=1)
        for _ in range(15):
            self.assertTrue(effect.step(0.1, (0, 0, 2000, 1000)))
        held_x = effect.x
        for _ in range(25):
            self.assertTrue(effect.step(0.1, (0, 0, 2000, 1000)))
            self.assertEqual(effect.x, held_x)
        effect.age = effect.lifetime + effect.linger_seconds - 0.02
        self.assertTrue(effect.step(0.01, (0, 0, 2000, 1000)))
        self.assertFalse(effect.step(0.02, (0, 0, 2000, 1000)))
        edge = launch_power("astral", 0, 300, facing=1)
        for _ in range(4):
            alive = edge.step(0.1, (0, 0, 100, 1000))
        self.assertTrue(alive)
        self.assertEqual(edge.x, 0)


if __name__ == "__main__":
    unittest.main()
