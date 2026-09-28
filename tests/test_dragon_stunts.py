import math,random,unittest
from pathlib import Path
from PIL import Image
from app.dragon_aerobatics import DragonFlightMotion
from app.dragon_animation import DRAGON_CLIPS,DragonBehavior
from app.behavior_art import EXTRA_CLIPS
from app.pet_sprites import POSES,atlas_path
from app.dragon_fire_layout import FIRE_NOZZLES
from app.dragon_roll_layout import ROLL_HORNS
from app.dragon_effect_layout import MOUTH_POSITIONS
from test_behavior_art import frame


class DragonStuntTests(unittest.TestCase):
    def test_one_half_probability_decision_per_successful_launch(self):
        flight=DragonFlightMotion(300,700,auto_launch=False,rng=random.Random(50))
        chosen=0;turns=set()
        for _ in range(2000):
            flight.reset(300,700);self.assertTrue(flight.launch())
            chosen+=flight.roll_chosen
            if flight.roll_chosen:turns.add(flight.roll_turns)
            before=(flight.roll_chosen,flight.roll_start,flight.roll_turns)
            self.assertFalse(flight.launch())
            flight.step(.1,0,20,900,700)
            self.assertEqual(before,(flight.roll_chosen,flight.roll_start,flight.roll_turns))
        self.assertTrue(.47<chosen/2000<.53)
        self.assertEqual(turns,{2,3})

    def test_complete_two_or_three_turns_then_resume_hover_phase_without_jump(self):
        flight=DragonFlightMotion(300,300,auto_launch=False)
        flight.state='cruise';flight.roll_chosen=True;flight.roll_start=5.4
        for turns in (2,3):
            flight.roll_turns=turns;flight.roll_duration=2.4+3*turns
            for turn in range(turns):
                flight.elapsed=flight.roll_start+1.2+3*turn+.001
                self.assertTrue(flight.roll_spinning)
                self.assertEqual(flight.roll_pose(),EXTRA_CLIPS['dragon']['roll_loop'][0])
            flight.elapsed=flight.roll_start+flight.roll_duration
            self.assertFalse(flight.rolling)
            self.assertAlmostEqual(flight.hover_elapsed,flight.roll_start)
        flight.elapsed=flight.roll_start+2;flight.paused=True
        before=flight.roll_pose(),flight.elapsed,flight.x,flight.y
        flight.step(.1,0,20,900,700)
        self.assertEqual(before,(flight.roll_pose(),flight.elapsed,flight.x,flight.y))

    def test_flight_and_ground_stunt_endpoints_share_exact_joined_body_pixels(self):
        poses=POSES['dragon'];atlas=Image.open(atlas_path('dragon',1,'darwin')).convert('RGBA')
        def pixels(name):return frame(atlas,poses.index(name)).tobytes()
        clips=EXTRA_CLIPS['dragon'];hover=DRAGON_CLIPS['hover'][0]
        for a,b in ((clips['roll_enter'][0],hover),(clips['roll_enter'][-1],clips['roll_loop'][0]),
                    (clips['roll_exit'][0],clips['roll_loop'][0]),(clips['roll_exit'][-1],hover)):
            self.assertEqual(pixels(a),pixels(b))
        for state in ('belly_smoke','fury'):
            for name in (clips[state][0],clips[state][-1]):self.assertEqual(pixels(name),pixels(DRAGON_CLIPS['idle'][0]))
            pet=DragonBehavior(random.Random(3));pet.force(state);pet.transition.queue=[]
            self.assertFalse(pet.walking)
            pet.elapsed=pet.duration/2;before=pet.pose(),pet.elapsed
            pet.step(.1,frozen=True);self.assertEqual(before,(pet.pose(),pet.elapsed))

    def test_horns_rotate_with_the_dragon_and_return_after_one_full_revolution(self):
        anchors=ROLL_HORNS['roll_loop']
        for horn in (0,1):
            radii=[math.dist(p[horn],(80,80)) for p in anchors]
            self.assertLess(max(radii)-min(radii),.0001)
            self.assertLess(math.dist(anchors[0][horn],anchors[-1][horn]),4)
        self.assertEqual(len(anchors),90)

    def test_large_flame_nozzle_is_defined_for_every_growth_and_fade_frame(self):
        self.assertEqual(len(FIRE_NOZZLES),32)
        self.assertTrue(all(0<=x<=10 and 25<y<135 for x,y in FIRE_NOZZLES))
        self.assertEqual(len(MOUTH_POSITIONS),len(DRAGON_CLIPS['fire']))
        poses=POSES['dragon'];atlas=Image.open(atlas_path('dragon',1,'darwin')).convert('RGBA')
        for i in range(8,34):
            body=frame(atlas,poses.index(DRAGON_CLIPS['fire'][i]));x,y=MOUTH_POSITIONS[i]
            self.assertTrue(any(body.getpixel((xx,yy))[3]>100 for xx in range(x-4,x+1) for yy in range(y-2,y+3)))

    def test_individual_trees_and_sky_ring_fades_are_packaged_for_both_platforms(self):
        root=Path(__file__).resolve().parents[1]/'assets/runtime'
        for platform in ('macos','windows'):
            base=root/f'dragon-{platform}'
            for side in ('left','right','up'):
                for i in range(16):
                    tree=Image.open(base/f'tree-{side}-{i:02d}.png').convert('RGBA')
                    self.assertEqual(tree.size,(560,480))
                    self.assertIsNotNone(tree.getchannel('A').getbbox())
                    if platform=='windows':self.assertLessEqual(set(tree.getchannel('A').tobytes()),{0,255})
            atlas=Image.open(base/'sky-rings.png').convert('RGBA')
            self.assertEqual(atlas.size,(384,576))
            for i in (0,23):
                ring=atlas.crop((i%4*96,i//4*96,i%4*96+96,i//4*96+96))
                self.assertIsNone(ring.getchannel('A').getbbox())
            self.assertIsNotNone(atlas.getchannel('A').getbbox())
            if platform=='windows':self.assertLessEqual(set(atlas.getchannel('A').tobytes()),{0,255})
