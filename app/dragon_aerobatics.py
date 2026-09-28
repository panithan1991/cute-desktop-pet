"""One 50% aerobatics decision per flight, driven by the pauseable cruise clock."""
import math
from app.pet_motion import BibiFlightMotion
from app.behavior_art import EXTRA_CLIPS


class DragonFlightMotion(BibiFlightMotion):
    roll_chosen=False
    roll_turns=0
    roll_start=0.0
    roll_duration=0.0

    def launch(self):
        if not super().launch():return False
        self.roll_chosen=self.rng.random()<.5
        self.roll_turns=self.rng.choice((2,3)) if self.roll_chosen else 0
        self.roll_start=math.ceil(self.rng.uniform(4,10)/1.8)*1.8
        self.roll_duration=2.4+3*self.roll_turns
        return True

    def reset(self,x,ground):
        super().reset(x,ground)
        self.roll_chosen=False

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
