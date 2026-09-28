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
        available=(w-mx-6) if facing>0 else mx-6
        scale=max(1,math.ceil(240/max(8,available)),math.ceil(160/max(8,2*min(my,h-my)-4)))
        frame=int(elapsed*9)%32
        side='right' if facing>0 else 'left'
        image=view.clip_image(f'aurora-{side}',frame,240,160,32,scale)
        c.create_image(mx if facing>0 else mx-240/scale,my-80/scale,image=image,anchor='nw')
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
        for wx,wy in horns:
            sx,sy=wx-x,wy-y
            scale=max(2,math.ceil(80/max(8,sy-4)),math.ceil(96/max(8,2*min(sx,w-sx)-4)))
            image=view.clip_image('scale-charge',frame,96,96,32,scale)
            c.create_image(sx-48/scale,sy-80/scale,image=image,anchor='nw')
        for i in range(7):
            a=elapsed*3+i*2.4
            sx=hx+22*math.sin(a);sy=hy+12+i*5
            if 3<sx<w-3 and 3<sy<h-3:
                light=max(0,math.sin(elapsed*9+i))
                if light>.55:
                    c.create_line(sx-1.5,sy,sx+1.5,sy,fill='#b9eaff',width=1)
                    c.create_line(sx,sy-1.5,sx,sy+1.5,fill='#8bd7ff',width=1)
    elif state=='thunder_roar':
        # Several expanding pressure waves; lightning strikes remain fast.
        for i in range(3):
            age=elapsed-duration*(.28+.15*i)
            if not 0<=age<1.5:continue
            scale=max(1,math.ceil(240/max(8,2*min(mx,w-mx,my,h-my)-4)))
            c.create_image(mx,my,image=view.clip_image('shockwave',min(31,int(age/1.5*32)),240,240,32,scale))
        strike,strength,_=flash_at(round(p*(STORM_FRAMES-1)))
        if strength and .25<p<.83:
            available=w-mx-4 if facing>0 else mx-4
            down=getattr(view,'downward',False) is True
            above,below=(40,320) if down else (320,40)
            scale=max(1,math.ceil(632/max(8,available)),math.ceil(above/max(8,my-4)),math.ceil(below/max(8,h-my-4)))
            side='right' if facing>0 else 'left'
            image=view.clip_image(f'roar-{"down" if down else "cone"}-{side}',(view.seed+strike*7)%16,640,360,16,scale)
            nozzle=8 if facing>0 else 631
            c.create_image(mx-nozzle/scale,my-(39 if down else 320)/scale,image=image,anchor='nw')
            fade*=strength
        else:fade*=.28
    view.window.wm_attributes('-alpha',fade)
    return True
