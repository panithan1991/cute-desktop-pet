"""A tiny, dependency-free Windows desktop companion."""

from __future__ import annotations

import ctypes
import math
import random
import sys
import time
import tkinter as tk
from ctypes import wintypes

from pet_motion import PetMotion


WIDTH = 184
HEIGHT = 174
TRANSPARENT = "#ff00ff"
OUTLINE = "#654842"


def get_work_area(root: tk.Tk) -> tuple[int, int, int, int]:
    """Return the primary monitor's usable area, excluding the taskbar."""
    if sys.platform == "win32":
        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class DesktopPet:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.random = random.Random()
        self.work_area = get_work_area(root)
        left, top, right, bottom = self.work_area
        self.x = float(left + max(0, right - left - WIDTH) * 0.25)
        self.y = float(bottom - HEIGHT)
        self.motion = PetMotion(self.x)
        self.dragging = False
        self.drag_offset = (0, 0)
        self.running = True
        self.last_tick = time.monotonic()
        self.walk_time = 0.0
        self.idle_until = 0.0
        self.next_idle = self.last_tick + self.random.uniform(7, 12)
        self.next_blink = self.last_tick + self.random.uniform(2, 5)
        self.blink_until = 0.0

        self.paused_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=True)
        self.character_var = tk.StringVar(value="cat")
        self.speed_var = tk.StringVar(value="normal")

        root.configure(background=TRANSPARENT)
        root.overrideredirect(True)
        root.wm_attributes("-topmost", True)
        # On Windows this makes the unused canvas pixels see-through and lets
        # mouse clicks pass through them to the user's other applications.
        root.wm_attributes("-transparentcolor", TRANSPARENT)
        self.canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            background=TRANSPARENT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.pack()
        self._place_window()
        self._build_menu()
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Double-Button-1>", self._toggle_pause)
        root.bind("<Escape>", lambda _event: self.close())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._draw(self.last_tick)
        root.after(33, self._tick)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_checkbutton(
            label="หยุดเดินชั่วคราว", variable=self.paused_var, command=self._set_paused
        )
        menu.add_separator()
        menu.add_radiobutton(
            label="แมวน้อย", variable=self.character_var, value="cat", command=self._redraw
        )
        menu.add_radiobutton(
            label="กระต่าย", variable=self.character_var, value="bunny", command=self._redraw
        )
        speed_menu = tk.Menu(menu, tearoff=False)
        for label, value in (("ช้า", "slow"), ("ปกติ", "normal"), ("เร็ว", "fast")):
            speed_menu.add_radiobutton(
                label=label, variable=self.speed_var, value=value, command=self._set_speed
            )
        menu.add_cascade(label="ความเร็ว", menu=speed_menu)
        menu.add_checkbutton(
            label="อยู่เหนือหน้าต่างอื่น",
            variable=self.topmost_var,
            command=lambda: self.root.wm_attributes("-topmost", self.topmost_var.get()),
        )
        menu.add_command(label="กลับไปขอบล่าง", command=self._move_to_bottom)
        menu.add_separator()
        menu.add_command(label="ออกจากแอป", command=self.close)
        self.menu = menu

    def _place_window(self) -> None:
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{round(self.x)}+{round(self.y)}")

    def _set_paused(self) -> None:
        self.motion.paused = self.paused_var.get()

    def _toggle_pause(self, _event: tk.Event) -> None:
        self.paused_var.set(not self.paused_var.get())
        self._set_paused()

    def _set_speed(self) -> None:
        self.motion.speed = {"slow": 38, "normal": 65, "fast": 105}[self.speed_var.get()]

    def _redraw(self) -> None:
        self._draw(time.monotonic())

    def _move_to_bottom(self) -> None:
        self.work_area = get_work_area(self.root)
        self.y = self.work_area[3] - HEIGHT
        self._place_window()

    def _start_drag(self, event: tk.Event) -> None:
        self.dragging = True
        self.drag_offset = (event.x, event.y)

    def _drag(self, event: tk.Event) -> None:
        left, top, right, bottom = self.work_area
        self.x = min(max(event.x_root - self.drag_offset[0], left), right - WIDTH)
        self.y = min(max(event.y_root - self.drag_offset[1], top), bottom - HEIGHT)
        self.motion.x = self.x
        self._place_window()

    def _end_drag(self, _event: tk.Event) -> None:
        self.dragging = False

    def _show_menu(self, event: tk.Event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _tick(self) -> None:
        if not self.running:
            return
        now = time.monotonic()
        dt = now - self.last_tick
        self.last_tick = now
        if now >= self.next_idle:
            self.idle_until = now + self.random.uniform(0.7, 1.5)
            self.next_idle = now + self.random.uniform(7, 12)
        if now >= self.next_blink:
            self.blink_until = now + 0.16
            self.next_blink = now + self.random.uniform(2.5, 5.5)
        if not self.dragging and now >= self.idle_until:
            left, _top, right, _bottom = self.work_area
            self.motion.step(dt, left, right - WIDTH)
            self.x = self.motion.x
            self._place_window()
            if not self.motion.paused:
                self.walk_time += min(max(dt, 0), 0.1)
        self._draw(now)
        self.root.after(33, self._tick)

    def _draw(self, now: float) -> None:
        canvas = self.canvas
        canvas.delete("all")
        walking = not self.motion.paused and not self.dragging and now >= self.idle_until
        stride = math.sin(self.walk_time * 12) if walking else 0.0
        bob = abs(stride) * 3 if walking else math.sin(now * 2) * 1.5
        blink = now < self.blink_until
        facing = self.motion.direction
        if self.character_var.get() == "bunny":
            self._draw_bunny(canvas, bob, stride, blink, facing)
        else:
            self._draw_cat(canvas, bob, stride, blink, facing)

    @staticmethod
    def _eyes(canvas: tk.Canvas, y: float, blink: bool, facing: int) -> None:
        for cx in (76, 110):
            if blink:
                canvas.create_line(cx - 5, y, cx + 5, y, fill=OUTLINE, width=3, capstyle=tk.ROUND)
            else:
                canvas.create_oval(cx - 5, y - 6, cx + 5, y + 6, fill=OUTLINE, outline="")
                canvas.create_oval(cx - 2 + facing, y - 4, cx + facing, y - 2, fill="white", outline="")

    def _draw_cat(self, c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int) -> None:
        y = -bob
        # The little shadow and tail sit behind the body.
        c.create_oval(55, 154, 129, 164, fill="#d5d1cd", outline="")
        tail_points = (59, 125 + y, 30, 132 + y, 30, 91 + y, 43, 83 + y)
        if facing < 0:
            tail_points = tuple(WIDTH - n if i % 2 == 0 else n for i, n in enumerate(tail_points))
        c.create_line(*tail_points, fill=OUTLINE, width=18, smooth=True, capstyle=tk.ROUND)
        c.create_line(*tail_points, fill="#efa56e", width=13, smooth=True, capstyle=tk.ROUND)
        c.create_oval(56, 91 + y, 128, 150 + y, fill="#f5b27d", outline=OUTLINE, width=3)
        c.create_oval(74, 107 + y, 111, 145 + y, fill="#ffdfb8", outline="")
        # Ears are broad triangles, with smaller rosy centers.
        c.create_polygon(52, 77 + y, 50, 27 + y, 82, 49 + y, fill="#f5b27d", outline=OUTLINE, width=3)
        c.create_polygon(104, 48 + y, 134, 27 + y, 131, 78 + y, fill="#f5b27d", outline=OUTLINE, width=3)
        c.create_polygon(58, 59 + y, 57, 38 + y, 74, 51 + y, fill="#e98e91", outline="")
        c.create_polygon(112, 51 + y, 128, 38 + y, 126, 59 + y, fill="#e98e91", outline="")
        c.create_oval(48, 47 + y, 136, 120 + y, fill="#f8c396", outline=OUTLINE, width=3)
        c.create_oval(56, 87 + y, 83, 106 + y, fill="#ffe4cc", outline="")
        c.create_oval(101, 87 + y, 128, 106 + y, fill="#ffe4cc", outline="")
        self._eyes(c, 82 + y, blink, facing)
        c.create_polygon(88, 94 + y, 96, 94 + y, 92, 99 + y, fill="#b56b70", outline="")
        c.create_line(92, 99 + y, 92, 103 + y, fill=OUTLINE, width=2)
        c.create_arc(84, 98 + y, 93, 108 + y, start=200, extent=140, style=tk.ARC, outline=OUTLINE, width=2)
        c.create_arc(91, 98 + y, 100, 108 + y, start=200, extent=140, style=tk.ARC, outline=OUTLINE, width=2)
        for start_x, end_x in ((54, 35), (129, 149)):
            c.create_line(start_x, 98 + y, end_x, 94 + y, fill=OUTLINE, width=2)
            c.create_line(start_x, 103 + y, end_x, 108 + y, fill=OUTLINE, width=2)
        c.create_arc(64, 101 + y, 121, 135 + y, start=185, extent=170, style=tk.ARC, outline="#df6968", width=7)
        c.create_oval(87, 122 + y, 98, 133 + y, fill="#f5d67e", outline=OUTLINE, width=1)
        left_step = stride * 5
        c.create_oval(60 + left_step, 139 + y, 86 + left_step, 155 + y, fill="#f5b27d", outline=OUTLINE, width=2)
        c.create_oval(100 - left_step, 139 + y, 126 - left_step, 155 + y, fill="#f5b27d", outline=OUTLINE, width=2)

    def _draw_bunny(self, c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int) -> None:
        y = -bob
        c.create_oval(55, 154, 129, 164, fill="#d5d1cd", outline="")
        c.create_oval(53, 103 + y, 72, 122 + y, fill="#fffefa", outline=OUTLINE, width=2)
        c.create_oval(56, 94 + y, 128, 150 + y, fill="#fffefa", outline=OUTLINE, width=3)
        c.create_oval(73, 109 + y, 111, 145 + y, fill="#f5e4db", outline="")
        c.create_oval(57, 8 + y, 83, 78 + y, fill="#fffefa", outline=OUTLINE, width=3)
        c.create_oval(102, 8 + y, 128, 78 + y, fill="#fffefa", outline=OUTLINE, width=3)
        c.create_oval(65, 20 + y, 75, 65 + y, fill="#f6b7bc", outline="")
        c.create_oval(110, 20 + y, 120, 65 + y, fill="#f6b7bc", outline="")
        c.create_oval(48, 54 + y, 136, 121 + y, fill="#fffefa", outline=OUTLINE, width=3)
        c.create_oval(61, 91 + y, 78, 101 + y, fill="#f9d6d6", outline="")
        c.create_oval(107, 91 + y, 124, 101 + y, fill="#f9d6d6", outline="")
        self._eyes(c, 83 + y, blink, facing)
        c.create_oval(88, 94 + y, 96, 100 + y, fill="#d88890", outline="")
        c.create_arc(82, 96 + y, 92, 108 + y, start=200, extent=135, style=tk.ARC, outline=OUTLINE, width=2)
        c.create_arc(92, 96 + y, 102, 108 + y, start=205, extent=135, style=tk.ARC, outline=OUTLINE, width=2)
        c.create_arc(64, 105 + y, 120, 136 + y, start=185, extent=170, style=tk.ARC, outline="#8ebbb6", width=7)
        c.create_oval(87, 124 + y, 98, 134 + y, fill="#f5d67e", outline=OUTLINE, width=1)
        left_step = stride * 5
        c.create_oval(59 + left_step, 139 + y, 85 + left_step, 155 + y, fill="#fffefa", outline=OUTLINE, width=2)
        c.create_oval(101 - left_step, 139 + y, 127 - left_step, 155 + y, fill="#fffefa", outline=OUTLINE, width=2)

    def close(self) -> None:
        self.running = False
        self.root.destroy()


def main() -> int:
    if sys.platform != "win32":
        print("This desktop pet currently supports Windows only.")
        return 1
    # Keep Windows work-area coordinates and Tk window coordinates in sync.
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    DesktopPet(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
