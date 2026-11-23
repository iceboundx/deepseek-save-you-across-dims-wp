"""Separate two painted optical emissions from the stationary water plate."""

import cv2 as cv
import numpy as np
from PIL import Image


def bake(ocean, output):
    scale = 3840/900
    width, height = 1184, 920
    with Image.open(ocean) as image:
        rgb = np.asarray(image.convert('RGB'))[:height, :width].copy()
    y, x = np.mgrid[:height,:width].astype('f4')/scale

    def step(a,b,value):
        t = np.clip((value-a)/(b-a),0,1)
        return t*t*(3-2*t)

    # These two ribbons are painted through the corner reflection. Interpolate the
    # illumination behind them and retain their original edges in the static plate.
    knots = [0,10,20,30,40,50,60,70,80,90,100]
    left = [[59,67,60,56,52,48,46,44,43,44,45],
            [121,115,109,104,99,94,90,87,83,81,79]]
    right = [[86,80,74,70,66,62,59,58,56,56,58],
             [152,139,131,123,116,109,103,97,92,88,86]]
    # At the top edge the inner ribbon is a narrow pale pink stroke.
    left[0][:3]=[64,60,56]
    ribbon=np.zeros((height,width),'f4')
    for lo,hi in zip(left,right):
        low=np.interp(y[:,0],knots,lo)[:,None]
        high=np.interp(y[:,0],knots,hi)[:,None]
        ribbon=np.maximum(ribbon,step(-1.3,.8,np.minimum(x-low,high-x)))

    small=cv.resize(rgb,None,fx=.32,fy=.32,interpolation=cv.INTER_AREA)
    rm=cv.resize(np.uint8((ribbon>.02)*255),small.shape[1::-1],interpolation=cv.INTER_AREA)
    fill=cv.inpaint(small,rm,5,cv.INPAINT_NS)
    corner=cv.resize(fill,(width,height),interpolation=cv.INTER_CUBIC).astype('f4')/255
    corner=cv.GaussianBlur(corner,(0,0),2.5)
    raw=rgb.astype('f4')/255
    corner=np.where((ribbon<.001)[...,None],cv.GaussianBlur(raw,(0,0),1.7),corner)
    radius=np.sqrt(((x-36)/108)**2+((y-3)/89)**2)
    support=1-step(.84,1.13,radius)
    water=np.stack([.12+.08*step(0,130,x),.24+.08*step(0,110,x),.47+.13*step(0,115,x)],axis=-1)
    corner_layer=(corner-water)*support[...,None]

    # Remove the fine water lines from the travelling star's broad glow. Only its
    # sharp rays and hot core travel at full spatial resolution.
    dx,dy=x-193.9,y-134.
    r=np.sqrt((dx/43)**2+(dy/36)**2)
    sm=cv.resize(np.uint8((r<.95)*255),small.shape[1::-1],interpolation=cv.INTER_AREA)
    base=cv.resize(cv.inpaint(small,sm,9,cv.INPAINT_NS),(width,height),interpolation=cv.INTER_CUBIC).astype('f4')/255
    base=cv.GaussianBlur(base,(0,0),11.)
    soft=cv.GaussianBlur(raw,(0,0),9.)
    fine=1-step(6,14,np.hypot(dx,dy))
    for vx,vy,length in [(.965,-.264,58),(.54,.842,48),(.35,.937,36),(-.26,.966,29),(.80,.60,25)]:
        line=np.abs(dx*vy-dy*vx)
        along=np.abs(dx*vx+dy*vy)
        fine=np.maximum(fine,(1-step(.7,2.8,line))*(1-step(.65*length,length,along)))
    star=(soft+(raw-soft)*fine[...,None]-base)*(1-step(.72,1.12,r))[...,None]
    atlas=np.dstack([corner_layer+star,1-.83*ribbon*(1-step(.86,1.16,radius))]).astype('f2')
    np.save(output, atlas)
