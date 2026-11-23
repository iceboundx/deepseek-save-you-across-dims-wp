"""Loopable families of square flakes. Members share a source and peel apart in flight."""
import numpy as np
from PIL import Image

def step(a,b,x):
    v=np.clip((x-a)/(b-a),0,1)
    return v*v*(3-2*v)

def tracks(actor_path):
    rng=np.random.default_rng(68452)
    with Image.open(actor_path) as image:
        plate=np.asarray(image.resize((900,506),Image.Resampling.LANCZOS))
    alpha=plate[:,:,3]>150

    def contour(y,lo,hi):
        row=alpha[round(y)]
        ends=np.flatnonzero(row[:-1]&~row[1:])
        ends=ends[(ends>=lo)&(ends<=hi)]
        if not len(ends):
            return None
        return np.array([ends[-1]-.65,y])

    data=[]
    for group,total in enumerate([45,44,20,64]):
        count=0
        family=0
        while count<total:
            socket=False
            if group==0:
                origins=[(280,195),(304,203),(317,220),(339,227)]
                start=np.array(origins[family%4])+rng.normal([0,0],[5.8,2.8])
                wind=np.array([rng.uniform(-23,16),-rng.uniform(20,49)])
            elif group==1:
                starts=[(667,421),(691,417),(712,415)]
                start=np.array(starts[family%3])+rng.normal([0,0],[6.,2.8])
                if family%4==3:
                    edge=contour(rng.uniform(370,400),719,798)
                    if edge is not None:
                        start=edge
                        socket=True
                wind=np.array([rng.uniform(12,49),-rng.uniform(16,48)])
            elif group==2:
                start=np.array([(484,478),(506,470),(547,477)][family%3])+rng.normal([0,0],[3.8,3.6])
                wind=np.array([rng.uniform(-24,-5) if start[0]<520 else rng.uniform(6,26),-rng.uniform(17,38)])
            else:
                outer=family%5 in (2,4)
                # The head and the long outer lock are independent silhouettes.
                y0=[117,164,144,188,113][family%5]
                y=y0+rng.normal(0,6.)
                start=contour(y,811 if outer else 773,885 if outer else 804)
                if start is None:
                    continue
                socket=True
                wind=np.array([rng.uniform(19,46) if outer else rng.uniform(22,55),-rng.uniform(12,42)])
            base=rng.uniform(1.65,3.4) if family%4==0 else rng.uniform(1.18,2.54)
            if group==2:
                base*=.84
            elif group==3:
                base*=1.21 if family%3==0 else 1.10
            x,y=np.rint(start).astype(int)
            pixel=plate[y,max(0,x-2)]
            if pixel[3]<170:
                patch=plate[y-4:y+5,x-6:x+5]
                inside=patch[patch[:,:,3]>180]
                pixel=inside[len(inside)//2] if len(inside) else np.array([29,84,165,255])
            sample=np.clip(pixel[:3].astype(float)/max(1,int(pixel[3])),0,1)
            rate=rng.choice([3,3,4,5])
            offset=rng.random()
            seed=rng.random()
            angle=rng.uniform(-.23,.23)
            curl=rng.uniform(2.,9.)
            ink=rng.integers(0,5)
            # Large flakes carry a notch and shed one or two smaller neighbours.
            members=min(total-count,[3,1,2,1][family%4])
            for k in range(members):
                spread=np.array([0.,0.]) if k==0 else rng.normal([2.6,-2.5],[2.3,2.8])
                kick=np.zeros(2) if k==0 else rng.normal([2,-1.5],[5.,6.])
                radius=base*([1,.53,.37][k])
                data.append((start+spread,wind+kick,rate,offset+.014*k,seed,radius,angle+.05*k,curl,
                             ink if k==0 else (ink+k)%5,sample,group,socket and k==0,k))
            count+=members
            family+=1
    starts,velocity,rate,offset,seed,radius,angle,curl,ink,paint,group,cut,child=map(np.asarray,zip(*data))
    palette=np.array([[.055,.86,1.],[.25,.90,.98],[.04,.66,.93],[.63,.95,1.],[.10,.57,.87]])
    cold=palette[ink].copy()
    cold[(group==2)&(ink!=3)]*=[.47,.74,.86]
    temple_palette=np.array([[.08,.96,1.],[.40,.93,1.],[.035,.48,.83],[.81,.98,1.],[.075,.32,.63]])
    cold[group==3]=temple_palette[ink[group==3]]
    def sample(phase):
        sec=phase*13.6
        # Faster shedding as each fault lands. The clock is continuous and
        # advances by exactly one turn over the full clip.
        clock=phase+.021*(step(2.91,3.31,sec)+step(11.17,11.58,sec)-2*phase)
        raw=rate*clock+offset
        age=raw%1
        cycle=np.floor(raw).astype(int)%rate
        rand=np.sin(6.283185*(seed+cycle*.381966))
        bend=np.sin(age*np.pi)
        lane=np.column_stack([curl*bend*np.sin(6.28*seed+age*2.4),
                              -curl*.44*bend*np.cos(5.6*seed+age*2.1)])
        progress=age*(1.29-.29*age)
        position=starts+velocity*(progress*(1.+.24*rand))[:,None]+lane
        position[:,0]+=age**1.45*rand*7.
        direction=angle+.39*np.sin(5.5*seed+age*2.4)*age
        points=np.column_stack([position,radius*(1.-.39*age),direction])
        # A fresh fragment borrows the colour of its parent paint, catching a
        # cyan edge as it separates. Ink-coloured and pale fragments coexist.
        tint=(.49+.43*step(.015,.30,age)-.15*step(.55,.98,age))
        tint-=.23*((ink==4)&(group!=2))
        tint=np.where(group==2,.94,tint)
        tint=np.where(group==3,np.minimum(1.,tint+.16),tint)
        colour=(1.-tint[:,None])*paint+tint[:,None]*cold
        opacity=step(.005,.068,age)*(1.-step(.67,.985,age))*(.92+.07*np.cos(seed*9.))
        chips=np.column_stack([np.clip(colour,0,1),opacity])
        removed=step(.018,.15,age)*(1.-step(.29,.68,age))*cut*.93
        sockets=np.column_stack([starts,radius*.97,removed])
        return points.astype('f4'),chips.astype('f4'),sockets.astype('f4')
    return sample
