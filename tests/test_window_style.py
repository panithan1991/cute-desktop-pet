import unittest
from unittest.mock import Mock, patch

from window_style import configure_overlay


class WindowStyleTests(unittest.TestCase):
    def test_windows_uses_color_key(self):
        window = Mock()
        background = configure_overlay(window, "win32")
        self.assertEqual(background, "#ff00ff")
        window.configure.assert_called_once_with(background=background)
        window.wm_attributes.assert_called_once_with("-transparentcolor", background)

    def test_mac_uses_aqua_transparent_background(self):
        window = Mock()
        background = configure_overlay(window, "darwin")
        self.assertEqual(background, "systemTransparent")
        window.configure.assert_called_once_with(background=background)
        window.wm_attributes.assert_called_once_with("-transparent", True)

    def test_other_platforms_fail_clearly(self):
        with self.assertRaises(RuntimeError):
            configure_overlay(Mock(), "linux")

    def test_mac_entrypoint_starts_with_aqua_tk(self):
        import desktop_pet

        root = Mock()
        root.tk.call.return_value = "aqua"
        with patch.object(desktop_pet.sys, "platform", "darwin"), \
             patch.object(desktop_pet.tk, "Tk", return_value=root), \
             patch.object(desktop_pet, "DesktopPet") as pet:
            self.assertEqual(desktop_pet.main(), 0)
        pet.assert_called_once_with(root)
        root.mainloop.assert_called_once()

    def test_mac_entrypoint_rejects_non_aqua_tk(self):
        import desktop_pet

        root = Mock()
        root.tk.call.return_value = "x11"
        with patch.object(desktop_pet.sys, "platform", "darwin"), \
             patch.object(desktop_pet.tk, "Tk", return_value=root), \
             patch.object(desktop_pet, "DesktopPet") as pet:
            self.assertEqual(desktop_pet.main(), 1)
        root.destroy.assert_called_once()
        pet.assert_not_called()

    def test_bundle_smoke_mode_initializes_then_closes(self):
        import desktop_pet

        root = Mock()
        root.tk.call.return_value = "aqua"
        with patch.object(desktop_pet.sys, "platform", "darwin"), \
             patch.object(desktop_pet.sys, "argv", ["desktop_pet.py", "--smoke-test"]), \
             patch.object(desktop_pet.tk, "Tk", return_value=root), \
             patch.object(desktop_pet, "DesktopPet") as pet:
            self.assertEqual(desktop_pet.main(), 0)
        root.withdraw.assert_called_once()
        pet.return_value.close.assert_called_once()
        root.mainloop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
