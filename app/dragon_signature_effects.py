"""Bounded, pauseable signature effects, drawn separately from the body."""
import math
from app.dragon_personality import envelope
from app.dragon_lightning import flash_at, STORM_FRAMES


def draw_signature(view,state,elapsed,duration,mouth,horns,facing,rect):
    x,y,w,h=rect;c=view.canvas;p=elapsed/max(.001,duration)
    fade=envelope(p,.20,.78)
    if not fade:return False
    mx,my=mouth[0]-x,mouth[1]-y
    hx,hy=(horns[0][0]+horns[1][0])/2-x,(horns[0][1]+horns[1][1])/2-y
    if state=='aurora_breath':
        if p < 0.20 or p >= 0.82:
            return False
        from app.dragon_fire_layout import FIRE_NOZZLES
        available=(w-mx-6) if facing>0 else mx-6
        scale=max(1,math.ceil(240/max(8,available)),math.ceil(160/max(8,2*min(my,h-my)-4)))
        t_active = (p - 0.20) / 0.62
        if t_active < 0.14:
            frame = min(7, int(t_active / 0.14 * 8))
        elif t_active < 0.82:
            frame = 8 + int(elapsed * 12) % 16
        else:
            frame = 24 + min(7, int((t_active - 0.82) / 0.18 * 8))
        side='right' if facing>0 else 'left'
        image=view.clip_image(f'aurora-flame-{side}',frame,240,160,32,scale)
        nx,ny=FIRE_NOZZLES[frame]
        if facing<0:nx=239-nx
        c.create_image(mx-nx/scale,my-ny/scale,image=image,anchor='nw')
        fade_active = min(1.0, (p - 0.20) / 0.04, (0.82 - p) / 0.04)
        fade = fade_active * fade_active * (3 - 2 * fade_active)
    elif state=='ember_bubbles':
        for i in range(8):
            birth=duration*(.28+.06*i);age=elapsed-birth
            if not 0<=age<3.6:continue
            if i not in view.ring_origins:view.ring_origins[i]=mouth
            ox,oy=view.ring_origins[i];t=age/3.6
            vertical=1 if getattr(view,'downward',False) is True else -1
            sx,sy=ox-x+facing*(4+120*t),oy-y+vertical*65*t**1.4+3*math.sin(age*2+i)*t
            if not 4<sx<w-4 or not 4<sy<h-4:continue
            scale=max(1,math.ceil(96/max(8,2*min(sx,w-sx,sy,h-sy)-4)))
            image=view.clip_image('ember-bubble',min(35,int(t*36)),96,96,36,scale)
            c.create_image(sx,sy,image=image)
    elif state=='static_charge':
        # Painted corona remains attached to each horn. Tiny specular glints
        # crawl over existing scales; no structural spike/limb is invented.
        frame=int(elapsed*11)%32
        for i,(wx,wy) in enumerate(horns):
            sx,sy=wx-x,wy-y
            scale=max(2,math.ceil(108/max(8,sy-4)),math.ceil(128/max(8,2*min(sx,w-sx)-4)))
            part='rear' if (i==0)==(facing>0) else 'front'
            side='right' if facing>0 else 'left'
            image=view.clip_image(f'charge-{part}-{side}',frame,128,128,32,scale)
            c.create_image(sx-(64 if facing>0 else 63)/scale,sy-108/scale,image=image,anchor='nw')
        for i in range(7):
            a=elapsed*3+i*2.4
            sx=hx+22*math.sin(a);sy=hy+12+i*5
            if 3<sx<w-3 and 3<sy<h-3:
                light=max(0,math.sin(elapsed*9+i))
                if light>.55:
                    c.create_line(sx-1.5,sy,sx+1.5,sy,fill='#b9eaff',width=1)
                    c.create_line(sx,sy-1.5,sx,sy+1.5,fill='#8bd7ff',width=1)
    elif state=='thunder_roar':
        # Three or four separate branching channels, with the same short
        # exposure/dark-gap rhythm as horn lightning. Every root is the mouth.
        strike,strength,_=flash_at(round(p*(STORM_FRAMES-1)))
        if not strength or not .20<p<.86:return False
        count=3+(view.seed%2)
        side='right' if facing>0 else 'left'
        for i in range(count):
            index=(view.seed+strike*7+i*5)%16
            from app.dragon_stunt_effect_layout import TREE_BOUNDS
            l,t,r,b=TREE_BOUNDS[index][side]
            available=w-mx-4 if facing>0 else mx-4
            extent=r-280 if facing>0 else 280-l
            scale=max(2,math.ceil(extent/max(8,available)),
                      math.ceil((380-t)/max(8,my-4)),math.ceil((b-380)/max(8,h-my-4)))
            image=view.tree(side,index,scale)
            c.create_image(mx-280/scale,my-380/scale,image=image,anchor='nw')
        fade*=strength
    view.window.wm_attributes('-alpha',fade)
    return True
