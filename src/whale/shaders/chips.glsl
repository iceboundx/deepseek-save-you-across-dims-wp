uniform vec4 chips[173],chipInk[173],sockets[173];

// These square bites open on traced edges of the opaque character plate.
// The actual moving water plate is exposed through them in the compositor.
vec2 missingInk(vec2 p){
    vec2 q=p*canvasSize;
    bool hair=q.x>765.&&q.x<891.&&q.y>77.&&q.y<225.;
    bool shoulder=q.x>716.&&q.x<803.&&q.y>361.&&q.y<407.;
    if(!hair&&!shoulder)return vec2(0.);
    int begin=hair?109:45,end=hair?173:89;
    vec2 result=vec2(0.);
    for(int i=begin;i<end;i++){
        vec4 s=sockets[i];
        vec2 d=abs(q-s.xy);
        float edge=max(d.x,d.y)-s.z;
        result.x=max(result.x,s.w*(1.-smoothstep(-.14,.18,edge)));
        float lip=smoothstep(-.09,.22,edge)*(1.-smoothstep(.35,1.08,edge));
        lip*=1.-smoothstep(.05,.73,(q.x-s.x)/max(.2,s.z));
        result.y=max(result.y,lip*s.w);
    }
    return result;
}

vec3 fragments(vec3 col,vec2 p){
    vec2 q=p*canvasSize;
    int begin,end;
    if(q.x>220.&&q.x<390.&&q.y>113.&&q.y<261.){begin=0;end=45;}
    else if(q.x>615.&&q.x<876.&&q.y>296.&&q.y<467.){begin=45;end=89;}
    else if(q.x>423.&&q.x<609.&&q.y>398.){begin=89;end=109;}
    else if(q.x>763.&&q.y>19.&&q.y<229.){begin=109;end=173;}
    else return col;
    for(int i=begin;i<end;i++){
        vec4 data=chips[i],ink=chipInk[i];
        vec2 d=q-data.xy;
        if(max(abs(d.x),abs(d.y))>data.z*1.49+.32)continue;
        float c=cos(data.w),s=sin(data.w);
        vec2 v=mat2(c,-s,s,c)*d;
        float box=max(abs(v.x),abs(v.y))-data.z;
        float cover=1.-smoothstep(-.15,.16,box);
        vec3 colour=ink.rgb;
        if(i%13==2&&data.z>1.25) cover*=smoothstep(-.72,-.48,box);
        if(i%4==0&&data.z>1.5){
            // Asymmetric bevel in the square's own coordinates.
            float rim=1.-smoothstep(.15,.55,min(v.x,v.y)+data.z);
            colour=mix(colour,vec3(.68,.96,1.),.57*rim);
        }
        col=mix(col,colour,cover*ink.a);
    }
    return col;
}

vec3 sapphire(vec3 col,vec2 p,float t){
    vec2 q=p*canvasSize,d=q-vec2(524.2,343.8);
    if(abs(d.x)>56.||d.y< -25.||d.y>100.)return col;
    float wave=.5+.5*sin(2.*t-.68+.45*sin(t+.25));
    vec2 axis=vec2(d.x+.13*d.y,d.y);
    vec2 stoneD=axis/vec2(6.8,10.9);
    float stone=1.-smoothstep(.65,1.05,dot(stoneD,stoneD));
    float facet=exp(-pow((axis.x+.34*d.y-mix(-6.2,6.4,wave))/1.95,2.));
    vec2 glint=axis-vec2(-3.5+4.6*wave,-4.7+1.8*wave);
    float pin=exp(-dot(glint,glint)/2.4);
    vec2 bow=(d-vec2(1.,5.))/vec2(24.,17.);
    float bounce=exp(-dot(bow,bow));
    vec2 tail=(d-vec2(8.,31.))/vec2(35.,40.);
    float fold=exp(-dot(tail,tail));
    float blue=smoothstep(.035,.23,col.b-col.r);
    float crest=exp(-pow((d.x-.36*d.y+4.*sin(d.y*.13)-mix(-16.,16.,wave))/5.9,2.));
    col+=(1.-col)*(stone*(vec3(.15,.67,.88)*facet*(.47+.48*wave)+vec3(.62,.92,.96)*pin)
          +vec3(.012,.30,.58)*bounce*(.19+.68*wave)
          +vec3(.025,.30,.64)*blue*fold*crest*(.43+.47*wave));
    return clamp(col,0.,1.);
}
