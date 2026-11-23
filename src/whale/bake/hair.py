"""Separate the moving blue fringe and reconstruct its underlying skin plane."""

import cv2 as cv
import numpy as np
from PIL import Image


def bake(base, matte, face_under):
    # Coordinates in the labelled reference crop, whose scale is three per design pixel.
    scale=3840/900
    x0,y0=round(426*scale),round(67*scale)
    w,h=round(311*scale),round(274*scale)
    with Image.open(base) as im:
        rgb=np.asarray(im.convert('RGB').crop((x0,y0,x0+w,y0+h)))
    def polygon(points):
        m=np.zeros((h,w),'u1')
        cv.fillPoly(m,[np.rint(np.asarray(points)*scale/3).astype('i4')],1)
        return m.astype(bool)
    # Only blue paint beside the cheeks or emerging from the fringe may be lifted.
    # Mark the lashes, iris, brows and the back layer that lies below the jaw.
    left_eye=polygon([(190,253),(205,246),(218,236),(225,221),(248,235),(282,238),(317,251),
                      (336,265),(356,290),(366,313),(353,350),(325,381),(285,389),
                      (232,378),(207,354),(188,328),(182,294)])
    right_eye=polygon([(509,418),(534,400),(559,393),(596,389),(624,397),(653,408),
                       (674,426),(690,457),(706,486),(721,514),(734,542),(707,536),
                       (667,549),(613,545),(567,529),(535,512),(516,488)])
    not_front=polygon([(0,537),(102,530),(151,544),(208,545),(232,586),(291,639),
                       (335,692),(397,701),(451,679),(499,665),(544,642),(591,639),
                       (634,636),(669,632),(602,688),(550,712),(603,727),(682,709),
                       (702,763),(942,776),(942,875),(-2,875)])
    rr,gg,bb=rgb.astype('f4').transpose(2,0,1)
    def view_poly(pts):return polygon(np.asarray(pts)*933/748)
    brow_l=view_poly([(159,128),(198,127),(231,132),(257,138),(285,149),(311,160),
                      (344,178),(345,184),(313,168),(286,155),(251,145),(220,140),(188,135),(158,135)])
    brow_r=view_poly([(465,239),(493,253),(524,274),(554,298),(565,311),(553,307),(519,285),(488,264),(464,251)])
    wide=cv.GaussianBlur((bb-rr>9.).astype('f4'),(0,0),7.5)
    permitted=~(left_eye|right_eye|((brow_l|brow_r)&(wide<.55))|not_front)
    seed=((bb-rr>9.) & permitted).astype('u1')
    seed=cv.morphologyEx(seed,cv.MORPH_CLOSE,cv.getStructuringElement(cv.MORPH_ELLIPSE,(5,5)))
    # Exclude isolated blue embroidery/noise, retain flyaway lines connected to the scalp.
    _,labels,stats,_=cv.connectedComponentsWithStats(seed,connectivity=8)
    retain=stats[:,cv.CC_STAT_AREA]>45
    retain[0]=False
    seed=(retain[labels]&permitted).astype('u1')
    distance=cv.distanceTransform(1-seed,cv.DIST_L2,5)
    ink=(rr<116)&(gg<103)&(distance<14)&permitted
    edge=cv.dilate((seed|ink).astype('u1'),cv.getStructuringElement(cv.MORPH_ELLIPSE,(3,3)))
    alpha=cv.GaussianBlur(edge.astype('f4'),(0,0),.55)
    distance=cv.distanceTransform(1-edge,cv.DIST_L2,5)
    u=np.clip((distance-5.)/24.,0,1)
    support=1-u*u*(3-2*u)
    protected=(left_eye|right_eye|((brow_l|brow_r)&(wide<.40))|not_front)
    support[protected]=alpha[protected]
    skin=(rr-gg>4)&(rr-bb>5)&(rr>118)&(gg>86)&(distance>14.)&~(left_eye|right_eye)
    solid=(~skin).astype('u1')
    yy,xx=np.indices((h,w))
    _,nearest=cv.distanceTransformWithLabels(solid,cv.DIST_L2,5,labelType=cv.DIST_LABEL_PIXEL)
    donors=np.empty((nearest.max()+1,2),'i4')
    donors[nearest[solid==0]]=np.stack([xx[solid==0],yy[solid==0]],axis=1)
    atlas=np.stack([alpha,support],axis=2)
    np.save(matte, atlas.astype('f2'))
    # Rebuild the skin plane under the travel band from observed skin *away* from
    # the antialiased ink. The cast shadow moves with its hair as a signed residual.
    def summed(img,k):
        for _ in range(3):img=cv.blur(img,(k,k))
        return img
    clean=rgb[donors[nearest,1],donors[nearest,0]].astype('f4')
    inkskin=rgb.astype('f4')*skin[:,:,None]
    for kernel in [95,47,23,13]:
        den=summed(skin.astype('f4'),kernel)
        estimate=summed(inkskin,kernel)/np.maximum(.00001,den[:,:,None])
        blend=np.clip((den-.018)/.16,0,1)[:,:,None]
        clean+=blend*(estimate-clean)
    def ramp(a,b,x):
        u=np.clip((x-a)/(b-a),0,1)
        return u*u*(3-2*u)
    eye_distance=cv.distanceTransform((~(left_eye|right_eye)).astype('u1'),cv.DIST_L2,5)/scale
    brow_distance=cv.distanceTransform((~((brow_l|brow_r)&(wide<.50))).astype('u1'),cv.DIST_L2,5)/scale
    guard=ramp(6.,16.,eye_distance)*ramp(2.,8.,brow_distance)
    Image.fromarray(np.dstack([np.clip(clean,0,255),guard*255]).astype('u1')).save(face_under)
