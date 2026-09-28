"""One 50% aerobatics decision per flight, driven by the pauseable cruise clock."""
import math
from app.pet_motion import BibiFlightMotion
from app.behavior_art import EXTRA_CLIPS
from app.dragon_personality import AIR_GESTURES, envelope


class DragonFlightMotion(BibiFlightMotion):
    mode='walk'
    requested_mode='walk'
    roll_chosen=False
    roll_turns=0
    roll_start=0.0
    roll_duration=0.0

    def launch(self):
        if not super().launch():return False
        self.mode=self.requested_mode
        self.requested_mode='walk'
        self.perch_side=None
        self.roll_chosen=self.rng.random()<.5 and self.mode=='walk'
        self.roll_turns=self.rng.choice((2,3)) if self.roll_chosen else 0
        self.roll_start=math.ceil(self.rng.uniform(4,10)/1.8)*1.8
        self.roll_duration=2.4+3*self.roll_turns
        return True

    def reset(self,x,ground):
        super().reset(x,ground)
        self.roll_chosen=False
        self.mode=self.requested_mode='walk'
        self.perch_side=None

    def depart(self):
        if self.state=='perched':
            self.state='unperch';self.elapsed=0

    def _perch_target(self,left,top,right,ground):
        if not getattr(self,'perch_side',None):
            self.perch_side=self.rng.choice(('left','right','top'))
        self.perch_x,self.perch_y=self.x,self.y
        self.perch_target_x=left if self.perch_side=='left' else right if self.perch_side=='right' else self.rng.uniform(left+(right-left)*.25,left+(right-left)*.75)
        self.perch_target_y=top if self.perch_side=='top' else top+(ground-top)*self.rng.uniform(.25,.55)
        self.direction=-1 if self.perch_side=='right' else 1
        self.perch_duration=self.rng.uniform(50,80)

    def perch_pose(self,behavior):
        if self.mode!='perch_landing':return None
        name='top_perch' if getattr(self,'perch_side',None)=='top' else 'wall_perch'
        frames=EXTRA_CLIPS['dragon'][name]
        if self.state=='cruise':
            p=min(1,self.elapsed/max(.001,self.cruise_duration)/.66)
            return frames[min(12,int(p*12))]
        if self.state=='unperch':return frames[max(0,12-int(self.elapsed/1.2*12))]
        if self.state!='perched':return None
        if behavior.state=='idle':return frames[12]
        p=min(1,behavior.elapsed/max(.001,behavior.duration))
        # Keep the paws planted while the mouth opens, holds, and closes.
        index=12+int(p/.22*8) if p<.22 else 20 if p<.82 else 20+int((p-.82)/.18*19)
        return frames[min(39,index)]

    def step(self,seconds,left,top,right,ground):
        if self.state in {'perched','unperch'}:
            if self.paused:return
            self.elapsed+=min(max(seconds,0),.1)
            self.x=max(left,min(right,self.x));self.y=max(top,min(ground,self.y))
            if self.state=='unperch' and self.elapsed>=1.2:
                self.state='landing';self.elapsed=0;self.landing_y=self.y
            return
        if self.mode not in AIR_GESTURES or self.state!='cruise':
            super().step(seconds,left,top,right,ground)
            return
        if self.paused:return
        dt=min(max(seconds,0),.1)
        old=self.elapsed;self.elapsed+=dt
        p=min(1,self.elapsed/max(.001,self.cruise_duration))
        e=envelope(p,.22,.78)
        high=top+(ground-top)*self.altitude
        wave=min(64,(ground-top)*.08)*math.sin(self.elapsed*self.wave_speed)
        if self.mode=='dive_recover':
            # A bounded smooth dive and climb, with zero displacement/slope
            # at both ends; it cannot intersect the desktop or jump on exit.
            self.y=high+wave+min(180,(ground-high)*.45)*math.sin(math.pi*p)**4
            speed=self.speed*(1+1.1*math.sin(math.pi*p)**2)
        elif self.mode=='hover_float':
            self.y=high+wave*(1-e)+3*math.sin(self.elapsed*2)*e
            speed=self.speed*(1-e)
        elif self.mode=='air_brake':
            self.y=high+wave-16*e
            # Slow through zero before a small backwards drift, then recover.
            speed=self.speed*(1-1.18*e)
        else:
            if old==0:self._perch_target(left,top,right,ground)
            t=min(1,p/.66);s=t*t*(3-2*t)
            self.x=self.perch_x+(self.perch_target_x-self.perch_x)*s
            self.y=self.perch_y+(self.perch_target_y-self.perch_y)*s
            speed=0
        if self.mode!='perch_landing':self.x+=self.direction*speed*dt
        if self.mode!='perch_landing':
            if self.x>=right:self.x,self.direction=right,-1
            elif self.x<=left:self.x,self.direction=left,1
        self.y=max(top,min(ground,self.y))
        if p>=1:
            self.landing_y=self.y;self.elapsed=0
            self.state='perched' if self.mode=='perch_landing' else 'landing'

    def maneuver_pose(self):
        if self.mode not in AIR_GESTURES or self.mode=='perch_landing' or self.state!='cruise':return None
        p=min(1,self.elapsed/max(.001,self.cruise_duration))
        frames=EXTRA_CLIPS['dragon'][self.mode]
        return frames[min(len(frames)-1,int(p*len(frames)))]

    @property
    def rolling(self):
        return self.roll_chosen and self.state=='cruise' and self.roll_start<=self.elapsed<self.roll_start+self.roll_duration

    @property
    def roll_elapsed(self):return self.elapsed-self.roll_start

    @property
    def roll_spinning(self):
        return self.rolling and 1.2<=self.roll_elapsed<1.2+3*self.roll_turns

    @property
    def hover_elapsed(self):
        completed=self.roll_chosen and self.state=='cruise' and self.elapsed>=self.roll_start+self.roll_duration
        return self.elapsed-(self.roll_duration if completed else 0)

    def roll_pose(self):
        if not self.rolling:return None
        t=self.roll_elapsed
        if t<1.2:name,p='roll_enter',t/1.2
        elif t<1.2+3*self.roll_turns:name,p='roll_loop',((t-1.2)%3)/3
        else:name,p='roll_exit',(t-1.2-3*self.roll_turns)/1.2
        frames=EXTRA_CLIPS['dragon'][name]
        return frames[min(len(frames)-1,int(p*len(frames)))]
