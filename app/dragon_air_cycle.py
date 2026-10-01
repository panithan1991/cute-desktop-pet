"""Pre-rendered powered flight, shared by launch, cruise and descent."""
WING_FRAMES = 60
WING_PERIOD = 3.0
LIFT_SECONDS = 1.4
LIFT_POSES = tuple(f'liftoff_{i:02d}' for i in range(24))
WING_POSES = tuple(f'wingbeat_{i:02d}' for i in range(WING_FRAMES))
WING_SETTLE_POSES = tuple(f'wing_settle_{phase:02d}_{i:02d}' for phase in range(WING_FRAMES) for i in range(6))
AIR_MANEUVERS = {name:tuple(f'air_{name}_{i:03d}' for i in range(180)) for name in ('dive_recover','air_brake')}
AIR_ROLL_ENTER = tuple(f'air_roll_enter_{i:02d}' for i in range(24))
AIR_ROLL_EXIT = tuple(f'air_roll_exit_{i:02d}' for i in range(24))
AIR_LAND_FOLD = tuple(f'air_land_fold_{i:02d}' for i in range(24))
AIR_BODY_POSES = frozenset((*LIFT_POSES,*WING_POSES,*WING_SETTLE_POSES,*AIR_ROLL_ENTER,*AIR_ROLL_EXIT,*AIR_LAND_FOLD,
                          *(p for clip in AIR_MANEUVERS.values() for p in clip)))
