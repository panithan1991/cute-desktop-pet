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
    """Random long branches in all quadrants, stable during one short strike."""
    w,h = size
    rng = random.Random(seed+strike*7919)
    paths = []
    center = ((origins[0][0]+origins[1][0])/2, (origins[0][1]+origins[1][1])/2)
    for side,origin in enumerate(origins):
        for _ in range(2):
            # Start outward to keep downward strikes from crossing the face.
            sign = -1 if side == 0 else 1
            first = (origin[0]+sign*rng.uniform(22,38),origin[1]-rng.uniform(5,20))
            angle = rng.uniform(-math.pi,math.pi)
            length = rng.uniform(170,280)
            target = (center[0]+math.cos(angle)*length,center[1]+math.sin(angle)*length)
            def clamp(point):
                return (max(12,min(w-12,point[0])),max(12,min(h-12,point[1])))
            target = clamp(target)
            path = [clamp(origin),clamp(first)]
            for j in range(1,11):
                t = j/10
                point = (first[0]*(1-t)+target[0]*t+rng.uniform(-12,12),
                         first[1]*(1-t)+target[1]*t+rng.uniform(-12,12))
                if point[1] > center[1] and abs(point[0]-center[0]) < 40:
                    point = (center[0]+sign*43,point[1])
                path.append(clamp(point))
            paths.append(path)
            for j in (4,7):
                branch_angle = angle+rng.uniform(-1.1,1.1)
                p = path[j]
                end = clamp((p[0]+math.cos(branch_angle)*rng.uniform(30,65),
                             p[1]+math.sin(branch_angle)*rng.uniform(30,65)))
                paths.append([p,clamp(((p[0]+end[0])/2+rng.uniform(-7,7),
                                      (p[1]+end[1])/2+rng.uniform(-7,7))),end])
    return paths


def gust_paths(origin,size,direction,progress,elapsed):
    """A drifting rotating funnel emitted on the active wing's side."""
    w,h = size
    direction = 1 if direction>=0 else -1
    available = w-origin[0]-45 if direction>0 else origin[0]-45
    travel = max(0,min(235,available))
    t = max(0,min(1,(progress-.15)/.79))
    growth = min(1,t/.23)
    cx = origin[0]+direction*(12+travel*t)
    cy = max(92,min(h-28,origin[1]-35*t))
    paths = []
    for strand in range(5):
        path = []
        for j in range(91):
            v = j/90
            angle = v*math.tau*3.5+elapsed*5+strand*math.tau/5
            radius = (7+28*v)*growth
            px = cx+math.cos(angle)*radius
            py = cy-v*100*growth+math.sin(angle)*radius*.18
            path.append((max(6,min(w-6,px)),max(6,min(h-6,py))))
        paths.append(path)
    return paths
