"""The master loop and its open/closed eyelid timing."""

from dataclasses import dataclass

import numpy as np


MASTER_FRAMES = 816
MASTER_FPS = 60
MOTION_FRAMES = MASTER_FRAMES // 2
SIZE = (3840, 2160)


@dataclass(frozen=True)
class Timeline:
    count: int

    @classmethod
    def for_output(cls, fps, rate):
        return cls(max(1, round(MASTER_FRAMES * fps / MASTER_FPS / rate)))

    def position(self, index):
        frame, fraction = divmod(index * MASTER_FRAMES, self.count)
        return frame + fraction / self.count if fraction else frame


def eyelid_at(position):
    # Painted cels exist only during the two blinks. Clamp fractional samples
    # at their edges to the nearest painted pose.
    first, last = (189, 214) if position < MASTER_FRAMES / 2 else (687, 715)
    return min(last, max(first, round(position)))


def hair_at(motion, frame):
    start = int(frame)
    fraction = frame - start
    if not fraction:
        return motion[start]
    return (1 - fraction) * motion[start] + fraction * motion[(start + 1) % MASTER_FRAMES]


def eye_closures(frame):
    timings = ((188.75, 9.25, 1.0, 15., .34), (686.50, 10.25, 1.5, 17.5, -.42))
    for start, down, contact, up, lag in timings:
        if start - 1 <= frame <= start + down + contact + up + 1:
            def stroke(offset):
                elapsed = frame - start - offset
                a, b = np.clip([elapsed / down, (elapsed - down - contact) / up], 0., 1.)
                return float(a*a*(3.-2.*a) * (1.-b*b*(3.-2.*b)))

            return stroke(0.), stroke(lag)
    return 0., 0.


def ease(value):
    value = np.clip(value, 0, 1)
    return value*value*(3-2*value)


def prepare_motion(source):
    """Delay the free tips, smooth the loop, and anchor the windward locks."""
    yy, xx = np.mgrid[0:506.25:109j, 0:900:193j]

    def zone(x, y, rx, ry):
        return np.exp(-2*(((xx-x)/rx)**2+((yy-y)/ry)**2))

    tips = np.clip(zone(734,444,120,80)+zone(409,469,67,82)+zone(327,129,86,43),0,1)[...,None]
    source = (source*(1-.73*tips)+np.roll(source,4,axis=0)*(.73*tips)).astype('f4')
    source = .2*np.roll(source,1,axis=0)+.6*source+.2*np.roll(source,-1,axis=0)

    weight = ease((xx-244)/24)*ease((459-xx)/40)*ease((237-yy)/28)
    length = np.clip((444-xx)/174,0,1)
    bubble_distance = np.sqrt(((xx-782)/12)**2+((yy-446)/12)**2)
    bubble_weight = ease((bubble_distance-1.05)/1.8)[...,None]
    for index, field in enumerate(source):
        angle = index / MOTION_FRAMES * 2 * np.pi
        root = field[round(142/506.25*108),round(448/900*192)].copy()
        drift_x = 1.8*np.sin(angle-.95*length)+.9*np.sin(2*angle-.5-.8*length)
        drift_y = 3.8*np.sin(angle-.35-1.1*length)+1.7*np.sin(2*angle+.35-1.1*length)
        anchored = np.stack([root[0]*(1-.46*length)+drift_x*length,
                             root[1]*(1-.46*length)+drift_y*length], axis=-1)
        field[:] = field*(1-weight[...,None])+anchored*weight[...,None]
        field *= bubble_weight
    return source


def motion_at(source, frame):
    position = frame / 2
    index = int(position)
    fraction = position - index
    current = source[index]
    if not fraction:
        return current
    following = source[(index + 1) % MOTION_FRAMES]
    before = source[index - 1]
    after = source[(index + 2) % MOTION_FRAMES]
    if fraction == .5:
        # Preserve the arithmetic of the established 60 Hz master.
        return (9 * (current + following) - before - after) / 16
    # Extend the same Catmull–Rom curve to fractional samples on a changed clock.
    return current + .5 * fraction * (
        following - before + fraction * (
            2 * before - 5 * current + 4 * following - after
            + fraction * (3 * (current - following) + after - before)
        )
    )
