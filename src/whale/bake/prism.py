"""Extract the painted light along the finger prism."""

import cv2 as cv
import numpy as np

from .png import read_png, write_png


def bake(base, output):
    art=read_png(base).astype('f4')/255.
    scale=3840/900.
    # Parameterise the paint across and along the diagonal shaft. Sampling inside
    # the digit avoids transferring its ink outline into the stationary light.
    yy,xx=np.mgrid[0:256,0:192].astype('f4')
    x=np.clip(215.+xx/192.*50.,226.25,252.)
    t=(yy+.5)/256.*70.-35
    center=206.5+1.15*(x-225.)
    def sample(offset):
        return cv.remap(art,(x*scale-.5).astype('f4'),((center+offset)*scale-.5).astype('f4'),cv.INTER_LINEAR)
    a=sum(sample(j) for j in [-26,-25,-24])/3
    b=sum(sample(j) for j in [24,25,26])/3
    fraction=((t+25)/50).clip(0,1)[...,None]
    baseline=a*(1-fraction)+b*fraction
    taper=((26-np.abs(t))/5).clip(0,1)[...,None]
    delta=(sample(t)-baseline)*taper
    encoded=np.rint((cv.GaussianBlur(delta,(0,0),1.65)*.85+.5).clip(0,1)*255).astype('uint8')
    write_png(output, encoded)
