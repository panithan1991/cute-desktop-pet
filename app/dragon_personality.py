"""Named personality, flight and elemental gestures for the sleepy dragon."""
from app.behavior_selection import Activity

NEW_ACTIVITIES = {
    'proud': Activity('Proud chest puff', (5, 7), 25),
    'curious_sniff': Activity('Curious sniff', (6, 9), 24),
    'happy': Activity('Happy wiggle', (5, 7), 30),
    'hover_float': Activity('Hover float', (10, 16), 45),
    'dive_recover': Activity('Dive and recover', (8, 11), 55),
    'air_brake': Activity('Air brake', (7, 10), 45),
    'perch_landing': Activity('Perch landing', (10, 14), 60),
    'ember_bubbles': Activity('Ember bubbles', (8, 11), 25),
    'static_charge': Activity('Static scale charge', (4, 6), 40),
    'aurora_breath': Activity('Aurora breath', (10, 14), 30),
    'thunder_roar': Activity('Thunder roar', (7, 10), 65),
}
AIR_GESTURES = frozenset(('hover_float', 'dive_recover', 'air_brake', 'perch_landing'))
POWER_GESTURES = frozenset(('ember_bubbles', 'static_charge', 'aurora_breath', 'thunder_roar'))
PERCH_CLIPS = ('wall_perch', 'top_perch')
PERCH_POWERS = frozenset(('fire', 'cloud_flame', 'thunder_roar', 'ember_bubbles'))
MENU_LABELS = (
    ('Proud Chest Puff (ยืดอกภูมิใจ)', 'proud'),
    ('Curious Sniff (ดมอย่างสงสัย)', 'curious_sniff'),
    ('Happy Wiggle (กระดิกหางดีใจ)', 'happy'),
    ('Hover Float (ลอยตัวกลางอากาศ)', 'hover_float'),
    ('Dive and Recover (บินดิ่งแล้วเชิดขึ้น)', 'dive_recover'),
    ('Air Brake (กางปีกเบรก)', 'air_brake'),
    ('Perch Landing (ลงเกาะขอบจอ)', 'perch_landing'),
    ('Ember Bubbles (ฟองประกายไฟ)', 'ember_bubbles'),
    ('Static Scale Charge (ชาร์จไฟที่เกล็ด)', 'static_charge'),
    ('Aurora Breath (ลมหายใจออโรรา)', 'aurora_breath'),
    ('Thunder Roar (คำรามสายฟ้า)', 'thunder_roar'),
)


def envelope(progress, enter=.18, exit=.82):
    """Smooth shared fade that is zero at every activity boundary."""
    t = max(0, min(1, progress / enter, (1-progress) / (1-exit)))
    return t*t*(3-2*t)
