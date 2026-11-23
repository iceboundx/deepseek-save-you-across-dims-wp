"""Build the eye mask while holding foreground hair in place."""

import cv2 as cv
import numpy as np

from .png import read_png, write_png


def bake(open_pose, output):
    face=read_png(open_pose).astype(np.int16)
    mask=np.zeros(face.shape[:2],np.uint8)
    contours=[[(348,270),(395,245),(430,216),(498,205),(555,216),(613,254),(649,309),(665,364),(660,435),(635,454),(576,459),(508,442),(437,420),(397,394),(369,352)],
              [(829,491),(858,458),(930,428),(979,432),(1037,459),(1074,493),(1122,550),(1150,600),(1185,665),(1162,681),(1101,676),(1050,678),(972,664),(922,644),(861,612),(834,572)]]
    for poly in contours:cv.fillPoly(mask,[np.asarray(poly,np.int32)],255)
    mask=cv.GaussianBlur(mask,(0,0),5)
    # Hold the hair in front of the face fixed, including the fine lock across the right eye.
    b,g,r=cv.split(face)
    hair=(b>r+34)&(b>g+15)&(r<158)
    openings=np.zeros_like(mask)
    for poly in [[(395,263),(443,225),(508,230),(566,257),(624,310),(647,375),(639,434),(573,449),(481,427),(413,401)],
                 [(843,498),(879,468),(945,458),(1015,479),(1078,529),(1142,622),(1155,663),(1060,681),(971,651),(866,611)]]:
        cv.fillPoly(openings,[np.asarray(poly,np.int32)],255)
    hair &= openings<30
    hold=cv.GaussianBlur(hair.astype(np.float32),(0,0),1.2)
    mask=np.round(mask*(1-hold)).astype(np.uint8)
    write_png(output, mask)
