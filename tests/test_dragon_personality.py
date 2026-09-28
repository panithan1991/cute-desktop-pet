import math
import random
import unittest
from pathlib import Path
from collections import OrderedDict
from unittest.mock import MagicMock,patch
from PIL import Image,ImageOps
from app.dragon_personality import NEW_ACTIVITIES,AIR_GESTURES,POWER_GESTURES,envelope
from app.dragon_animation import DragonBehavior,DRAGON_CLIPS
from app.dragon_aerobatics import DragonFlightMotion
from app.behavior_art import EXTRA_CLIPS
from app.pet_sprites import POSES
from app.dragon_power_view import DragonPowerView

ROOT=Path(__file__).resolve().parents[1]


class DragonPersonalityTests(unittest.TestCase):
    def test_eleven_gestures_have_complete_frames_and_matching_body_joins(self):
        self.assertEqual(len(NEW_ACTIVITIES),11)
        with Image.open(ROOT/'assets/dragon-motion.png') as atlas:
            def pixels(pose):
                i=POSES['dragon'].index(pose)
                return atlas.crop((i%5*160,i//5*160,i%5*160+160,i//5*160+160)).tobytes()
            for name in NEW_ACTIVITIES:
                frames=EXTRA_CLIPS['dragon'][name]
                self.assertEqual(len(frames),40)
                start=DRAGON_CLIPS['hover'][0] if name in AIR_GESTURES else DRAGON_CLIPS['idle'][0]
                end=DRAGON_CLIPS['idle'][0] if name=='perch_landing' else start
                self.assertEqual(pixels(frames[0]),pixels(start),name)
                self.assertEqual(pixels(frames[-1]),pixels(end),name)
                self.assertGreater(len({pixels(p) for p in frames}),18,name)

    def test_air_gestures_stay_on_screen_freeze_and_return_to_ground(self):
        for mode in AIR_GESTURES:
            flight=DragonFlightMotion(300,680,auto_launch=False,rng=random.Random(30))
            flight.requested_mode=mode;self.assertTrue(flight.launch())
            flight.cruise_duration=10
            self.assertFalse(flight.roll_chosen)
            reached=set();positions=[]
            for _ in range(1000):
                if flight.state=='perched' and flight.elapsed>=1:flight.depart()
                before=(flight.x,flight.y)
                flight.step(.1,0,25,950,680)
                self.assertTrue(0<=flight.x<=950 and 25<=flight.y<=680,mode)
                self.assertLess(math.dist(before,(flight.x,flight.y)),45,mode)
                frame=flight.perch_pose(DragonBehavior(random.Random(1))) or flight.maneuver_pose()
                if frame:reached.add(frame)
                if flight.state=='cruise':positions.append((flight.x,flight.y))
                if flight.state=='rest':break
            self.assertEqual(flight.state,'rest',mode)
            self.assertEqual(flight.y,680)
            self.assertGreater(len(reached),8)
            flight.state='cruise';flight.elapsed=3;flight.paused=True
            before=(flight.x,flight.y,flight.elapsed,flight.maneuver_pose())
            flight.step(.1,0,25,950,680)
            self.assertEqual(before,(flight.x,flight.y,flight.elapsed,flight.maneuver_pose()))


    def test_hover_holds_horizontal_position_brake_retreats_and_dive_climbs(self):
        for name in ('hover_float','air_brake','dive_recover'):
            flight=DragonFlightMotion(300,240,auto_launch=False)
            flight.mode=name;flight.state='cruise';flight.cruise_duration=10
            flight.altitude=.3;flight.wave_speed=.5
            samples=[]
            for _ in range(100):
                flight.step(.1,0,25,2000,680);samples.append((flight.x,flight.y))
            if name=='hover_float':self.assertLess(abs(samples[60][0]-samples[40][0]),1)
            elif name=='air_brake':self.assertLess(samples[60][0],samples[40][0])
            else:self.assertGreater(samples[50][1],samples[20][1]+50)

    def test_new_behavior_selection_pause_and_charge_followup(self):
        pet=DragonBehavior(random.Random(10))
        for name in NEW_ACTIVITIES:
            pet.force(name);pet.transition.queue=[];pet.elapsed=pet.duration*.5
            before=(pet.pose(),pet.elapsed,pet.clock)
            pet.step(.1,frozen=True)
            self.assertEqual(before,(pet.pose(),pet.elapsed,pet.clock))
            self.assertEqual(pet.walking,name in AIR_GESTURES)
        pet.force('static_charge');pet.transition.queue=[];pet.elapsed=pet.duration
        pet.finish();self.assertEqual(pet.state,'storm_hover')

    def test_signature_effects_join_with_no_visible_boundary_frame(self):
        self.assertEqual(envelope(0),0);self.assertEqual(envelope(1),0)
        self.assertAlmostEqual(envelope(.5),1)
        for state in POWER_GESTURES:
            view=DragonPowerView.__new__(DragonPowerView)
            view.window=MagicMock();view.parent=MagicMock();view.canvas=MagicMock();view.rng=random.Random(2)
            view.previous_state=None;view.previous_elapsed=0;view.last_rect=None
            view.ring_origins={};view.clip_frames=OrderedDict();view.weather=OrderedDict()
            view.clip_image=MagicMock();view.tree=MagicMock();view.draw_trees=MagicMock()
            for elapsed in (0,3,5,8,10):
                view.draw(state,elapsed,10,(300,400),((270,360),(290,360)),1,(0,20,1200,800),True)
            self.assertTrue(view.window.withdraw.called)
            self.assertTrue(view.window.deiconify.called,state)

    def test_new_effects_have_full_alpha_on_mac_and_simple_windows_masks(self):
        sizes={'ember-bubble':(96,96,36),'aurora-right':(240,160,64),'aurora-left':(240,160,64),'scale-charge':(96,96,32),'shockwave':(240,240,32)}
        for platform in ('windows','macos'):
            for name,(w,h,count) in sizes.items():
                for i in range(count):
                    with Image.open(ROOT/f'assets/runtime/dragon-{platform}/fx/{name}/{i:02d}.png') as im:
                        self.assertEqual(im.size,(w,h))
                        if platform=='windows':self.assertLessEqual(set(im.getchannel('A').tobytes()),{0,255})
        for i in range(64):
            root=ROOT/'assets/runtime/dragon-macos/fx'
            with Image.open(root/f'aurora-right/{i:02d}.png') as right,Image.open(root/f'aurora-left/{i:02d}.png') as left:
                self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes())

    def test_roar_cones_are_mirrored_rooted_at_mouth_and_never_cropped(self):
        for platform in ('macos','windows'):
            base=ROOT/f'assets/runtime/dragon-{platform}/fx'
            for i in range(16):
                with Image.open(base/f'roar-cone-right/{i:02d}.png') as right,Image.open(base/f'roar-cone-left/{i:02d}.png') as left:
                    self.assertEqual(right.size,(640,360))
                    self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes())
                    b=right.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
                    self.assertGreaterEqual(min(b[0],b[1],640-b[2],360-b[3]),4)
                    self.assertTrue(any(right.getpixel((x,y))[3]>100 for x in range(7,12) for y in range(317,324)))
                    if platform=='windows':self.assertLessEqual(set(right.getchannel('A').tobytes()),{0,255})

    def test_ember_membrane_grows_then_breaks_apart_and_fades_to_empty(self):
        base=ROOT/'assets/runtime/dragon-macos/fx/ember-bubble'
        def alpha(i):
            with Image.open(base/f'{i:02d}.png') as image:return image.getchannel('A').copy()
        self.assertIsNone(alpha(0).getbbox());self.assertIsNone(alpha(35).getbbox())
        bounds=[alpha(i).point(lambda a:255 if a>32 else 0).getbbox() for i in (4,14,26)]
        spans=[b[2]-b[0] for b in bounds]
        self.assertLess(spans[0],spans[1]);self.assertLess(spans[1],spans[2])
        self.assertLess(sum(alpha(33).tobytes()),sum(alpha(26).tobytes()))




    def test_mouth_lightning_has_three_or_four_separate_fast_channels(self):
        from app.dragon_signature_effects import draw_signature
        from app.dragon_lightning import STRIKES,STORM_FRAMES
        for seed in (10,11):
            view=MagicMock();view.seed=seed;view.downward=False
            elapsed=STRIKES[4][0]/(STORM_FRAMES-1)*8
            self.assertTrue(draw_signature(view,'thunder_roar',elapsed,8,(150,250),((130,200),(145,200)),1,(0,0,840,480)))
            self.assertEqual(view.tree.call_count,3+seed%2)
            self.assertFalse(view.clip_image.called)
            view.reset_mock()
            self.assertFalse(draw_signature(view,'thunder_roar',55/(STORM_FRAMES-1)*8,8,(150,250),((130,200),(145,200)),1,(0,0,840,480)))
            self.assertFalse(view.tree.called)

    def test_aurora_nozzle_is_stationary_and_loop_has_no_jump(self):
        root=ROOT/'assets/runtime/dragon-macos/fx/aurora-right'
        with Image.open(root/'00.png') as first,Image.open(root/'63.png') as last:
            self.assertEqual(first.tobytes(),last.tobytes())
            nozzle=first.crop((0,0,24,160)).tobytes()
        for i in range(64):
            with Image.open(root/f'{i:02d}.png') as frame:
                self.assertEqual(frame.crop((0,0,24,160)).tobytes(),nozzle)

    def test_charge_tracks_horn_tips_and_outward_variants_mirror_exactly(self):
        from app.dragon_charge_layout import charge_horns
        self.assertEqual(charge_horns(0),charge_horns(39))
        self.assertLess(charge_horns(20)[1][1],charge_horns(0)[1][1])
        for part in ('rear','front'):
            for platform in ('macos','windows'):
                root=ROOT/f'assets/runtime/dragon-{platform}/fx'
                for i in range(32):
                    with Image.open(root/f'charge-{part}-right/{i:02d}.png') as right,Image.open(root/f'charge-{part}-left/{i:02d}.png') as left:
                        self.assertEqual(right.size,(128,128))
                        self.assertEqual(ImageOps.mirror(right).tobytes(),left.tobytes())
