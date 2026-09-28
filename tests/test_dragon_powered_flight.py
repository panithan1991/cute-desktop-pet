import math
import random
import unittest
from pathlib import Path
from PIL import Image, ImageOps
from app.dragon_aerobatics import DragonFlightMotion, MANEUVERS
from app.dragon_air_cycle import AIR_BODY_POSES, WING_FRAMES
from app.dragon_animation import DragonBehavior

ROOT=Path(__file__).resolve().parents[1]


class PoweredFlightTests(unittest.TestCase):
    def test_maneuvers_are_one_half_of_launches_and_include_all_five(self):
        f=DragonFlightMotion(500,700,auto_launch=False,rng=random.Random(222))
        choices=[]
        for _ in range(3000):
            f.reset(500,700);f.launch();choices.append(f.maneuver_choice)
        self.assertTrue(.47<sum(c is not None for c in choices)/len(choices)<.53)
        self.assertEqual(set(choices)-{None},set(MANEUVERS))

    def test_contact_probability_and_correct_hand_facing_for_each_wall(self):
        f=DragonFlightMotion(500,300,auto_launch=False,rng=random.Random(77))
        count=0
        for _ in range(3000):
            f.state='cruise';f.edge_cooldown=0;f.perch_side=None
            f._contact('right',0,25,1000)
            count+=f.state=='grabbing'
            self.assertEqual(f.direction,1 if f.state=='grabbing' else -1)
        self.assertTrue(.47<count/3000<.53)
        for side, direction in (('left',-1),('right',1)):
            f._grip(side);self.assertEqual(f.direction,direction)
        f.perch_probability=0;f.state='cruise';f.edge_cooldown=0;f.vy=-50
        f._contact('top',0,25,1000)
        self.assertGreater(f.vy,0);self.assertEqual(f.state,'cruise')

    def test_takeoff_prepares_then_repeatedly_flaps_without_teleportation(self):
        f=DragonFlightMotion(500,700,auto_launch=False,rng=random.Random(6))
        f.perch_probability=0;f.launch();poses=set();speeds=[]
        for _ in range(130):
            before=(f.x,f.y);f.step(.1,0,25,3000,700)
            self.assertLess(math.dist(before,(f.x,f.y)),16)
            if f.state=='takeoff' and f.elapsed<1.3:self.assertEqual(f.y,700)
            if f.state=='takeoff' and f.elapsed>1.5:
                poses.add(f.flight_pose());speeds.append(f.vy)
        self.assertGreaterEqual(len(poses),30)
        self.assertGreater(max(speeds)-min(speeds),15)
        f.paused=True;before=(f.x,f.y,f.flap_clock,f.elapsed)
        f.step(.1,0,25,3000,700);self.assertEqual(before,(f.x,f.y,f.flap_clock,f.elapsed))

    def test_maneuvers_keep_continuous_positions_then_wingbeat_descent(self):
        for name in MANEUVERS:
            f=DragonFlightMotion(1200,250,auto_launch=False,rng=random.Random(2))
            f.state='cruise';f.cruise_duration=12;f.climb=-30;f.perch_probability=0
            f.request_maneuver(name);states=set();poses=set()
            for _ in range(500):
                before=(f.x,f.y);f.step(.1,0,25,3000,700)
                self.assertLess(math.dist(before,(f.x,f.y)),22,name)
                self.assertTrue(0<=f.x<=3000 and 25<=f.y<=700)
                states.add(f.state)
                pose=f.perch_pose(DragonBehavior()) or f.roll_pose() or f.maneuver_pose() or f.flight_pose()
                if pose:poses.add(pose)
                if f.state=='rest':break
            self.assertEqual(f.state,'rest',name)
            self.assertTrue({'air_settle','landing','land_fold','touchdown'}.issubset(states),name)
            self.assertGreater(len(poses),30,name)

    def test_all_extra_flight_frames_exist_and_mirror_without_cropped_anatomy(self):
        for pose in AIR_BODY_POSES:
            for platform,extension in (('macos','png'),('windows','ppm')):
                root=ROOT/f'assets/runtime/dragon-{platform}/body-fx'
                with Image.open(root/f'right/{pose}.{extension}') as right,Image.open(root/f'left/{pose}.{extension}') as left:
                    self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes(),pose)
                    self.assertEqual(right.size,(160,160))
                    if platform=='macos':
                        bounds=right.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
                        self.assertGreaterEqual(min(bounds[0],bounds[1],160-bounds[2],160-bounds[3]),3,pose)
        self.assertEqual(WING_FRAMES,60)

    def test_aurora_grows_fades_and_has_a_connected_mouth_nozzle(self):
        from app.dragon_fire_layout import FIRE_NOZZLES
        spans=[]
        for platform in ('macos','windows'):
            root=ROOT/f'assets/runtime/dragon-{platform}/fx'
            for i in range(32):
                with Image.open(root/f'aurora-flame-right/{i:02d}.png') as right,Image.open(root/f'aurora-flame-left/{i:02d}.png') as left:
                    self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes())
                    x,y=FIRE_NOZZLES[i]
                    self.assertGreater(right.getpixel((round(x),round(y)))[3],100)
                    if platform=='macos' and i in (0,5,14,30):
                        bounds=right.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
                        spans.append(bounds[2]-bounds[0])
        self.assertLess(spans[0],spans[1]);self.assertLess(spans[1],spans[2])
        self.assertLess(spans[3],spans[2])

    def test_wing_phase_bridges_and_posture_boundaries_match_exact_pixels(self):
        root=ROOT/'assets/runtime/dragon-macos/body-fx/right'
        with Image.open(root/'wingbeat_00.png') as image:neutral=image.tobytes()
        for phase in range(60):
            with Image.open(root/f'wingbeat_{phase:02d}.png') as wing,Image.open(root/f'wing_settle_{phase:02d}_00.png') as first,Image.open(root/f'wing_settle_{phase:02d}_05.png') as last:
                self.assertEqual(wing.tobytes(),first.tobytes())
                self.assertEqual(last.tobytes(),neutral)
        for filename in ('liftoff_23.png','extra_wall_perch_00.png','extra_top_perch_00.png',
                         'air_roll_enter_00.png','air_roll_exit_23.png','air_land_fold_00.png',
                         'air_dive_recover_000.png','air_dive_recover_179.png','air_air_brake_000.png','air_air_brake_179.png'):
            with Image.open(root/filename) as image:self.assertEqual(image.tobytes(),neutral,filename)
