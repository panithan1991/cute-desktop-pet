"""Slow emission, detached accumulation, then a sharp turquoise ignition."""
import math
import random

CLOUD_SIZE = 240
CLOUD_FRAMES = 48


def cloud_frame(elapsed, duration):
    p = elapsed / max(duration, .001)
    for start, end, first, count in ((.08,.35,0,12),(.35,.56,12,8),
                                   (.56,.68,20,12),(.68,.85,32,8),(.85,.97,40,8)):
        if start <= p < end:
            return first + min(count-1, int((p-start)/(end-start)*count))
    return None


def cloud_center(origin, facing, rect):
    x,y,w,h = rect
    # Scale the full plume before placement so no wisp is cut at any edge.
    forward = (x+w-origin[0]) if facing >= 0 else (origin[0]-x)
    scale = max(1, math.ceil(CLOUD_SIZE / max(8, min(w,h)-8)), math.ceil(248/max(8,forward-4)))
    half = CLOUD_SIZE / scale / 2 + 3
    cx = max(half, min(w-half, origin[0]-x + facing*125/scale))
    cy = max(half, min(h-half, origin[1]-y - 35/scale))
    return cx, cy, scale


def cloud_sparks(elapsed, duration, seed):
    """Deterministic sparks with an initial lift and gravitational descent."""
    rng=random.Random(seed)
    sparks=[]
    for i in range(36):
        birth=duration*(.57+.27*i/35)
        age=elapsed-birth
        lifetime=min(2.4,duration*.115)
        ox,oy=rng.uniform(-62,62),rng.uniform(-46,20)
        vx,vy=rng.uniform(-16,16),rng.uniform(-28,-10)
        if 0<=age<lifetime:
            x=ox+vx*age+3*math.sin(age*2+i)
            y=oy+vy*age+24*age*age
            fade=1-age/lifetime
            sparks.append((x,y,fade))
    return sparks
