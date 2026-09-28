"""Slow emission, detached accumulation, then a sharp turquoise ignition."""
import math
import random

CLOUD_SIZE = 240
CLOUD_FRAMES = 48
DRAGON_VISIBLE_SPAN = 98  # Measured from the canonical idle sprite alpha bounds.
CLOUD_DISTANCE = 2.5 * DRAGON_VISIBLE_SPAN


def cloud_frame(elapsed, duration):
    p = elapsed / max(duration, .001)
    for start, end, first, count in ((.20,.44,0,12),(.44,.56,12,8),
                                   (.56,.68,20,12),(.68,.85,32,8),(.85,.97,40,8)):
        if start <= p < end:
            return first + min(count-1, int((p-start)/(end-start)*count))
    return None


def cloud_overlay_rect(origin,bounds,facing):
    left,top,right,bottom=bounds
    w,h=min(840,right-left),min(480,bottom-top)
    offset=min(140,w/4) if facing>=0 else w-min(140,w/4)
    return (max(left,min(round(origin[0]-offset),right-w)),
            max(top,min(round(origin[1]-h*.75),bottom-h)),w,h)


def cloud_center(origin, facing, rect):
    x,y,w,h = rect
    # Scale the full plume before placement so no wisp is cut at any edge.
    forward = (x+w-origin[0]) if facing >= 0 else (origin[0]-x)
    scale = max(1, math.ceil(CLOUD_SIZE / max(8, min(w,h)-8)), math.ceil((CLOUD_DISTANCE+124)/max(8,forward-4)))
    half = CLOUD_SIZE / scale / 2 + 3
    cx = max(half, min(w-half, origin[0]-x + facing*CLOUD_DISTANCE/scale))
    cy = max(half, min(h-half, origin[1]-y - 65/scale))
    return cx, cy, scale


RING_BIRTHS=(.07,.105,.14,.175,.21,.245)
RING_TRAVEL=2.6


def gas_ring(elapsed,duration,index,origin,target):
    age=elapsed-duration*RING_BIRTHS[index]
    if not 0<=age<RING_TRAVEL:return None
    t=age/RING_TRAVEL
    # Horizontal momentum stays forward while gentle thermal buoyancy lifts
    # the ring. The hollow torus opens, then mixes away at the cloud boundary.
    arrival=(target[0]+((index%3)-1)*12,target[1]+(index%2)*10-5)
    sign=1 if arrival[0]>=origin[0] else -1
    launch_x=origin[0]+sign*18
    x=launch_x+(arrival[0]-launch_x)*t
    y=origin[1]+(arrival[1]-origin[1])*t-8*math.sin(t*math.pi)
    return x,y,min(23,int(t*24))


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
