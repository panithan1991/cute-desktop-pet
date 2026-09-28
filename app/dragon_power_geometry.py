"""Desktop-sized dragon powers, separate from the small body sprite."""

import math
import random

FIRE_WIDTH, FIRE_HEIGHT = 240, 160
FIRE_FRAMES = 32
OVERLAY_WIDTH, OVERLAY_HEIGHT = 560, 480


def fire_frame(elapsed, duration):
    p = elapsed/max(duration,.001)
    if p < .04 or p >= .96:
        return None
    if p < .14:
        return min(7,int((p-.04)/.1*8))
    if p < .84:
        return 8+int(elapsed*12)%16
    return 24+min(7,int((p-.84)/.12*8))


def overlay_rect(origin, bounds):
    left,top,right,bottom = bounds
    w,h = min(OVERLAY_WIDTH,right-left),min(OVERLAY_HEIGHT,bottom-top)
    return (max(left,min(round(origin[0]-w/2),right-w)),
            max(top,min(round(origin[1]-h/2),bottom-h)), w,h)


def bolt_paths(origins, size, seed, strike):
    """Lateral tree-shaped discharge: outward trunk, forks and fine twigs."""
    w,h=size
    rng=random.Random(seed+strike*7919)
    paths=[]
    def clamp(p): return (max(12,min(w-12,p[0])),max(12,min(h-12,p[1])))
    def branch(start,sign,length,slope,depth):
        points=[clamp(start)]
        count=20 if depth==0 else 12 if depth==1 else 7
        for j in range(1,count):
            t=j/(count-1)
            # Progress always outward; jitter is transverse, never backwards.
            x=start[0]+sign*length*t
            y=start[1]+slope*length*t+rng.uniform(-1,1)*(5 if depth==0 else 3)
            points.append(clamp((x,y)))
        paths.append(points)
        if depth<2:
            for fraction in ((.25,.45,.65,.8) if depth==0 else (.42,.72)):
                at=points[round(fraction*(count-1))]
                branch(at,sign,length*rng.uniform(.25,.43),
                       slope+rng.choice((-1,1))*rng.uniform(.3,.7),depth+1)
    for side,origin in enumerate(origins):
        sign=-1 if side==0 else 1
        branch(origin,sign,rng.uniform(195,250),rng.uniform(-.5,.1),0)
    return paths


def gust_transform(origin,size,direction,progress):
    """Cloud funnel tip moves away from the flapping wing without clipping."""
    w,h=size
    direction=1 if direction>=0 else -1
    available=w-origin[0]-90 if direction>0 else origin[0]-90
    travel=max(0,min(235,available))
    t=max(0,min(1,(progress-.15)/.79))
    cx=origin[0]+direction*(12+travel*t)
    return max(12,min(w-12,cx)),max(12,min(h-12,origin[1]-35*t))
