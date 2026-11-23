"""Extract the hand matte from the painted base."""

import cv2 as cv
import numpy as np

from .png import read_png, write_png


def bake(base, output):
    src = read_png(base)
    scale = src.shape[1] / 900
    top = round(140 * scale)
    # Trace the outside ink at the five fingers, between them and along the heel of the palm.
    points = [
        (17,228),(16,225),(20,220),(28,217),(54,213),(79,206),(101,194),
        (113,184),(122,180),(94,174),(66,165),(44,153),(30,140),(21,128),(19,122),
        (21,117),(26,114),(32,115),(52,123),(78,133),(102,139),(132,144),(152,146),
        (158,146),(143,131),(128,113),(114,94),(102,73),(95,53),(94,41),(98,34),
        (103,33),(110,35),(120,43),(136,61),(151,81),(168,100),(186,118),
        (199,130),(205,136),(213,136),(219,131),(220,110),(222,83),(222,54),
        (225,28),(231,15),(237,10),(244,10),(250,14),(254,24),(257,43),
        (259,70),(259,99),(258,124),(261,142),(272,165),(285,186),(302,201),
        (322,213),(346,221),(365,228),(374,235),(377,242),(373,250),
        (363,256),(344,260),(323,260),(307,256),(288,246),(274,240),
        (247,240),(230,237),(214,230),(200,220),(194,218),(186,219),
        (170,226),(153,227),(142,224),(132,219),(124,222),(116,220),
        (105,224),(82,232),(57,237),(39,237),(24,233)
    ]
    roi = src[top:top+round(275*scale), :round(396*scale)]
    outline = np.zeros(roi.shape[:2], np.uint8)
    cv.fillPoly(outline,[np.round(np.array(points)*scale).astype('int32')],255)
    inner = cv.distanceTransform(outline, cv.DIST_L2,5)
    outer = cv.distanceTransform(255-outline, cv.DIST_L2,5)
    mask = np.where(outline,cv.GC_PR_FGD,cv.GC_PR_BGD).astype('uint8')
    mask[inner > 8*scale] = cv.GC_FGD
    mask[outer > 7*scale] = cv.GC_BGD
    cv.setNumThreads(4)
    cv.setRNGSeed(0)
    cv.grabCut(roi,mask,None,np.zeros((1,65),'f8'),np.zeros((1,65),'f8'),4,cv.GC_INIT_WITH_MASK)
    hard = ((mask & 1)*255).astype('uint8')
    contours,_ = cv.findContours(hard,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    hard.fill(0)
    cv.drawContours(hard,[max(contours,key=cv.contourArea)],-1,255,cv.FILLED)
    alpha = cv.GaussianBlur(hard,(0,0),.90)
    write_png(output, alpha)
