"""Lightning exposure timing, independent of the dragon's slow wingbeats."""

STORM_FRAMES = 140
# Irregular gaps and double strikes: each exposure lasts about 0.1–0.2s
# during a 7–9 second activity, with completely dark gaps between strikes.
STRIKES = ((18,3),(26,3),(33,4),(43,3),(49,3),(58,4),
           (69,3),(75,3),(85,4),(98,3),(105,3),(117,3))


def flash_at(frame):
    for index, (start, length) in enumerate(STRIKES):
        age = frame-start
        if 0 <= age < length:
            return index, (.6,1,.22,.06)[age], (.7,1,1,1)[age]
    return -1, 0, 0
