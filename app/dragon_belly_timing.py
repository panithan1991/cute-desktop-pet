"""Six relaxed exhalations between the painted lie-down and sit-up joins."""
ENTRY=.12
EXIT=.88
RING_COUNT=6
SKY_RING_BIRTHS=tuple(ENTRY+(i+.36)*(EXIT-ENTRY)/RING_COUNT for i in range(RING_COUNT))


def belly_pose_index(progress):
    p=max(0,min(1,progress))
    if p<ENTRY:return min(23,int(p/ENTRY*24))
    if p>=EXIT:return 96+min(23,int((p-EXIT)/(1-EXIT)*24))
    cycle=(p-ENTRY)/(EXIT-ENTRY)*RING_COUNT
    return 24+(int(cycle)%3)*24+min(23,int((cycle%1)*24))
