"""Horn tips follow the painted static-charge head, rather than its forehead."""
def charge_horns(index):
    p=max(0,min(1,index/39))
    t=min(1,p*3,(1-p)*3)
    resting=((80,55),(103,55))
    raised=((75,58),(102,49))
    return tuple(tuple(a[j]+(b[j]-a[j])*t for j in (0,1)) for a,b in zip(resting,raised))
