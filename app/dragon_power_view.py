"""Transparent fantasy flame and lightning overlay; no body pixels are edited."""

from collections import OrderedDict
from pathlib import Path
import math
import sys
import tkinter as tk

from app.dragon_lightning import flash_at, STORM_FRAMES
from app.dragon_power_geometry import FIRE_WIDTH, FIRE_HEIGHT, fire_frame, overlay_rect, gust_transform
from app.dragon_weather_layout import LIGHTNING_BOUNDS
from app.dragon_fire_layout import FIRE_NOZZLES
from app.dragon_stunt_effect_layout import TREE_BOUNDS
from app.dragon_cloud import cloud_frame, cloud_center, cloud_overlay_rect, gas_ring, RING_BIRTHS, cloud_sparks, CLOUD_SIZE, CLOUD_FRAMES

SKY_RING_LIFETIME = 6.0
from app.window_style import configure_overlay, configure_pet_window


class DragonPowerView:
    def __init__(self, parent, rng):
        self.parent=parent
        self.rng = rng
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        configure_pet_window(self.window)
        background = configure_overlay(self.window)
        self.canvas = tk.Canvas(self.window, background=background, highlightthickness=0,borderwidth=0)
        self.canvas.pack()
        self.weather = OrderedDict()
        self.clip_frames = OrderedDict()
        self.previous_state, self.previous_elapsed = None,0
        self.seed = 0
        self.last_rect = None
        self.ring_origins={}

    def hide(self):
        self.window.withdraw()
        self.previous_state = None

    def flame(self, index, facing, scale):
        side = "left" if facing < 0 else "right"
        return self.clip_image(f'fire-{side}', index, FIRE_WIDTH, FIRE_HEIGHT, 32, scale)

    def asset_path(self,name,extension='png'):
        base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
        platform="windows" if sys.platform=="win32" else "macos"
        return str(base/f"assets/runtime/dragon-{platform}/{name}.{extension}")

    def vortex(self,index,facing,scale=1):
        side="left" if facing<0 else "right"
        return self.clip_image(f'vortex-{side}', index, 180, 200, 32, scale)

    def lightning(self,index,scale):
        key=index,scale
        if key not in self.weather:
            image=tk.PhotoImage(master=self.window,file=self.asset_path(f"lightning-{index:02d}"))
            self.weather[key]=image.subsample(scale,scale) if scale>1 else image
        self.weather.move_to_end(key)
        if len(self.weather)>8:self.weather.popitem(last=False)
        return self.weather[key]

    def clip_image(self,name,index,width,height,count,scale=1):
        if not 0<=index<count:raise IndexError(index)
        key=name,index,scale
        if key in self.clip_frames:
            self.clip_frames.move_to_end(key)
            return self.clip_frames[key]
        original_key=name,index,1
        if original_key not in self.clip_frames:
            original=tk.PhotoImage(master=self.window,file=self.asset_path(f'fx/{name}/{index:02d}'))
            if (original.width(),original.height()) != (width,height):
                raise ValueError(f'Invalid effect frame {name}:{index}')
            self.clip_frames[original_key]=original
        original=self.clip_frames[original_key]
        self.clip_frames[key]=original if scale==1 else original.subsample(scale,scale)
        self.clip_frames.move_to_end(key)
        while len(self.clip_frames)>96:self.clip_frames.popitem(last=False)
        return self.clip_frames[key]

    def tree(self,side,index,scale):
        key=side,index,scale
        if key not in self.weather:
            image=tk.PhotoImage(master=self.window,file=self.asset_path(f"tree-{side}-{index:02d}"))
            self.weather[key]=image.subsample(scale,scale) if scale>1 else image
        self.weather.move_to_end(key)
        if len(self.weather)>12:self.weather.popitem(last=False)
        return self.weather[key]

    def draw_trees(self,horns,index,x,y,w,h,third=False):
        roots=list(zip(('left','right'),horns))
        if third:roots.append(('up',((horns[0][0]+horns[1][0])/2,(horns[0][1]+horns[1][1])/2)))
        for side,(hx,hy) in roots:
            mx,my=hx-x,hy-y;l,t,r,b=TREE_BOUNDS[index][side]
            scale=max(1,math.ceil((280-l)/max(8,mx-2)),math.ceil((r-280)/max(8,w-mx-2)),
                      math.ceil((380-t)/max(8,my-2)),math.ceil((b-380)/max(8,h-my-2)))
            image=self.tree(side,index,scale)
            self.canvas.create_image(mx-280/scale,my-380/scale,image=image,anchor='nw')

    def draw(self,state,elapsed,duration,mouth,horns,facing,bounds,topmost):
        if state not in {"fire","cloud_flame","storm_hover","wing_gust","belly_smoke","roll_lightning","fury"}:
            self.hide(); return
        if state != self.previous_state or elapsed < self.previous_elapsed:
            self.seed = self.rng.getrandbits(24)
            self.ring_origins={}
        self.previous_state,self.previous_elapsed = state,elapsed
        origin = mouth if state in {"fire","cloud_flame","wing_gust","belly_smoke","fury"} else ((horns[0][0]+horns[1][0])/2,(horns[0][1]+horns[1][1])/2)
        if state == 'cloud_flame':
            # A mouth-anchored emitter feeds a cloud with its own fixed origin.
            # Recoil and head movement cannot pull the cloud into the face.
            if elapsed >= duration*.07 and 'cloud' not in self.ring_origins:
                self.ring_origins['cloud'] = mouth
            origin = self.ring_origins.get('cloud', mouth)
        x,y,w,h = cloud_overlay_rect(origin,bounds,facing) if state=='cloud_flame' else overlay_rect(origin,bounds)
        if self.last_rect != (x,y,w,h):
            self.window.geometry(f"{w}x{h}{x:+d}{y:+d}"); self.canvas.configure(width=w,height=h)
            self.last_rect = x,y,w,h
        self.window.wm_attributes("-topmost",topmost)
        c = self.canvas; c.delete("all")
        if state == 'cloud_flame':
            index = cloud_frame(elapsed,duration)
            cx,cy,scale = cloud_center(origin,facing,(x,y,w,h))
            visible=False
            target=(cx+x,cy+y)
            for i,birth in enumerate(RING_BIRTHS):
                if elapsed<duration*birth:continue
                key=('gas',i)
                if key not in self.ring_origins:self.ring_origins[key]=mouth
                ring=gas_ring(elapsed,duration,i,self.ring_origins[key],target)
                if ring is None:continue
                sx,sy,frame=ring;sx-=x;sy-=y
                shrink=max(scale,math.ceil(96/max(8,2*min(sx,w-sx,sy,h-sy)-4)))
                side='left' if facing<0 else 'right'
                c.create_image(sx,sy,image=self.clip_image(f'jade-rings-{side}',frame,96,96,24,shrink))
                visible=True
            # Arriving rings dissolve underneath the accumulated cloud, with
            # fixed world origins rather than a loop teleporting back to mouth.
            if index is not None:
                c.create_image(cx,cy,image=self.clip_image('cloud-flame',index,CLOUD_SIZE,CLOUD_SIZE,CLOUD_FRAMES,scale))
                visible=True
            if not visible:self.window.withdraw();return
            for dx,dy,fade in cloud_sparks(elapsed,duration,self.seed):
                sx,sy=cx+dx/scale,cy+dy/scale
                if not 6<sx<w-6 or not 6<sy<h-6:continue
                color='#caffee' if fade>.72 else '#65efd7' if fade>.4 else '#299b90' if fade>.15 else '#245b60'
                radius=max(.5,2.4*fade/scale)
                c.create_line(sx-.6,sy-4*fade/scale,sx,sy,fill=color,width=max(1,2*fade/scale))
                c.create_oval(sx-radius,sy-radius,sx+radius,sy+radius,fill=color,outline='')
                if fade>.8:
                    c.create_line(sx-3/scale,sy,sx+3/scale,sy,fill='#edfff6',width=1)
            opacity=max(0,min(1,(.97-elapsed/max(duration,.001))/.12)) if sys.platform=='win32' else 1
            self.window.wm_attributes('-alpha',opacity)
        elif state == "fire":
            index = fire_frame(elapsed,duration)
            if index is None:
                self.window.withdraw(); return
            mx,my = mouth[0]-x,mouth[1]-y
            available = w-mx-10 if facing>=0 else mx-10
            scale = max(1,math.ceil(FIRE_WIDTH/max(8,available)),
                        math.ceil(118/max(8,2*min(my,h-my)-4)))
            image = self.flame(index,facing,scale)
            nx,ny=FIRE_NOZZLES[index]
            if facing<0:nx=239-nx
            c.create_image(mx-nx/scale,my-ny/scale,image=image,anchor="nw")
            # A few flowing glints travel beyond the flame core, never behind
            # the mouth. Their position follows the frozen activity clock.
            for i in range(9):
                travel = (elapsed*.55+i*.137)%1
                distance = (24+190*travel)/scale
                sx = mx+(1 if facing>=0 else -1)*distance
                sy = my+math.sin(i*2.3+elapsed*3)*(8+26*travel)/scale
                if 8<sx<w-8 and 8<sy<h-8:
                    c.create_line(sx-2,sy,sx+2,sy,fill="#fff2bc",width=1)
                    c.create_line(sx,sy-2,sx,sy+2,fill="#ffbd43",width=1)
        elif state == "wing_gust":
            p = elapsed/max(duration,.001)
            if p<.15 or p>.94:
                self.window.withdraw(); return
            envelope = min(1,(p-.15)/.15,(.94-p)/.2)
            cx,cy = gust_transform((mouth[0]-x,mouth[1]-y),(w,h),-facing,p)
            t=(p-.15)/.79
            index=min(7,int(t/.2*8)) if t<.2 else 8+int(elapsed*12)%16 if t<.8 else 24+min(7,int((t-.8)/.2*8))
            scale=max(1,math.ceil(200/max(8,cy-4)),math.ceil(180/max(8,2*min(cx,w-cx)-4)))
            image=self.vortex(index,-facing,scale)
            c.create_image(cx,cy,image=image,anchor="s")
            self.window.wm_attributes("-alpha",max(0,min(1,envelope)))
        elif state=='belly_smoke':
            visible=False
            for i,at in enumerate((.27,.47,.67)):
                age=elapsed-duration*at
                if not 0<=age<SKY_RING_LIFETIME:continue
                visible=True
                if i not in self.ring_origins:self.ring_origins[i]=mouth
                ox,oy=self.ring_origins[i];t=age/SKY_RING_LIFETIME
                mx=max(50,min(w-50,ox-x+6*math.sin(age*1.2+i)-3))
                my=max(12,min(h-12,oy-y-8-100*t))
                scale=max(1,math.ceil(96/max(8,2*min(my,h-my)-4)))
                image=self.clip_image('sky-rings',min(23,int(t*24)),96,96,24,scale)
                c.create_image(mx,my,image=image)
            if not visible:self.window.withdraw();return
            self.window.wm_attributes('-alpha',1)
        elif state=='fury':
            p=elapsed/max(duration,.001)
            envelope=max(0,min(1,(p-.12)/.12,(.95-p)/.16))
            if not envelope:self.window.withdraw();return
            mx,my=mouth[0]-x,mouth[1]-y
            scale=max(1,math.ceil(150/max(8,my-4)),math.ceil(50/max(8,h-my-4)),math.ceil(210/max(8,2*min(mx,w-mx)-4)))
            image=self.clip_image('fury-aura',int(elapsed*12)%32,240,200,32,scale)
            c.create_image(mx-120/scale,my-150/scale,image=image,anchor='nw')
            # New vortices are born on alternate downstrokes, then drift freely.
            for i,at in enumerate((.22,.38,.54,.70)):
                age=elapsed-duration*at
                if not 0<=age<3:continue
                sign=-1 if i%2==0 else 1;t=age/3
                cx,cy=gust_transform((mx+sign*36,my+12),(w,h),sign,.15+.79*t)
                frame=min(7,int(t/.2*8)) if t<.2 else 8+int(age*12)%16 if t<.8 else 24+min(7,int((t-.8)/.2*8))
                shrink=max(2,math.ceil(200/max(8,cy-4)),math.ceil(180/max(8,2*min(cx,w-cx)-4)))
                c.create_image(cx,cy,image=self.vortex(frame,sign,shrink),anchor='s')
            strike,strength,_=flash_at(round(p*(STORM_FRAMES-1)))
            if strength:self.draw_trees(horns,(self.seed+strike*7919)%16,x,y,w,h,third=bool(self.seed%2))
            self.window.wm_attributes('-alpha',envelope)
        elif state=='roll_lightning':
            strike,strength,_=flash_at(round(elapsed/max(duration,.001)*(STORM_FRAMES-1)))
            if not strength:self.window.withdraw();return
            self.draw_trees(horns,(self.seed+strike*7919)%16,x,y,w,h)
            self.window.wm_attributes('-alpha',strength*.8)
        else:
            strike,strength,growth = flash_at(round(elapsed/max(duration,.001)*(STORM_FRAMES-1)))
            if not strength:
                self.window.withdraw(); return
            index=(self.seed+strike*7919)%16
            mx,my=origin[0]-x,origin[1]-y
            l,t,r,b=LIGHTNING_BOUNDS[index]
            scale=max(1,math.ceil((280-l)/max(8,mx-2)),
                      math.ceil((r-280)/max(8,w-mx-2)),
                      math.ceil((380-t)/max(8,my-2)),
                      math.ceil((b-380)/max(8,h-my-2)))
            image=self.lightning(index,scale)
            c.create_image(mx-280/scale,my-380/scale,image=image,anchor="nw")
            self.window.wm_attributes("-alpha",strength)
        if state == "fire":
            self.window.wm_attributes("-alpha",1)
        self.window.deiconify()
        if state=='fury':self.window.lower(self.parent)
        else:self.window.lift(self.parent)

    def close(self):
        self.window.destroy()
