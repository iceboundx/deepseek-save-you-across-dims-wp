"""Fit the tracked hand and face, then stabilize the bow and shirt front."""

import json

import cv2 as cv
import numpy as np

from ..timeline import MOTION_FRAMES, SIZE


WIDTH, HEIGHT = SIZE
scale=np.array([WIDTH/1254,HEIGHT/706])
hand_outline=[(12,533),(12,344),(116,223),(304,193),(362,192),(384,255),(379,378),(428,464),(526,495),(540,540),(521,570),(452,568),(341,535),(190,541)]
face_outline=[(626,190),(667,119),(817,77),(937,119),(1000,231),(967,333),(877,419),(804,442),(718,441),(649,384),(614,302)]
hand_points=[(334,232),(331,305),(328,378),(161,281),(229,359),(90,395),(165,426),(94,506),(175,475),(255,441),(311,474),(357,485),(448,517),(501,536)]
face_points=[(685,235),(728,244),(861,311),(904,334),(764,298),(746,356),(785,412),(850,390),(683,329),(827,246)]
def sample(grid,x,y):
    gx=np.clip(x/WIDTH*(grid.shape[1]-1),0,grid.shape[1]-1-.00001)
    gy=np.clip(y/HEIGHT*(grid.shape[0]-1),0,grid.shape[0]-1-.00001)
    ix,iy=gx.astype('i4'),gy.astype('i4')
    fx,fy=(gx-ix)[...,None],(gy-iy)[...,None]
    return (grid[iy,ix]*(1-fx)+grid[iy,ix+1]*fx)*(1-fy)+(grid[iy+1,ix]*(1-fx)+grid[iy+1,ix+1]*fx)*fy
def mask(poly,margin,blend):
    raw=np.zeros((706,1254),np.uint8)
    cv.fillPoly(raw,[np.array(poly,np.int32)],255)
    dist=cv.distanceTransform(255-raw,cv.DIST_L2,cv.DIST_MASK_PRECISE)
    t=np.clip((dist-margin)/blend,0,1)
    return 1-t*t*(3-2*t)
def fit(grid,points):
    pts=np.asarray(points)*scale;center=pts.mean(0);a=pts-center
    dst=pts+sample(grid,pts[:,0],pts[:,1]);b=dst-dst.mean(0)
    angle=np.arctan2(np.sum(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b))
    return center,dst.mean(0)-center,angle
def filtered(x):
    # Circular filtering uses neighbors across the playback seam.
    return sum(w*np.roll(x,n,axis=0) for n,w in [(-2,.08),(-1,.22),(0,.40),(1,.22),(2,.08)])
def tracked_field(motion_json):
    data = json.loads(motion_json.read_text(encoding="utf-8"))
    tracked = np.asarray(data["frames"], dtype="f4").reshape(-1, data["rows"], data["cols"], 2) * data["scaleToPixels"]
    gx,gy=np.meshgrid(np.linspace(0,WIDTH,193),np.linspace(0,HEIGHT,109))
    loc=np.stack([gx,gy],-1)
    shapes=[(hand_points,hand_outline,17,44),(face_points,face_outline,12,55)]
    layers=[]; smoothed=filtered(tracked)
    for pts,poly,pad,blend in shapes:
        alpha=cv.resize(mask(poly,pad,blend),(193,109),interpolation=cv.INTER_LINEAR)[...,None]
        layers.append((pts,alpha))
    fields=[]
    for i in range(MOTION_FRAMES):
        clock=2*np.pi*i/MOTION_FRAMES
        angle=2*clock+.17*(np.sin(clock+.45)-np.sin(.45))+.06*np.sin(2*clock)
        pos=(angle/(2*np.pi)*len(smoothed))%len(smoothed)
        k=int(pos);t=pos-k;observed=(1-t)*smoothed[k]+t*smoothed[(k+1)%len(smoothed)]
        field=.83*sample(observed,gx,gy)
        for idx,(pts,alpha) in enumerate(layers):
            center,delta,rot=fit(observed,pts)
            if idx==0:
                delta=.8*delta+[7.5*np.sin(clock+.3),4.8*np.cos(clock+.3)]
                rot=.009*np.tanh(rot/.009)+.0015*np.sin(clock-.7)
            else:
                delta=.79*delta+[3.9*np.cos(clock-.45),3.2*np.sin(clock-.45)]
                rot=.006*np.tanh(rot/.006)+.0011*np.cos(clock-.2)
            cs,sn=np.cos(rot),np.sin(rot)
            rigid=(loc-center)@np.array([[cs-1,sn],[-sn,cs-1]])+delta
            field=field*(1-alpha)+rigid*alpha
        fields.append(field.astype('f4'))
    fields=np.asarray(fields)
    return fields


def stabilize_cloth(grid):
    poly=[(381,658),(414,606),(503,564),(565,545),(625,500),(672,453),
          (709,443),(754,445),(811,437),(859,456),(887,516),(881,611),
          (845,706),(380,706)]
    anchors=np.array([(677,503),(705,540),(729,477),(753,502),(766,553),(785,586),
                      (809,540),(710,620),(730,602),(730,635),(729,667),(762,669)])*scale
    gy,gx=np.mgrid[0:2160:109j,0:3840:193j]
    locations=np.stack([gx,gy],axis=-1)
    alpha=mask(poly,14,56)
    protected=np.maximum(mask(hand_outline,4,17),mask(face_outline,0,11))
    alpha=cv.resize(alpha*(1-protected),(193,109),interpolation=cv.INTER_AREA)[...,None]
    center=np.array([730,562])*scale
    parameters=[]
    for f in grid:
        obs=sample(f,anchors[:,0],anchors[:,1])
        # Fit one translation and rotation, with fixed scale, for collar, bow and shirt front.
        delta=np.median(obs,axis=0)
        rel=anchors-center
        theta=np.sum(rel[:,0]*(obs[:,1]-delta[1])-rel[:,1]*(obs[:,0]-delta[0]))/np.sum(rel**2)
        parameters.append([*delta,theta])
    parameters=np.asarray(parameters)
    # Filter periodically in time, retaining the underlying swaying motion.
    parameters=sum(np.roll(parameters,k,axis=0)*w for k,w in zip(range(-3,4),[.06,.115,.2,.25,.2,.115,.06]))
    new=[]
    for i,(dx,dy,theta) in enumerate(parameters):
        angle=.0045*np.tanh(theta/.0045)
        cs,sn=np.cos(angle),np.sin(angle)
        delta=np.array([.72*dx,.67*dy])
        inv=(locations-center)@np.array([[cs-1,sn],[-sn,cs-1]])+delta
        new.append(((1-alpha)*grid[i]+alpha*inv).astype('f4'))
    new=np.asarray(new)
    return new


def bake(motion_json, output):
    np.save(output, stabilize_cloth(tracked_field(motion_json)))
