"""BooBoo's nine transparent poses and small desktop animation timeline.

Windows/Tk uses a color key for the desktop window. Semi-transparent PNG edge
pixels blend with that key and become a visible magenta fringe. At load time we
give the displayed frames a clean binary alpha mask before Tk sees them. The
checked-in artwork remains the full-quality RGBA original, and the application
still needs only Python's standard library.
"""

from __future__ import annotations

import base64
from pathlib import Path
import struct
import sys
import tkinter as tk
import zlib


GRID_SIZE = 3
CELL_SIZE = 418
DISPLAY_SCALE = 3
ALPHA_CUTOFF = 128
POSES = {
    "idle": (0, 0),
    "smile": (1, 0),
    "happy": (2, 0),
    "curious": (0, 1),
    "hop_start": (1, 1),
    "hop_air": (2, 1),
    "hop_land": (0, 2),
    "stretch": (1, 2),
    "sleepy": (2, 2),
}


def choose_pose(
    now: float,
    *,
    walking: bool,
    airborne: bool,
    jump_velocity: float,
    just_landed: bool,
    blink: bool,
    resting_remaining: float,
    paused: bool,
) -> str:
    """Hold distinct takeoff, midair, and landing frames during each hop."""
    if paused:
        return "sleepy"
    if airborne:
        if jump_velocity > 105:
            return "hop_start"
        if jump_velocity < -105:
            return "hop_land"
        return "hop_air"
    if just_landed:
        return "hop_land"
    if resting_remaining > 3.8:
        return "curious"
    if resting_remaining > 3.2:
        return "stretch"
    if resting_remaining > 0:
        return "sleepy"
    if blink:
        return "smile"
    if walking and now % 5.2 < 0.55:
        return "happy"
    return "idle"


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def _read_rgba_png(path: Path) -> tuple[int, int, bytes]:
    """Decode the project's 8-bit RGBA PNG without an installed image library."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("BooBoo art must be a PNG")
    chunks: list[bytes] = []
    width = height = 0
    offset = 8
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("BooBoo art must be non-interlaced 8-bit RGBA PNG")
        elif kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            break
        offset += length + 12
    if not width or not height or not chunks:
        raise ValueError("BooBoo PNG is incomplete")
    raw = zlib.decompress(b"".join(chunks))
    stride = width * 4
    if len(raw) != height * (stride + 1):
        raise ValueError("BooBoo PNG data size is invalid")
    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        filter_type = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        if filter_type > 4:
            raise ValueError("Unsupported BooBoo PNG filter")
        if filter_type:
            for i in range(stride):
                left = row[i - 4] if i >= 4 else 0
                above = previous[i]
                upper_left = previous[i - 4] if i >= 4 else 0
                if filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = above
                elif filter_type == 3:
                    predictor = (left + above) // 2
                else:
                    base = left + above - upper_left
                    distances = (abs(base - left), abs(base - above), abs(base - upper_left))
                    predictor = (left, above, upper_left)[distances.index(min(distances))]
                row[i] = (row[i] + predictor) & 255
        pixels[y * stride:(y + 1) * stride] = row
        previous = row
    return width, height, bytes(pixels)


def _display_png(pixels: bytes, source_width: int, col: int, row: int) -> bytes:
    """Build a compact color-key-safe frame, preserving source colors."""
    size = (CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE
    scanlines = bytearray()
    for sy in range(row * CELL_SIZE, (row + 1) * CELL_SIZE, DISPLAY_SCALE):
        scanlines.append(0)  # PNG filter: none
        for sx in range(col * CELL_SIZE, (col + 1) * CELL_SIZE, DISPLAY_SCALE):
            index = (sy * source_width + sx) * 4
            if pixels[index + 3] >= ALPHA_CUTOFF:
                scanlines.extend(pixels[index:index + 3])
                scanlines.append(255)
            else:
                scanlines.extend(b"\x00\x00\x00\x00")
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header)
            + _png_chunk(b"IDAT", zlib.compress(scanlines)) + _png_chunk(b"IEND", b""))


class BooBooSprites:
    """Keep all Tk frames alive and mirror them for left-facing movement."""

    def __init__(self, root: tk.Misc) -> None:
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        path = base_dir / "assets" / "booboo-sprites.png"
        width, height, pixels = _read_rgba_png(path)
        expected = CELL_SIZE * GRID_SIZE
        if (width, height) != (expected, expected):
            raise ValueError(f"BooBoo sprite sheet must be {expected}x{expected}")

        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        size = (CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE
        for pose, (col, row) in POSES.items():
            png = _display_png(pixels, width, col, row)
            frame = tk.PhotoImage(master=root, data=base64.b64encode(png))
            self.frames[(pose, 1)] = frame
            mirrored = tk.PhotoImage(master=root, width=size, height=size)
            root.tk.call(str(mirrored), "copy", str(frame), "-from",
                         0, 0, size, size, "-to", 0, 0, "-subsample", -1, 1)
            self.frames[(pose, -1)] = mirrored

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
