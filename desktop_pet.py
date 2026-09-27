"""A tiny, dependency-free Windows desktop companion."""

from __future__ import annotations

import ctypes
import math
import random
import sys
import time
import tkinter as tk
from ctypes import wintypes

from fantasy_art import (
    draw_astral_sage,
    draw_ember_warden,
    draw_moss_keeper,
    draw_trail_scout,
)
from pet_motion import FlightMotion, JumpMotion, PetMotion


WIDTH = 184
HEIGHT = 174
TRANSPARENT = "#ff00ff"
OUTLINE = "#30394f"
GROUND_JUMPERS = frozenset({"guardian", "moss", "astral", "trail", "ember"})


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
        self.base_y = self.y
        self.motion = PetMotion(self.x)
        self.jump = JumpMotion()
        self.flight = FlightMotion(self.x, self.y)
        self.dragging = False
        self.drag_offset = (0, 0)
        self.running = True
        self.last_tick = time.monotonic()
        self.walk_time = 0.0
        self.idle_until = 0.0
        self.next_idle = self.last_tick + self.random.uniform(7, 12)
        self.next_jump = self.last_tick + self.random.uniform(2, 4)
        self.next_blink = self.last_tick + self.random.uniform(2, 5)
        self.blink_until = 0.0

        self.paused_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=True)
        self.character_var = tk.StringVar(value="guardian")
        self.current_character = "guardian"
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
        self.canvas.bind("<Button-2>", lambda _event: self._jump_now())
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
            label="ผู้พิทักษ์ดวงดาว", variable=self.character_var, value="guardian", command=self._set_character
        )
        menu.add_radiobutton(
            label="ยานสำรวจดาว", variable=self.character_var, value="ship", command=self._set_character
        )
        menu.add_separator()
        for label, value in (
            ("ผู้ดูแลพฤกษา", "moss"),
            ("นักอ่านแผนที่ดาว", "astral"),
            ("นักสำรวจเส้นทาง", "trail"),
            ("ผู้พิทักษ์แสงอำพัน", "ember"),
        ):
            menu.add_radiobutton(
                label=label, variable=self.character_var, value=value, command=self._set_character
            )
        menu.add_separator()
        menu.add_radiobutton(
            label="แมวน้อย", variable=self.character_var, value="cat", command=self._set_character
        )
        menu.add_radiobutton(
            label="กระต่าย", variable=self.character_var, value="bunny", command=self._set_character
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
        menu.add_command(label="กระโดด", command=self._jump_now)
        menu.add_command(label="กลับไปขอบล่าง", command=self._move_to_bottom)
        menu.add_separator()
        menu.add_command(label="ออกจากแอป", command=self.close)
        self.menu = menu

    def _place_window(self) -> None:
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{round(self.x)}+{round(self.y)}")

    def _set_paused(self) -> None:
        self.motion.paused = self.paused_var.get()
        self.flight.paused = self.paused_var.get()

    def _toggle_pause(self, _event: tk.Event) -> None:
        self.paused_var.set(not self.paused_var.get())
        self._set_paused()

    def _set_speed(self) -> None:
        self.motion.speed = {"slow": 38, "normal": 65, "fast": 105}[self.speed_var.get()]
        self.flight.speed = {"slow": 85, "normal": 145, "fast": 220}[self.speed_var.get()]

    def _set_character(self) -> None:
        character = self.character_var.get()
        left, top, right, bottom = self.work_area
        if character == "ship" and self.current_character != "ship":
            self.flight.x = self.x
            self.flight.y = top + (bottom - top - HEIGHT) * 0.32
            self.y = self.flight.y
        elif self.current_character == "ship":
            self.base_y = bottom - HEIGHT
            self.y = self.base_y
            self.motion.x = self.x
            self.jump.reset()
        if character not in GROUND_JUMPERS:
            self.jump.reset()
        self.current_character = character
        self._place_window()
        self._redraw()

    def _jump_now(self) -> None:
        if self.current_character in GROUND_JUMPERS and not self.motion.paused:
            self.jump.jump()
            self.next_jump = time.monotonic() + self.random.uniform(3, 6)

    def _redraw(self) -> None:
        self._draw(time.monotonic())

    def _move_to_bottom(self) -> None:
        self.work_area = get_work_area(self.root)
        self.y = self.work_area[3] - HEIGHT
        self.base_y = self.y
        self.jump.reset()
        self.flight.y = self.y
        self._place_window()

    def _start_drag(self, event: tk.Event) -> None:
        self.dragging = True
        self.drag_offset = (event.x, event.y)
        self.jump.reset()

    def _drag(self, event: tk.Event) -> None:
        left, top, right, bottom = self.work_area
        self.x = min(max(event.x_root - self.drag_offset[0], left), right - WIDTH)
        self.y = min(max(event.y_root - self.drag_offset[1], top), bottom - HEIGHT)
        self.motion.x = self.x
        self.flight.x = self.x
        self.flight.y = self.y
        if self.current_character != "ship":
            self.base_y = self.y
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
        if now >= self.next_idle and self.current_character != "ship" and not self.jump.airborne:
            self.idle_until = now + self.random.uniform(0.7, 1.5)
            self.next_idle = now + self.random.uniform(7, 12)
        if now >= self.next_blink:
            self.blink_until = now + 0.16
            self.next_blink = now + self.random.uniform(2.5, 5.5)
        if not self.dragging:
            left, top, right, bottom = self.work_area
            if self.current_character == "ship":
                self.flight.step(dt, left, top, right - WIDTH, bottom - HEIGHT)
                self.x, self.y = self.flight.x, self.flight.y
                if not self.flight.paused:
                    self.walk_time += min(max(dt, 0), 0.1)
            else:
                moving = now >= self.idle_until or self.jump.airborne
                if moving:
                    self.motion.step(dt, left, right - WIDTH)
                    self.x = self.motion.x
                    if not self.motion.paused:
                        self.walk_time += min(max(dt, 0), 0.1)
                if self.current_character in GROUND_JUMPERS:
                    if now >= self.next_jump and not self.motion.paused:
                        self.jump.jump()
                        self.next_jump = now + self.random.uniform(3.5, 6.5)
                    if not self.motion.paused:
                        self.jump.step(dt, self.base_y - top)
                    self.y = self.base_y - self.jump.height
                else:
                    self.y = self.base_y
            self._place_window()
        self._draw(now)
        self.root.after(33, self._tick)

    def _draw(self, now: float) -> None:
        canvas = self.canvas
        canvas.delete("all")
        character = self.character_var.get()
        walking = not self.motion.paused and not self.dragging and (now >= self.idle_until or self.jump.airborne)
        stride = math.sin(self.walk_time * 12) if walking else 0.0
        bob = abs(stride) * 3 if walking else math.sin(now * 2) * 1.5
        blink = now < self.blink_until
        facing = self.motion.direction
        if character == "guardian":
            self._draw_guardian(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "ship":
            self._draw_ship(canvas, now, self.flight.dx, self.flight.dy)
        elif character == "moss":
            draw_moss_keeper(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "astral":
            draw_astral_sage(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "trail":
            draw_trail_scout(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "ember":
            draw_ember_warden(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "bunny":
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

    def _draw_guardian(
        self, c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
    ) -> None:
        """An original star navigator: a cream helmet, copper cape and orbit compass."""
        y = -bob
        step = stride * 6
        if not jumping:
            c.create_oval(48, 153, 136, 164, fill="#c4ced1", outline="")
        # Copper cape and dark boots establish a silhouette distinct from a robe.
        c.create_polygon(
            65, 81 + y, 121, 80 + y, 143 + stride * 4, 143 + y,
            105, 135 + y, 75, 146 + y, 42 - stride * 4, 143 + y,
            fill="#dd8058", outline=OUTLINE, width=3,
        )
        c.create_line(54, 130 + y, 70, 110 + y, fill="#f5bf84", width=4)
        if jumping:
            c.create_line(79, 129 + y, 69, 138 + y, fill=OUTLINE, width=16, capstyle=tk.ROUND)
            c.create_line(106, 129 + y, 119, 138 + y, fill=OUTLINE, width=16, capstyle=tk.ROUND)
            c.create_oval(56, 130 + y, 78, 143 + y, fill="#34455c", outline=OUTLINE, width=2)
            c.create_oval(109, 130 + y, 131, 143 + y, fill="#34455c", outline=OUTLINE, width=2)
        else:
            c.create_line(78, 127 + y, 73 + step, 146 + y, fill=OUTLINE, width=16, capstyle=tk.ROUND)
            c.create_line(108, 127 + y, 113 - step, 146 + y, fill=OUTLINE, width=16, capstyle=tk.ROUND)
            c.create_oval(58 + step, 141 + y, 86 + step, 156 + y, fill="#34455c", outline=OUTLINE, width=2)
            c.create_oval(99 - step, 141 + y, 127 - step, 156 + y, fill="#34455c", outline=OUTLINE, width=2)
        # A short navigation compass with a floating orb, not an energy sword.
        c.create_line(144, 112 + y, 151, 58 + y, fill=OUTLINE, width=7, capstyle=tk.ROUND)
        c.create_line(144, 111 + y, 150, 65 + y, fill="#73d9d7", width=3, capstyle=tk.ROUND)
        c.create_oval(136, 43 + y, 165, 71 + y, fill="#f7e7c5", outline=OUTLINE, width=3)
        c.create_oval(143, 50 + y, 158, 64 + y, fill="#72dce1", outline="")
        c.create_oval(147, 51 + y, 152, 56 + y, fill="white", outline="")
        c.create_oval(56, 81 + y, 128, 139 + y, fill="#f5e6c9", outline=OUTLINE, width=3)
        c.create_polygon(64, 89 + y, 92, 80 + y, 122, 91 + y, 113, 125 + y, 72, 125 + y,
                         fill="#f0a166", outline=OUTLINE, width=2)
        c.create_polygon(78, 100 + y, 93, 93 + y, 108, 100 + y, 103, 117 + y, 83, 117 + y,
                         fill="#34455c", outline="")
        c.create_oval(85, 99 + y, 101, 115 + y, fill="#72dce1", outline="#f5e6c9", width=2)
        c.create_polygon(89, 101 + y, 98, 107 + y, 89, 113 + y, fill="#f7d379", outline="")
        # Hood and offset crest are geometric, with a teal visor and expressive eyes.
        c.create_oval(47, 28 + y, 137, 103 + y, fill="#34455c", outline=OUTLINE, width=3)
        c.create_oval(57, 43 + y, 127, 95 + y, fill="#f5e6c9", outline=OUTLINE, width=3)
        c.create_polygon(61, 48 + y, 76, 22 + y, 109, 23 + y, 128, 49 + y,
                         fill="#f5e6c9", outline=OUTLINE, width=3)
        c.create_polygon(82, 29 + y, 102, 29 + y, 107, 37 + y, 78, 37 + y,
                         fill="#ed945f", outline="")
        c.create_oval(65, 57 + y, 119, 84 + y, fill="#5bbcc2", outline=OUTLINE, width=2)
        for cx in (78, 105):
            if blink:
                c.create_line(cx - 4, 70 + y, cx + 4, 70 + y, fill=OUTLINE, width=3)
            else:
                c.create_oval(cx - 4, 65 + y, cx + 4, 75 + y, fill="#243148", outline="")
                c.create_oval(cx - 2 + facing, 66 + y, cx + facing, 69 + y,
                              fill="white", outline="")
        c.create_arc(83, 72 + y, 101, 86 + y, start=205, extent=130,
                     style=tk.ARC, outline=OUTLINE, width=2)
        # Cream sleeves, teal gloves and orange shoulder badges.
        c.create_oval(44, 84 + y, 72, 118 + y, fill="#f5e6c9", outline=OUTLINE, width=3)
        c.create_oval(113, 84 + y, 141, 118 + y, fill="#f5e6c9", outline=OUTLINE, width=3)
        c.create_oval(45, 105 + y, 68, 126 + y, fill="#72bdbd", outline=OUTLINE, width=2)
        c.create_oval(120, 104 + y, 145, 126 + y, fill="#72bdbd", outline=OUTLINE, width=2)
        c.create_oval(49, 88 + y, 62, 99 + y, fill="#e78e58", outline="")
        c.create_oval(124, 88 + y, 137, 99 + y, fill="#e78e58", outline="")

    def _draw_ship(self, c: tk.Canvas, now: float, dx: float, dy: float) -> None:
        """A small manta-shaped survey ship with an asymmetric orbit window."""
        facing = 1 if dx >= 0 else -1
        bob = math.sin(now * 4.5) * 2

        def x(value: float) -> float:
            return value if facing > 0 else WIDTH - value

        def oval(x1: float, y1: float, x2: float, y2: float, **kwargs: object) -> None:
            c.create_oval(min(x(x1), x(x2)), y1 + bob,
                          max(x(x1), x(x2)), y2 + bob, **kwargs)

        def polygon(points: tuple[float, ...], **kwargs: object) -> None:
            mapped = [x(value) if index % 2 == 0 else value + bob
                      for index, value in enumerate(points)]
            c.create_polygon(*mapped, **kwargs)

        pulse = 4 + math.sin(now * 15) * 3 if not self.flight.paused else 2
        # Two soft exhaust plumes follow the direction of travel.
        for ey in (78, 107):
            polygon((29, ey - 7, 9 - pulse, ey, 29, ey + 7),
                    fill="#79e4e1", outline="")
            polygon((27, ey - 4, 15 - pulse / 2, ey, 27, ey + 4),
                    fill="#f5d174", outline="")
        polygon((30, 72, 18, 57, 23, 100, 53, 117, 58, 91),
                fill="#34455c", outline=OUTLINE, width=3)
        polygon((61, 101, 29, 125, 69, 121, 91, 107),
                fill="#64b8b8", outline=OUTLINE, width=3)
        polygon((34, 74, 61, 56, 115, 54, 159, 76, 170, 89,
                 153, 104, 112, 116, 58, 111, 32, 94),
                fill="#f4e4c5", outline=OUTLINE, width=4)
        polygon((54, 69, 92, 59, 129, 69, 145, 82, 124, 94, 72, 94),
                fill="#ed945f", outline="")
        polygon((68, 73, 100, 64, 124, 76, 119, 95, 77, 95),
                fill="#34455c", outline=OUTLINE, width=2)
        oval(81, 70, 115, 93, fill="#69d6d5", outline="#f4e4c5", width=2)
        oval(88, 72, 98, 78, fill="#d9ffff", outline="")
        polygon((150, 78, 166, 88, 149, 98, 138, 88),
                fill="#68c3c0", outline=OUTLINE, width=2)
        c.create_line(x(63), 102 + bob, x(111), 103 + bob,
                      fill="#34455c", width=3, capstyle=tk.ROUND)
        oval(51, 98, 61, 108, fill="#f7d379", outline=OUTLINE, width=1)
        oval(68, 101, 76, 109, fill="#72dce1", outline="")
        # Tiny radar star makes the craft readable even when flying upward.
        c.create_line(x(117), 45 + bob, x(123), 36 + bob,
                      fill=OUTLINE, width=3, capstyle=tk.ROUND)
        oval(119, 29, 128, 39, fill="#f7d379", outline=OUTLINE, width=2)

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
