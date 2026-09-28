"""Wingbeat-driven flight with an optional maneuver and contact-only perching."""
import math
from app.pet_motion import BibiFlightMotion
from app.behavior_art import EXTRA_CLIPS
from app.dragon_personality import AIR_GESTURES, envelope
from app.dragon_flight_joins import JOIN_SECONDS, JOIN_FRAMES, TOUCHDOWN_JOIN_POSES
from app.dragon_air_cycle import WING_FRAMES, WING_PERIOD, LIFT_SECONDS, LIFT_POSES, AIR_MANEUVERS, AIR_ROLL_ENTER, AIR_ROLL_EXIT, AIR_LAND_FOLD

MANEUVERS = ('glide', 'dive_recover', 'air_brake', 'hover_float', 'roll')


class DragonFlightMotion(BibiFlightMotion):
    mode = requested_mode = 'walk'
    perch_side = None
    roll_chosen = False
    roll_turns = 0
    roll_start = roll_duration = flap_clock = vy = vx = 0.0
    perch_probability = .5
    maneuver_choice = None
    maneuver_age = 0.0
    maneuver_duration = 6.0
    maneuver_done = maneuver_active = False
    edge_cooldown = 0.0
    flight_join_index = 0

    def launch(self):
        if not super().launch():return False
        self.mode = self.requested_mode; self.requested_mode = 'walk'
        self.perch_side = None
        self.flap_clock = self.vy = self.vx = 0.0
        self.climb = -self.speed*self.rng.uniform(.65, 1.05)
        self.edge_cooldown = 0.0
        self.maneuver_choice = None
        if self.mode in AIR_GESTURES and self.mode != 'perch_landing':
            self.maneuver_choice = self.mode
        elif self.rng.random() < .5:
            self.maneuver_choice = self.rng.choice(MANEUVERS)
        self.maneuver_start = self.rng.uniform(3.5, 6)
        self.maneuver_active = self.maneuver_done = False
        self.maneuver_age = 0.0
        self.roll_chosen = self.maneuver_choice == 'roll'
        self.roll_turns = self.rng.choice((2, 3)) if self.roll_chosen else 0
        self.roll_duration = 2.4+3*self.roll_turns
        self.roll_start = self.maneuver_start+JOIN_SECONDS
        self.maneuver_duration = self.roll_duration if self.roll_chosen else 6.0
        return True

    def reset(self, x, ground):
        super().reset(x, ground)
        self.roll_chosen = self.maneuver_active = self.maneuver_done = False
        self.mode = self.requested_mode = 'walk'; self.perch_side = None
        self.flap_clock = self.vy = self.vx = 0.0

    def request_maneuver(self, name):
        if self.state != 'cruise' or name not in MANEUVERS:return False
        self.maneuver_choice = name
        self.maneuver_done = self.maneuver_active = False
        self.maneuver_start = self.elapsed
        self.roll_chosen = name == 'roll'
        self.roll_turns = self.rng.choice((2, 3)) if self.roll_chosen else 0
        self.roll_duration = 2.4+3*self.roll_turns
        self.maneuver_duration = self.roll_duration if self.roll_chosen else 6.0
        return True

    def _settle(self, destination):
        self.flight_join_index = int(self.flap_clock/WING_PERIOD*WING_FRAMES) % WING_FRAMES
        if self.maneuver_active and self.maneuver_choice=='glide':self.flight_join_index=0
        self.state = 'air_settle'; self.join_destination = destination
        self.join_elapsed = 0.0

    def begin_landing(self, settle=True):
        self.maneuver_active = self.roll_chosen = False
        if settle:self._settle('landing')
        else:self.state = 'landing'; self.elapsed = self.flap_clock = 0.0

    def depart(self):
        if self.state == 'perched':self.state = 'unperch'; self.elapsed = 0.0

    def _grip(self, side):
        self.flight_join_index = int(self.flap_clock/WING_PERIOD*WING_FRAMES) % WING_FRAMES
        if self.maneuver_active and self.maneuver_choice=='glide':self.flight_join_index=0
        self.perch_side = side; self.state = 'grabbing'; self.elapsed = 0.0
        self.maneuver_active = self.roll_chosen = False
        # Wall artwork looks and reaches right. Mirror both for the left wall.
        self.direction = -1 if side == 'left' else 1
        self.vx = self.vy = 0.0

    def _contact(self, side, left, top, right):
        if self.edge_cooldown > 0:return
        if self.rng.random() < self.perch_probability:
            self._grip(side); return
        self.edge_cooldown = .65
        if side == 'top':
            self.y = top+1; self.climb = abs(getattr(self, 'climb', self.speed))
            self.vy = abs(self.vy)*.55
        else:
            self.direction = 1 if side == 'left' else -1
            self.x = left+1 if side == 'left' else right-1
            self.vx = self.direction*abs(self.vx)*.55

    @property
    def grip_amount(self):
        if self.state == 'grabbing':return max(0, min(1, (self.elapsed-JOIN_SECONDS)/1.2))
        if self.state == 'unperch':return max(0, 1-self.elapsed/1.2)
        return 1 if self.state == 'perched' else 0

    def perch_pose(self, behavior):
        if self.state == 'touchdown':return TOUCHDOWN_JOIN_POSES[min(JOIN_FRAMES-1, int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES))]
        if self.state == 'air_settle':return f'wing_settle_{self.flight_join_index:02d}_{min(JOIN_FRAMES-1,int(self.join_elapsed/JOIN_SECONDS*JOIN_FRAMES)):02d}'
        if self.state not in {'grabbing', 'perched', 'unperch'}:return None
        name = 'top_perch' if self.perch_side == 'top' else 'wall_perch'
        frames = EXTRA_CLIPS['dragon'][name]
        if self.state == 'grabbing':
            if self.elapsed < JOIN_SECONDS:return f'wing_settle_{self.flight_join_index:02d}_{min(JOIN_FRAMES-1,int(self.elapsed/JOIN_SECONDS*JOIN_FRAMES)):02d}'
            return frames[min(12, int((self.elapsed-JOIN_SECONDS)/1.2*12))]
        if self.state == 'unperch':return frames[max(0, 12-int(self.elapsed/1.2*12))]
        if behavior.state == 'idle':return frames[12]
        p = min(1, behavior.elapsed/max(.001, behavior.duration))
        index = 12+int(p/.22*8) if p < .22 else 20 if p < .82 else 20+int((p-.82)/.18*19)
        return frames[min(39, index)]

    def flight_pose(self):
        if self.state == 'takeoff' and self.elapsed < LIFT_SECONDS:return LIFT_POSES[min(len(LIFT_POSES)-1, int(self.elapsed/LIFT_SECONDS*len(LIFT_POSES)))]
        if self.state == 'land_fold':
            frames = AIR_LAND_FOLD
            return frames[min(len(frames)-1, int(self.elapsed/1.4*len(frames)))]
        if self.state in {'takeoff', 'cruise', 'landing'}:return f'wingbeat_{int(self.flap_clock/WING_PERIOD*WING_FRAMES)%WING_FRAMES:02d}'
        return None

    def _move(self, dt, desired_x, desired_y, left, top, right, ground, lift=1):
        # Continuous gravity and wingbeat lift, with gentle trajectory trim.
        phase = self.flap_clock/WING_PERIOD*math.tau
        gravity=100.0
        stroke_lift=gravity*(1+.85*math.sin(phase)*lift)
        trim=(desired_y-self.vy)*2.8
        self.vy += (gravity-stroke_lift+trim)*dt
        self.vy = max(-120, min(120, self.vy))
        self.vx += (desired_x-self.vx)*min(1, 2.4*dt)
        self.x += self.vx*dt; self.y += self.vy*dt
        side = 'top' if self.y <= top else 'left' if self.x <= left else 'right' if self.x >= right else None
        self.x = max(left, min(right, self.x)); self.y = max(top, min(ground, self.y))
        if side and self.state in {'takeoff', 'cruise'}:self._contact(side, left, top, right)
        elif side and side != 'top':
            self.direction = 1 if side == 'left' else -1; self.vx = self.direction*abs(self.vx)*.5

    def step(self, seconds, left, top, right, ground):
        if self.paused:return
        dt = min(max(seconds, 0), .1)
        right, ground = max(left, right), max(top, ground)
        self.edge_cooldown = max(0, self.edge_cooldown-dt)
        if self.state == 'rest':
            self.elapsed += dt; self.y = ground
            if self.auto_launch and self.elapsed >= self.rest_duration:self.launch()
            return
        if self.state == 'air_settle':
            self.join_elapsed += dt
            self._move(dt, self.vx*.85, 0, left, top, right, ground, lift=0)
            if self.join_elapsed >= JOIN_SECONDS:
                self.flap_clock = 0.0
                if self.join_destination == 'maneuver':
                    self.state = 'cruise'; self.maneuver_active = True
                    self.maneuver_age = 0.0; self.maneuver_y = self.y; self.roll_start = self.elapsed
                elif self.join_destination=='cruise':self.state='cruise'
                else:self.state = 'landing'; self.elapsed = 0.0
            return
        self.elapsed += dt
        if self.state in {'grabbing', 'perched', 'unperch', 'touchdown', 'land_fold'}:
            if self.state == 'grabbing' and self.elapsed >= 1.2+JOIN_SECONDS:self.state = 'perched'; self.elapsed = 0.0
            elif self.state == 'unperch' and self.elapsed >= 1.2:
                if self.perch_side in {'left', 'right'}:self.direction *= -1
                self.state = 'landing'; self.elapsed = self.flap_clock = 0.0
            elif self.state == 'land_fold' and self.elapsed >= 1.4:self.state = 'touchdown'; self.elapsed = 0.0
            elif self.state == 'touchdown' and self.elapsed >= JOIN_SECONDS:self.state = 'rest'; self.elapsed = 0.0
            return
        if self.state == 'takeoff':
            if self.elapsed < LIFT_SECONDS:return
            self.flap_clock += dt
            self._move(dt, self.direction*self.speed*.55, -self.speed*.8, left, top, right, ground)
            high = top+(ground-top)*self.altitude
            if self.state == 'takeoff' and self.y <= high:self.state = 'cruise'; self.elapsed = 0.0
            return
        self.flap_clock += dt
        if self.state == 'landing':
            gap = ground-self.y
            self._move(dt, self.direction*self.speed*.55*min(1,gap/90), min(65,max(9,gap*.65)), left, top, right, ground, lift=min(1,gap/50))
            if self.y >= ground-.5:
                self.y = ground; self.vx = self.vy = 0.0
                self.state = 'land_fold'; self.elapsed = 0.0
            return
        if self.state != 'cruise':return
        if self.mode in AIR_GESTURES and self.mode != 'perch_landing' and self.maneuver_choice is None and not self.maneuver_done:
            self.maneuver_choice = self.mode; self.maneuver_start = self.elapsed
        if self.elapsed >= self.cruise_duration and not self.maneuver_active:self.begin_landing(); return
        if self.maneuver_choice and not self.maneuver_done and not self.maneuver_active and self.elapsed >= self.maneuver_start:
            self._settle('maneuver'); return
        target_x = self.direction*self.speed
        target_y = getattr(self, 'climb', -self.speed*.8)
        if self.y > ground-90:self.climb = target_y = -self.speed*.8
        if self.maneuver_active:
            self.maneuver_age += dt
            p = min(1, self.maneuver_age/self.maneuver_duration); e = envelope(p,.25,.75)
            name = self.maneuver_choice
            if name == 'dive_recover':
                amplitude = min(150,max(0,ground-self.maneuver_y-50))
                target = self.maneuver_y+amplitude*math.sin(math.pi*p)**4
                derivative = amplitude*4*math.sin(math.pi*p)**3*math.cos(math.pi*p)*math.pi/self.maneuver_duration
                target_y = derivative+3*(target-self.y); target_x *= 1+.7*e
            elif name in {'hover_float','roll'}:target_y = 3*(self.maneuver_y-self.y); target_x *= 1-e
            elif name == 'air_brake':target_x *= 1-1.25*e; target_y = 3*(self.maneuver_y-10*e-self.y)
            elif name == 'glide':target_x *= 1+.25*e; target_y = 12*e
            if p >= 1:
                self.maneuver_active = False; self.maneuver_done = True
                if name=='hover_float':
                    self._settle('landing' if self.elapsed>=self.cruise_duration else 'cruise')
                    return
                self.flap_clock = 0.0
                if self.elapsed >= self.cruise_duration:self.begin_landing(settle=False)
        self._move(dt,target_x,target_y,left,top,right,ground,lift=.3 if self.maneuver_active and self.maneuver_choice=='glide' else 1)

    def maneuver_pose(self):
        if self.state != 'cruise' or not self.maneuver_active or self.maneuver_choice is None:return None
        name = self.maneuver_choice
        if name in {'roll','hover_float'}:return None
        if name == 'glide':return 'wingbeat_00'
        frames = AIR_MANEUVERS[name]; p = min(1,self.maneuver_age/self.maneuver_duration)
        return frames[min(len(frames)-1,int(p*len(frames)))]

    @property
    def rolling(self):
        return self.roll_chosen and self.state=='cruise' and self.maneuver_active and self.roll_start<=self.elapsed<self.roll_start+self.roll_duration

    @property
    def roll_elapsed(self):return self.elapsed-self.roll_start

    @property
    def roll_spinning(self):return self.rolling and 1.2<=self.roll_elapsed<1.2+3*self.roll_turns

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
        frames=AIR_ROLL_ENTER if name=='roll_enter' else AIR_ROLL_EXIT if name=='roll_exit' else EXTRA_CLIPS['dragon'][name]
        return frames[min(len(frames)-1,int(p*len(frames)))]
