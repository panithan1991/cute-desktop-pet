"""One 50% aerobatics decision per flight, driven by the pauseable cruise clock."""
import math
from app.pet_motion import BibiFlightMotion
from app.behavior_art import EXTRA_CLIPS
from app.dragon_personality import AIR_GESTURES, envelope
from app.dragon_flight_joins import JOIN_SECONDS,JOIN_FRAMES,LANDING_JOIN_POSES,TOUCHDOWN_JOIN_POSES


class DragonFlightMotion(BibiFlightMotion):
    mode='walk'
    requested_mode='walk'
    perch_side=None
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
        if self.roll_chosen:self.roll_start=0
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

    def begin_landing(self,settle=True):
        self.flight_join_index=min(9,int((self.hover_elapsed%1.8)/1.8*10))
        self.state='air_settle' if settle else 'release_join'
        self.elapsed=0

    def _grip(self,side):
        self.flight_join_index=min(9,int((self.hover_elapsed%1.8)/1.8*10))
        self.perch_side=side
        self.state='grabbing';self.elapsed=0;self.roll_chosen=False
        self.direction=-1 if side=='right' else 1

    @property
    def grip_amount(self):
        if self.state=='grabbing':return max(0,min(1,(self.elapsed-JOIN_SECONDS)/1.2))
        if self.state=='unperch':return max(0,1-self.elapsed/1.2)
        return 1 if self.state=='perched' else 0

    def perch_pose(self,behavior):
        if self.state=='touchdown':return TOUCHDOWN_JOIN_POSES[min(JOIN_FRAMES-1,int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES))]
        if self.state=='air_settle':return f'flight_join_{self.flight_join_index:02d}_{min(JOIN_FRAMES-1,int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES)):02d}'
        if self.state=='release_join':return LANDING_JOIN_POSES[min(JOIN_FRAMES-1,int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES))]
        if self.state not in {'grabbing','perched','unperch'}:return None
        name='top_perch' if getattr(self,'perch_side',None)=='top' else 'wall_perch'
        frames=EXTRA_CLIPS['dragon'][name]
        if self.state=='grabbing':
            if self.elapsed<JOIN_SECONDS:
                return f'flight_join_{self.flight_join_index:02d}_{min(JOIN_FRAMES-1,int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES)):02d}'
            return frames[min(12,int((self.elapsed-JOIN_SECONDS)/1.2*12))]
        if self.state=='unperch':return frames[max(0,12-int(self.elapsed/1.2*12))]
        if self.state!='perched':return None
        if behavior.state=='idle':return frames[12]
        p=min(1,behavior.elapsed/max(.001,behavior.duration))
        # Keep the paws planted while the mouth opens, holds, and closes.
        index=12+int(p/.22*8) if p<.22 else 20 if p<.82 else 20+int((p-.82)/.18*19)
        return frames[min(39,index)]

    def step(self,seconds,left,top,right,ground):
        if self.state in {'grabbing','perched','unperch','release_join','air_settle','touchdown'}:
            if self.paused:return
            self.elapsed+=min(max(seconds,0),.1)
            self.x=max(left,min(right,self.x));self.y=max(top,min(ground,self.y))
            if self.state=='grabbing' and self.elapsed>=1.2+JOIN_SECONDS:
                self.state='perched';self.elapsed=0
            elif self.state=='unperch' and self.elapsed>=1.2:
                self.state='release_join';self.elapsed=0
            elif self.state=='release_join' and self.elapsed>=JOIN_SECONDS:
                self.state='landing';self.elapsed=0;self.landing_y=self.y
            elif self.state=='air_settle' and self.elapsed>=JOIN_SECONDS:
                self.state='release_join';self.elapsed=0
            elif self.state=='touchdown' and self.elapsed>=JOIN_SECONDS:
                self.state='rest';self.elapsed=0
            return
        if self.state=='cruise' and self.mode in {'walk','perch_landing'}:
            if self.paused:return
            dt=min(max(seconds,0),.1);self.elapsed+=dt
            # True diagonal flight: neither position nor grip is interpolated
            # toward a preselected edge. Contact alone starts the grip clip.
            if self.elapsed<=dt:
                self.climb=-self.speed*self.rng.uniform(1.35,1.95)
            acceleration=min(1,self.elapsed/.8)
            horizontal_factor=.1 if self.rolling else 1
            vertical_factor=.02 if self.rolling else 1
            horizontal_gap=right-self.x if self.direction>0 else self.x-left
            vertical_gap=self.y-top if getattr(self,'climb',-self.speed)<0 else ground-self.y
            self.x+=self.direction*self.speed*dt*acceleration*horizontal_factor*max(.2,min(1,horizontal_gap/65))
            self.y+=getattr(self,'climb',-self.speed)*dt*acceleration*vertical_factor*max(.2,min(1,vertical_gap/65))
            side='top' if self.y<=top else 'left' if self.x<=left else 'right' if self.x>=right else None
            self.x=max(left,min(right,self.x));self.y=max(top,min(ground,self.y))
            if self.y>=ground:self.climb=-abs(self.climb)
            if side:self._grip(side)
            elif self.elapsed>=self.cruise_duration:
                self.begin_landing()
            return
        if self.mode not in AIR_GESTURES or self.state!='cruise':
            previous=self.state
            super().step(seconds,left,top,right,ground)
            if previous=='landing' and self.state=='rest':
                self.state='touchdown';self.elapsed=0
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
        if self.mode!='perch_landing':self.x+=self.direction*speed*dt
        side='top' if self.y<=top else 'left' if self.x<=left else 'right' if self.x>=right else None
        if side:
            self.x=max(left,min(right,self.x));self.y=max(top,min(ground,self.y))
            self._grip(side)
            return
        if self.mode!='perch_landing':
            if self.x>=right:self.x,self.direction=right,-1
            elif self.x<=left:self.x,self.direction=left,1
        self.y=max(top,min(ground,self.y))
        if p>=1:
            self.begin_landing(settle=False)

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
