import unittest
from unittest.mock import Mock, patch

from window_style import configure_overlay, configure_pet_window


class WindowStyleTests(unittest.TestCase):
    def test_mac_pet_uses_native_floating_window_on_all_spaces(self):
        window = Mock()
        window._w = "."
        configure_pet_window(window, "darwin")
        window.tk.call.assert_called_once_with(
            "::tk::unsupported::MacWindowStyle", "style", ".",
            "floating", "noTitleBar noShadow canJoinAllSpaces",
        )
        window.overrideredirect.assert_not_called()

    def test_mac_pet_falls_back_for_older_aqua_tk(self):
        import tkinter as tk

        window = Mock()
        window.tk.call.side_effect = tk.TclError("unknown window style")
        configure_pet_window(window, "darwin")
        window.overrideredirect.assert_called_once_with(True)

    def test_windows_pet_keeps_borderless_window(self):
        window = Mock()
        configure_pet_window(window, "win32")
        window.overrideredirect.assert_called_once_with(True)

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
        root.withdraw.assert_called_once()
        root.deiconify.assert_called_once()
        root.lift.assert_called_once()
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
