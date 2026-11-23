#version 330
uniform sampler2D scene;
uniform sampler3D printGrade;
uniform float seconds, peripheralFocus;
out vec4 frag;
const vec2 size=vec2(3840.,2160.);

#include "focus.glsl"


// A lens falloff on all four corners also affects close ribbons and peripheral
// HUDs. The independent water-depth pass still handles gaps between the locks.
vec3 exposure(vec2 p){
    vec2 radial=abs(2.*p-1.);
    vec2 nearest=1.-radial;
    float corner=1.-smoothstep(.09,.65,length(nearest*vec2(1.07,.94)));
    float focus=lensPull(seconds);
    float cuff=(1.-smoothstep(.13,.37,p.x))*smoothstep(.63,.89,p.y);
    float distant=mix(.32,1.25,focus);
    float nearer=mix(1.04,.40,focus);
    float coc=peripheralFocus*corner*mix(20.,27.,p.y)*mix(distant,nearer,cuff);
    if(coc>.55)coc*=mix(1.,.08,textureLod(scene,p,0.).a);
    if(coc<.55)return textureLod(scene,p,0.).rgb;
    float level=clamp(log2(max(1.,coc*.53)),0.,5.);
    vec3 sum=textureLod(scene,p,level).rgb*.16;
    for(int i=0;i<8;i++){
        float a=float(i)*.7853982+.19635;
        sum+=.105*textureLod(scene,p+vec2(cos(a),sin(a))*coc*.64/size,level).rgb;
    }
    return sum;
}
vec3 develop(vec2 p){
    vec3 c=exposure(p);
    float y=dot(c,vec3(.2126,.7152,.0722)), mid=4.*y*(1.-y);
    vec3 foundation=mix(vec3(y),c,.972);
    foundation+=(1.-c)*vec3(.001,.015,.036)*smoothstep(.01,.37,c.b-c.r)*mid;
    foundation+=(1.-c)*vec3(.017,.005,.001)*smoothstep(.02,.33,c.r-c.b)*mid;
    vec3 colour=texture(printGrade,(clamp(foundation,0.,1.)*48.+.5)/49.).rgb;
    float sea=smoothstep(.81,.956,p.x)*smoothstep(.08,.27,c.g-c.r)
        *smoothstep(.08,.32,y)*(1.-smoothstep(.70,.93,c.g));
    colour-=sea*vec3(.056,.034,.011);
    vec2 cheek=(p-vec2(.624,.477))/vec2(.157,.227);
    float skin=(1.-smoothstep(.65,1.15,dot(cheek,cheek)))*smoothstep(.03,.13,c.r-c.g);
    return clamp(colour+skin*vec3(.014,-.010,-.025),0.,1.);
}

uniform sampler2D handPlane;
vec3 labFromDisplay(vec3 c){
    vec3 lin=mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));
    vec3 xyz=vec3(dot(lin,vec3(.4124564,.3575761,.1804375))/.95047,
                  dot(lin,vec3(.2126729,.7151522,.0721750)),
                  dot(lin,vec3(.0193339,.1191920,.9503041))/1.08883);
    vec3 f=mix(7.787*xyz+16./116.,pow(max(xyz,vec3(0.)),vec3(1./3.)),step(vec3(.008856),xyz));
    return vec3(116.*f.y-16.,500.*(f.x-f.y),200.*(f.y-f.z));
}
vec3 displayFromLab(vec3 lab){
    float fy=(lab.x+16.)/116.;
    vec3 f=vec3(fy+lab.y/500.,fy,fy-lab.z/200.);
    vec3 xyz=mix((f-16./116.)/7.787,f*f*f,step(vec3(.206897),f))*vec3(.95047,1.,1.08883);
    vec3 lin=vec3(dot(xyz,vec3(3.24045,-1.53714,-.49853)),
                  dot(xyz,vec3(-.96927,1.87601,.04156)),
                  dot(xyz,vec3(.05564,-.20403,1.05723)));
    return mix(12.92*lin,1.055*pow(max(lin,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),lin));
}
vec3 finalPrint(vec3 c,vec2 p){
    float y=dot(c,vec3(.2126,.7152,.0722));
    float navy=smoothstep(.12,.34,c.b-c.r)*smoothstep(.035,.18,c.b-c.g)*(1.-smoothstep(.28,.57,y));
    float sat=max(c.r,max(c.g,c.b))-min(c.r,min(c.g,c.b));
    float pearl=(1.-smoothstep(.13,.31,sat))*smoothstep(.43,.77,y)*(1.-smoothstep(.88,.99,y));
    pearl*=1.-.72*smoothstep(.025,.105,c.r-c.b);
    c=clamp(c+navy*vec3(-.0055,-.0105,.002)+pearl*vec3(.008,.0025,-.014),0.,1.);
    float matte=texture(handPlane,p).r;
    if(matte<.001)return c;
    vec3 lab=labFromDisplay(c);
    float middle=smoothstep(30.,48.,lab.x)*(1.-smoothstep(72.,91.,lab.x));
    float skin=1.-smoothstep(13.,25.,length(lab.yz-vec2(10.,3.)));
    float a=matte*middle*skin;
    lab.x+=1.30*a;
    lab.y+=a*clamp(.80*(11.45-lab.y),0.,1.85);
    lab.z+=a*clamp(.85*(4.20-lab.z),0.,5.6);
    return clamp(displayFromLab(lab),0.,1.);
}


#ifndef SIGNAL_FAULT
void main(){vec2 uv=gl_FragCoord.xy/size;frag=vec4(finalPrint(develop(uv),uv),1.);}
#endif
