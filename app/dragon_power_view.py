"""Transparent fantasy flame and lightning overlay; no body pixels are edited."""

from collections import OrderedDict
from pathlib import Path
import math
import sys
import tkinter as tk

from app.dragon_lightning import flash_at, STORM_FRAMES
from app.dragon_power_geometry import FIRE_WIDTH, FIRE_HEIGHT, fire_frame, overlay_rect, gust_transform
from app.dragon_weather_layout import LIGHTNING_BOUNDS
from app.window_style import configure_overlay, configure_pet_window


class DragonPowerView:
    def __init__(self, parent, rng):
        self.rng = rng
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        configure_pet_window(self.window)
        background = configure_overlay(self.window)
        self.canvas = tk.Canvas(self.window, background=background, highlightthickness=0,borderwidth=0)
        self.canvas.pack()
        self.frames, self.scaled = {}, OrderedDict()
        self.weather = OrderedDict()
        self.previous_state, self.previous_elapsed = None,0
        self.seed = 0
        self.last_rect = None

    def hide(self):
        self.window.withdraw()
        self.previous_state = None

    def flame(self, index, facing, scale):
        side = "left" if facing < 0 else "right"
        if side not in self.frames:
            base = Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
            platform = "windows" if sys.platform == "win32" else "macos"
            atlas = tk.PhotoImage(master=self.window,file=str(base/f"assets/runtime/dragon-{platform}/fire-{side}.png"))
            images = []
            for i in range(32):
                image = tk.PhotoImage(master=self.window,width=FIRE_WIDTH,height=FIRE_HEIGHT)
                x,y = i%4*FIRE_WIDTH,i//4*FIRE_HEIGHT
                self.window.tk.call(str(image),"copy",str(atlas),"-from",x,y,x+FIRE_WIDTH,y+FIRE_HEIGHT,"-to",0,0)
                images.append(image)
            self.frames[side] = images
        original = self.frames[side][index]
        if scale == 1:
            return original
        key = side,index,scale
        if key not in self.scaled:
            self.scaled[key] = original.subsample(scale,scale)
        self.scaled.move_to_end(key)
        if len(self.scaled)>64:
            self.scaled.popitem(last=False)
        return self.scaled[key]

    def asset_path(self,name):
        base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
        platform="windows" if sys.platform=="win32" else "macos"
        return str(base/f"assets/runtime/dragon-{platform}/{name}.png")

    def vortex(self,index,facing,scale=1):
        side="left" if facing<0 else "right"
        key=f"vortex-{side}"
        if key not in self.frames:
            atlas=tk.PhotoImage(master=self.window,file=self.asset_path(key))
            frames=[]
            for i in range(32):
                image=tk.PhotoImage(master=self.window,width=180,height=200)
                x,y=i%4*180,i//4*200
                self.window.tk.call(str(image),"copy",str(atlas),"-from",x,y,x+180,y+200,"-to",0,0)
                frames.append(image)
            self.frames[key]=frames
        original=self.frames[key][index]
        if scale==1:return original
        cache_key=key,index,scale
        if cache_key not in self.scaled:self.scaled[cache_key]=original.subsample(scale,scale)
        self.scaled.move_to_end(cache_key)
        if len(self.scaled)>64:self.scaled.popitem(last=False)
        return self.scaled[cache_key]

    def lightning(self,index,scale):
        key=index,scale
        if key not in self.weather:
            image=tk.PhotoImage(master=self.window,file=self.asset_path(f"lightning-{index:02d}"))
            self.weather[key]=image.subsample(scale,scale) if scale>1 else image
        self.weather.move_to_end(key)
        if len(self.weather)>8:self.weather.popitem(last=False)
        return self.weather[key]

    def draw(self,state,elapsed,duration,mouth,horns,facing,bounds,topmost):
        if state not in {"fire","storm_hover","wing_gust"}:
            self.hide(); return
        if state != self.previous_state or elapsed < self.previous_elapsed:
            self.seed = self.rng.getrandbits(24)
        self.previous_state,self.previous_elapsed = state,elapsed
        origin = mouth if state in {"fire","wing_gust"} else ((horns[0][0]+horns[1][0])/2,(horns[0][1]+horns[1][1])/2)
        x,y,w,h = overlay_rect(origin,bounds)
        if self.last_rect != (x,y,w,h):
            self.window.geometry(f"{w}x{h}{x:+d}{y:+d}"); self.canvas.configure(width=w,height=h)
            self.last_rect = x,y,w,h
        self.window.wm_attributes("-topmost",topmost)
        c = self.canvas; c.delete("all")
        if state == "fire":
            index = fire_frame(elapsed,duration)
            if index is None:
                self.window.withdraw(); return
            mx,my = mouth[0]-x,mouth[1]-y
            available = w-mx-10 if facing>=0 else mx-10
            scale = max(1,math.ceil(FIRE_WIDTH/max(8,available)),
                        math.ceil(118/max(8,2*min(my,h-my)-4)))
            image = self.flame(index,facing,scale)
            c.create_image(mx-4/scale if facing>=0 else mx+4/scale,my,
                           image=image,anchor="w" if facing>=0 else "e")
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

    def close(self):
        self.window.destroy()
