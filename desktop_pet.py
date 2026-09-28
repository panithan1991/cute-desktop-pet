"""A tiny desktop companion for Windows and macOS."""

from __future__ import annotations

import ctypes
import math
from pathlib import Path
import random
import sys
import time
import tkinter as tk

from app.pet_animation import choose_pet_pose
from app.pet_behavior import PetBehavior
from app.dragon_animation import DragonBehavior
from app.bibi_animation import choose_bibi_pose
from app.pet_sprites import PetSprites
from app.fantasy_art import draw_trail_scout
from app.storybook_art import (
    draw_astral_sage,
    draw_ember_warden,
    draw_moss_keeper,
)
from app.pet_motion import BibiFlightMotion, FlightMotion, JumpMotion, PetMotion
from app.power_effects import AutoPowerTimer, SPECIAL_POWERS, PowerEffectView, launch_power
from app.window_style import configure_overlay, configure_pet_window


WIDTH = 184
HEIGHT = 174
OUTLINE = "#30394f"
GROUND_PETS = frozenset({"bunny", "mookrata", "kitten"})
AIR_PETS = frozenset({"bibi", "dragon"})
PET_CHARACTERS = GROUND_PETS | AIR_PETS
GROUND_JUMPERS = GROUND_PETS | {"guardian", "moss", "astral", "trail", "ember"}


def get_work_area(root: tk.Tk) -> tuple[int, int, int, int]:
    """Return a usable primary-display area clear of system UI."""
    if sys.platform == "win32":
        from ctypes import wintypes

        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    if sys.platform == "darwin":
        # Tk exposes the full display rather than the macOS visible frame.
        # Leave room for the menu bar and a bottom-positioned Dock.
        return 0, 32, root.winfo_screenwidth(), root.winfo_screenheight() - 80
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
        self.jump = JumpMotion(launch_speed=245, gravity=1050)
        self.flight = FlightMotion(self.x, self.y)
        self.bibi_flight = BibiFlightMotion(self.x, self.y, auto_launch=False)
        self.dragon_flight = BibiFlightMotion(self.x, self.y, speed=55, auto_launch=False,
                                             altitude_range=(0.72, 0.85))
        self.dragging = False
        self.drag_offset = (0, 0)
        self.running = True
        self.last_tick = time.monotonic()
        self.walk_time = 0.0
        self.idle_until = self.last_tick + 7.0
        self.next_idle = self.idle_until + 2.5
        self.next_jump = self.last_tick + self.random.uniform(12, 18)
        self.next_blink = self.last_tick + self.random.uniform(2, 5)
        self.blink_until = 0.0
        self.land_until = 0.0
        self.power_timer = AutoPowerTimer(5, self.last_tick + 5)
        self.effects: list[PowerEffectView] = []

        self.paused_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=True)
        self.auto_power_var = tk.BooleanVar(value=True)
        self.power_interval_var = tk.IntVar(value=5)
        default_character = "bunny"
        if "mookrata" in Path(sys.argv[0]).stem.lower() or "--mookrata" in sys.argv[1:]:
            default_character = "mookrata"
        if "bibi" in Path(sys.argv[0]).stem.lower() or "--bibi" in sys.argv[1:]:
            default_character = "bibi"
        if "kitten" in Path(sys.argv[0]).stem.lower() or "--kitten" in sys.argv[1:]:
            default_character = "kitten"
        if "dragon" in Path(sys.argv[0]).stem.lower() or "--dragon" in sys.argv[1:]:
            default_character = "dragon"
        for argument in sys.argv[1:]:
            if argument.startswith("--character="):
                requested = argument.split("=", 1)[1]
                if requested == "moo":
                    requested = "mookrata"
                if requested in PET_CHARACTERS:
                    default_character = requested
        self.character_var = tk.StringVar(value=default_character)
        self.current_character = default_character
        self.behavior = (DragonBehavior(self.random) if default_character == "dragon"
                         else PetBehavior(default_character, self.random))
        if default_character == "mookrata":
            self.jump.launch_speed = 300
        self.speed_var = tk.StringVar(value="normal")
        self.pet_sprites = {default_character: PetSprites(root, default_character)}

        configure_pet_window(root)
        root.wm_attributes("-topmost", True)
        background = configure_overlay(root)
        self.canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            background=background,
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
        if sys.platform == "darwin":
            # Control-click is the standard context-menu gesture on a Mac.
            self.canvas.bind("<Control-ButtonPress-1>", self._show_menu)
        else:
            self.canvas.bind("<Control-ButtonPress-1>", self._shoot_click)
        self.canvas.bind("<Double-Button-1>", self._toggle_pause)
        root.bind("<Escape>", lambda _event: self.close())
        root.bind("<KeyPress-f>", lambda _event: self._fire_now())
        root.bind("<KeyPress-t>", lambda _event: self._fire_now(special=True))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._draw(self.last_tick)
        root.after(33, self._tick)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_checkbutton(
            label="Pause (หยุดชั่วคราว)", variable=self.paused_var, command=self._set_paused
        )
        menu.add_separator()
        menu.add_radiobutton(
            label="Star Guardian (ผู้พิทักษ์ดวงดาว)", variable=self.character_var, value="guardian", command=self._set_character
        )
        menu.add_radiobutton(
            label="Starship (ยานสำรวจดาว)", variable=self.character_var, value="ship", command=self._set_character
        )
        menu.add_separator()
        for label, value in (
            ("Grove Keeper (นักดูแลพฤกษา)", "moss"),
            ("Wizard (พ่อมด)", "astral"),
            ("Trail Scout (นักสำรวจเส้นทาง)", "trail"),
            ("Amber Guardian (ผู้พิทักษ์แสงอำพัน)", "ember"),
        ):
            menu.add_radiobutton(
                label=label, variable=self.character_var, value=value, command=self._set_character
            )
        menu.add_separator()
        menu.add_radiobutton(
            label="Cartoon Cat (แมวน้อย)", variable=self.character_var, value="cat", command=self._set_character
        )
        menu.add_radiobutton(
            label="BooBoo — Rabbit (กระต่ายหูตก)", variable=self.character_var,
            value="bunny", command=self._set_character,
        )
        menu.add_radiobutton(
            label="Moo Krata — Puppy (ลูกสุนัข)", variable=self.character_var,
            value="mookrata", command=self._set_character,
        )
        menu.add_radiobutton(
            label="Bibi — Eagle (ลูกนกอินทรี)", variable=self.character_var,
            value="bibi", command=self._set_character,
        )
        menu.add_radiobutton(
            label="Tabby Kitten (ลูกแมวลายขนฟู)", variable=self.character_var,
            value="kitten", command=self._set_character,
        )
        menu.add_radiobutton(label="Sleepy Dragon (มังกรดำขี้เซา)", variable=self.character_var,
                             value="dragon", command=self._set_character)
        speed_menu = tk.Menu(menu, tearoff=False)
        for label, value in (("Slow (ช้า)", "slow"), ("Normal (ปกติ)", "normal"), ("Fast (เร็ว)", "fast")):
            speed_menu.add_radiobutton(
                label=label, variable=self.speed_var, value=value, command=self._set_speed
            )
        menu.add_cascade(label="Speed (ความเร็ว)", menu=speed_menu)
        menu.add_checkbutton(
            label="Always on Top (อยู่เหนือหน้าต่างอื่น)",
            variable=self.topmost_var,
            command=self._set_topmost,
        )
        menu.add_checkbutton(
            label="Auto Powers (ใช้พลังอัตโนมัติ)", variable=self.auto_power_var,
            command=self._reset_power_timer, state="disabled",
        )
        self.auto_power_menu_index = menu.index("end")
        interval_menu = tk.Menu(menu, tearoff=False)
        for seconds in (3, 5, 6):
            interval_menu.add_radiobutton(
                label=f"Every {seconds}s (ทุก {seconds} วินาที)",
                variable=self.power_interval_var,
                value=seconds,
                command=self._reset_power_timer,
            )
        menu.add_cascade(label="Power Interval (ความถี่ใช้พลัง)", menu=interval_menu, state="disabled")
        self.power_interval_menu_index = menu.index("end")
        menu.add_command(label="Fly (บิน)" if self.current_character in AIR_PETS else "Jump (กระโดด)",
                         command=self._jump_now)
        self.jump_menu_index = menu.index("end")
        menu.add_command(label="Curl Up & Sleep (ขดตัวนอน)" if self.current_character == "dragon" else "Roll / Belly Up (กลิ้งเล่น / นอนหงาย)",
                         command=self._roll_now)
        self.roll_menu_index = menu.index("end")
        menu.add_command(label="Use Power (ใช้พลัง)", command=self._fire_now, state="disabled")
        self.fire_menu_index = menu.index("end")
        menu.add_command(
            label="Special Power (พลังพิเศษ)", command=lambda: self._fire_now(special=True),
            state="disabled",
        )
        self.special_menu_index = menu.index("end")
        menu.add_command(label="Return to Bottom (กลับไปขอบล่าง)", command=self._move_to_bottom)
        menu.add_separator()
        menu.add_command(label="Quit (ออกจากแอป)", command=self.close)
        self.menu = menu

    def _place_window(self) -> None:
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{round(self.x)}+{round(self.y)}")

    def _set_paused(self) -> None:
        self.motion.paused = self.paused_var.get()
        self.flight.paused = self.paused_var.get()
        self.bibi_flight.paused = self.paused_var.get()
        self.dragon_flight.paused = self.paused_var.get()

    def _set_topmost(self) -> None:
        topmost = self.topmost_var.get()
        self.root.wm_attributes("-topmost", topmost)
        for view in self.effects:
            view.window.wm_attributes("-topmost", topmost)

    def _toggle_pause(self, _event: tk.Event) -> None:
        self.paused_var.set(not self.paused_var.get())
        self._set_paused()

    def _set_speed(self) -> None:
        self.motion.speed = {"slow": 38, "normal": 65, "fast": 105}[self.speed_var.get()]
        self.flight.speed = {"slow": 85, "normal": 145, "fast": 220}[self.speed_var.get()]
        self.bibi_flight.speed = {"slow": 58, "normal": 95, "fast": 145}[self.speed_var.get()]
        self.dragon_flight.speed = {"slow": 35, "normal": 55, "fast": 85}[self.speed_var.get()]

    def _reset_power_timer(self) -> None:
        self.power_timer.reset(time.monotonic(), self.power_interval_var.get())

    def _set_character(self) -> None:
        character = self.character_var.get()
        if character in PET_CHARACTERS and character not in self.pet_sprites:
            self.pet_sprites[character] = PetSprites(self.root, character)
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
        if character in AIR_PETS:
            self.base_y = bottom - HEIGHT
            bird = self.dragon_flight if character == "dragon" else self.bibi_flight
            bird.reset(self.x, self.base_y)
            self.y = self.base_y
        elif self.current_character in AIR_PETS and character != "ship":
            self.base_y = bottom - HEIGHT
            self.y = self.base_y
            self.motion.x = self.x
        if character not in GROUND_JUMPERS:
            self.jump.reset()
        if character in GROUND_PETS:
            self.jump.reset()
            self.jump.launch_speed = 245 if character in {"bunny", "kitten"} else 300
            self.jump.gravity = 1050
        else:
            self.jump.launch_speed = 340
            self.jump.gravity = 1050
            self.idle_until = 0.0
            self.next_idle = time.monotonic() + self.random.uniform(7, 12)
        self.current_character = character
        if character in PET_CHARACTERS:
            self.behavior = (DragonBehavior(self.random) if character == "dragon"
                             else PetBehavior(character, self.random))
            self.walk_time = 0.0
            for view in self.effects:
                view.close()
            self.effects.clear()
        self._reset_power_timer()
        power_state = "disabled" if character in PET_CHARACTERS else "normal"
        for index in (self.auto_power_menu_index, self.power_interval_menu_index,
                      self.fire_menu_index):
            self.menu.entryconfig(index, state=power_state)
        self.menu.entryconfig(
            self.special_menu_index,
            label=SPECIAL_POWERS.get(character, ("", "Special Power (พลังพิเศษ)"))[1],
            state="normal" if character in SPECIAL_POWERS else "disabled",
        )
        self.menu.entryconfig(self.jump_menu_index, label="Fly (บิน)" if character in AIR_PETS else "Jump (กระโดด)",
                              state="normal" if character in GROUND_JUMPERS or character in AIR_PETS else "disabled")
        self.menu.entryconfig(self.roll_menu_index,
                              label="Curl Up & Sleep (ขดตัวนอน)" if character == "dragon" else "Roll / Belly Up (กลิ้งเล่น / นอนหงาย)",
                              state="normal" if character in PET_CHARACTERS else "disabled")
        self._place_window()
        self._redraw()

    def _jump_now(self) -> None:
        if self.current_character in AIR_PETS:
            bird = self.dragon_flight if self.current_character == "dragon" else self.bibi_flight
            if bird.state == "rest" and not bird.paused:
                self.behavior.force("walk")
            return
        if self.current_character in GROUND_JUMPERS and not self.motion.paused:
            if self.current_character in GROUND_PETS and self.behavior.transition.active:
                return
            self.jump.jump()
            delay = self.random.uniform(12, 18) if self.current_character in {"bunny", "kitten"} else (self.random.uniform(8, 13) if self.current_character == "mookrata" else self.random.uniform(3, 6))
            self.next_jump = time.monotonic() + delay

    def _shoot_click(self, _event: tk.Event) -> str:
        self._fire_now()
        return "break"

    def _roll_now(self) -> None:
        if self.paused_var.get() or self.dragging:
            return
        if self.current_character in AIR_PETS:
            bird = self.dragon_flight if self.current_character == "dragon" else self.bibi_flight
            if bird.state == "rest":
                self.behavior.force("sleep" if self.current_character == "dragon" else "roll")
            return
        if self.current_character not in GROUND_PETS or self.jump.airborne:
            return
        self.behavior.force("roll")

    def _fire_now(self, special: bool = False) -> bool:
        if self.current_character in PET_CHARACTERS:
            return False
        if special and self.current_character not in SPECIAL_POWERS:
            return False
        if len(self.effects) >= 6:
            return False
        effect = launch_power(
            self.current_character, self.x, self.y,
            self.motion.direction, self.flight.dx, special,
        )
        self.effects.append(PowerEffectView(self.root, effect, self.topmost_var.get()))
        return True

    def _redraw(self) -> None:
        self._draw(time.monotonic())

    def _move_to_bottom(self) -> None:
        self.work_area = get_work_area(self.root)
        self.y = self.work_area[3] - HEIGHT
        self.base_y = self.y
        self.jump.reset()
        self.flight.y = self.y
        self.bibi_flight.reset(self.x, self.y)
        self.dragon_flight.reset(self.x, self.y)
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
        self.bibi_flight.x = self.x
        self.bibi_flight.y = self.y
        self.dragon_flight.x = self.x
        self.dragon_flight.y = self.y
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
        if (now >= self.next_idle and self.current_character not in PET_CHARACTERS | {"ship"}
                and not self.jump.airborne):
            self.idle_until = now + self.random.uniform(0.7, 1.5)
            self.next_idle = now + self.random.uniform(7, 12)
        if now >= self.next_blink:
            self.blink_until = now + 0.16
            self.next_blink = now + self.random.uniform(2.5, 5.5)
        if self.current_character in GROUND_PETS:
            self.behavior.step(dt, frozen=self.motion.paused or self.dragging or self.jump.airborne)
        if not self.dragging:
            left, top, right, bottom = self.work_area
            if self.current_character == "ship":
                self.flight.step(dt, left, top, right - WIDTH, bottom - HEIGHT)
                self.x, self.y = self.flight.x, self.flight.y
                if not self.flight.paused:
                    self.walk_time += min(max(dt, 0), 0.1)
            elif self.current_character in AIR_PETS:
                bird = self.dragon_flight if self.current_character == "dragon" else self.bibi_flight
                if bird.state == "rest":
                    self.behavior.step(dt, frozen=bird.paused)
                    if self.behavior.walking and bird.launch():
                        bird.cruise_duration = self.behavior.duration
                else:
                    self.behavior.step(dt, frozen=bird.paused, advance_state=False)
                was_flying = bird.state != "rest"
                bird.step(dt, left, top, right - WIDTH, bottom - HEIGHT)
                if was_flying and bird.state == "rest":
                    self.behavior.finish()
                self.x, self.y = bird.x, bird.y
            else:
                moving = (self.behavior.walking if self.current_character in GROUND_PETS
                          else now >= self.idle_until) or self.jump.airborne
                if moving:
                    speed = self.motion.speed
                    pace = self.behavior.pace if self.current_character in GROUND_PETS else 1.0
                    self.motion.speed *= pace
                    self.motion.step(dt, left, right - WIDTH)
                    self.motion.speed = speed
                    self.x = self.motion.x
                    if not self.motion.paused:
                        self.walk_time += min(max(dt, 0), 0.1) * pace * speed / 65
                if self.current_character in GROUND_JUMPERS:
                    if (
                        not self.motion.paused and (
                            self.behavior.consume_hop() if self.current_character in GROUND_PETS
                            else now >= self.next_jump)
                    ):
                        self.jump.jump()
                        if self.current_character not in GROUND_PETS:
                            self.next_jump = now + self.random.uniform(3.5, 6.5)
                    was_airborne = self.jump.airborne
                    if not self.motion.paused:
                        self.jump.step(dt, self.base_y - top)
                    if self.current_character in PET_CHARACTERS and was_airborne and not self.jump.airborne:
                        self.land_until = now + 0.20
                    self.y = self.base_y - self.jump.height
                else:
                    self.y = self.base_y
            self._place_window()
        if (
            self.current_character not in PET_CHARACTERS
            and self.power_timer.due(now)
            and self.auto_power_var.get()
            and not self.paused_var.get()
            and not self.dragging
        ):
            self._fire_now(special=self.current_character in SPECIAL_POWERS)
        live_effects: list[PowerEffectView] = []
        for view in self.effects:
            if view.effect.step(dt, self.work_area):
                view.draw()
                live_effects.append(view)
            else:
                view.close()
        self.effects = live_effects
        self._draw(now)
        self.root.after(33, self._tick)

    def _draw(self, now: float) -> None:
        canvas = self.canvas
        canvas.delete("all")
        character = self.character_var.get()
        walking = not self.motion.paused and not self.dragging and (
            (self.behavior.walking if character in GROUND_PETS else now >= self.idle_until)
            or self.jump.airborne
        )
        stride = math.sin(self.walk_time * 12) if walking else 0.0
        bob = abs(stride) * 3 if walking else math.sin(now * 2) * 1.5
        blink = now < self.blink_until
        facing = self.motion.direction
        if character == "guardian":
            self._draw_guardian(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "ship":
            self._draw_ship(canvas, now, self.flight.dx, self.flight.dy)
        elif character == "dragon":
            pose = self.behavior.pose(self.dragon_flight.state, self.dragon_flight.elapsed)
            canvas.create_image(WIDTH // 2, HEIGHT - 2,
                                image=self.pet_sprites["dragon"].get(pose, self.dragon_flight.direction),
                                anchor="s")
        elif character == "bibi":
            pose = choose_bibi_pose(self.bibi_flight.state, self.bibi_flight.elapsed,
                                    rest_state=self.behavior.state, rest_elapsed=self.behavior.elapsed,
                                    rest_duration=self.behavior.duration, variant=self.behavior.variant,
                                    blink=blink and not self.paused_var.get(),
                                    behavior_pose=self.behavior.pose())
            canvas.create_image(WIDTH // 2, HEIGHT - 2,
                                image=self.pet_sprites["bibi"].get(pose, self.bibi_flight.direction),
                                anchor="s")
        elif character == "moss":
            draw_moss_keeper(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "astral":
            draw_astral_sage(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "trail":
            draw_trail_scout(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character == "ember":
            draw_ember_warden(canvas, bob, stride, blink, facing, self.jump.airborne)
        elif character in PET_CHARACTERS:
            self._draw_pet(canvas, now, bob, walking, blink, facing, character)
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

    def _draw_pet(
        self, c: tk.Canvas, now: float, bob: float,
        walking: bool, blink: bool, facing: int, character: str,
    ) -> None:
        pose = choose_pet_pose(
            character,
            walking=self.behavior.walking,
            walk_time=self.walk_time,
            rest_progress=self.behavior.elapsed / self.behavior.duration,
            rest_variant=self.behavior.variant,
            airborne=self.jump.airborne,
            jump_velocity=self.jump.velocity,
            landed=now < self.land_until,
            blink=blink and not self.paused_var.get(),
            paused=False,
            jump_progress=0.5 - self.jump.velocity / (2 * self.jump.launch_speed),
            rest_time=self.behavior.elapsed,
            rest_state=self.behavior.state, rest_duration=self.behavior.duration,
            behavior_pose=self.behavior.pose(),
        )
        c.create_image(
            WIDTH // 2, HEIGHT - 2,
            image=self.pet_sprites[character].get(pose, facing), anchor="s",
        )

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
        for view in self.effects:
            view.close()
        self.effects.clear()
        self.root.destroy()


def main() -> int:
    if sys.platform not in {"win32", "darwin"}:
        print("This desktop pet supports Windows and macOS.")
        return 1
    if sys.platform == "win32":
        # Keep Windows work-area coordinates and Tk window coordinates in sync.
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    root.title("Cute Desktop Pet")
    root.withdraw()
    if sys.platform == "darwin" and root.tk.call("tk", "windowingsystem") != "aqua":
        root.destroy()
        print("macOS needs a Python build with Aqua Tk (for example from python.org).")
        return 1
    smoke_test = "--smoke-test" in sys.argv[1:]
    pet = DesktopPet(root)
    if smoke_test:
        root.update_idletasks()
        pet.close()
        return 0
    root.deiconify()
    root.lift()
    root.mainloop()
    return 0


def report_mac_startup_failure() -> None:
    """Make a Finder-launched crash visible and leave a local diagnostic log."""
    from pathlib import Path
    import subprocess
    import traceback

    log_path = Path.home() / "Library" / "Logs" / "BooBoo" / "startup.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
    except OSError:
        pass
    try:
        subprocess.run(
            ["osascript", "-e", 'display alert "BooBoo could not start" '
             'message "See ~/Library/Logs/BooBoo/startup.log for details." as critical'],
            timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        if sys.platform == "darwin":
            report_mac_startup_failure()
        raise
