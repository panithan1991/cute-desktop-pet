"""Rebake the repaired running stride without changing other painted clips."""
from PIL import Image
from build_behavior_atlases import ROOT, frame_at, save
from build_dragon_gaits import ground_sequences
from app.pet_sprites import POSES
from app.behavior_art import EXTRA_CLIPS


def build():
    with Image.open(ROOT / 'assets/dragon-motion.png') as atlas:
        frames = [frame_at(atlas, i) for i in range(len(POSES['dragon']))]
    repaired = ground_sequences(frames[0])['run']
    for pose, image in zip(EXTRA_CLIPS['dragon']['run'], repaired):
        frames[POSES['dragon'].index(pose)] = image
    save('dragon', frames)
    preview = Image.new('RGB', (1600, 640), '#e8edf2')
    for i, frame in enumerate(repaired):
        preview.paste(frame, ((i % 10)*160, (i // 10)*160), frame.getchannel('A'))
    preview.save(ROOT.parent / 'dragon-run-wings-fixed-audit.png')
    print('Repaired all 40 running frames; preserved all other clips')


if __name__ == '__main__':
    build()
