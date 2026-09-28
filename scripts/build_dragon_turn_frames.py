"""Bake dragon turn-around frames for smooth realistic 180-degree ground transitions."""
import sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_behavior_atlases import inbetweens, frame_at


def build():
    with Image.open(ROOT / "assets/dragon-motion.png") as atlas:
        idle = frame_at(atlas, 0)
    front = Image.open(ROOT / "assets/source/dragon-front.png").convert("RGBA")
    mirrored_idle = ImageOps.mirror(idle)

    first_half = inbetweens(idle, front, 6)
    second_half = inbetweens(front, mirrored_idle, 6)
    turn_frames = first_half + second_half + [mirrored_idle]
    assert len(turn_frames) == 13

    for platform in ("macos", "windows"):
        for side in ("left", "right"):
            out = ROOT / f"assets/runtime/dragon-{platform}/body-fx/{side}"
            out.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(turn_frames):
                f = ImageOps.mirror(frame) if side == "left" else frame
                name = f"dragon_turn_{i:02d}"
                if platform == "windows":
                    rgb = Image.new("RGB", f.size, "#ff00ff")
                    alpha = f.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
                    rgb.paste(f, mask=alpha)
                    rgb.save(out / f"{name}.ppm")
                else:
                    f.save(out / f"{name}.png", optimize=True)

    print(f"Baked {len(turn_frames)} dragon turn frames for both platforms and sides.")


if __name__ == "__main__":
    build()
