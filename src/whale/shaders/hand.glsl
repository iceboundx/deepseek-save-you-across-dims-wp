uniform sampler2D skinMask;
const vec2 drawing=vec2(900.,506.25);
uniform sampler2D prism;
vec3 prismLight(vec2 point){
    float along=point.y-(206.5+1.15*(point.x-225.));
    return texture(prism,vec2((point.x-215.)/50.,(along+35.)/70.)).rgb/.85;
}
mat2 rotation(float a){
    float s=sin(a),c=cos(a);
    return mat2(c,s,-s,c);
}
// Bends are confined to individual digits. The palm, and the ink past each joint,
// follow rigid transforms. Distinct joint timings also change the gaps between fingers.
vec2 digitDelta(vec2 q, vec2 knuckle, vec2 tip, float radius, float angle){
    vec2 axis=tip-knuckle;
    float along=dot(q-knuckle,axis)/dot(axis,axis);
    vec2 nearest=knuckle+clamp(along,0.,1.)*axis;
    float extent=1.-smoothstep(radius,radius+6.,length(q-nearest));
    float joint=smoothstep(-.04,.26,along);
    return extent*(rotation(angle*joint)*(q-knuckle)-(q-knuckle));
}
vec3 drawHand(vec2 p,vec2 screen,vec3 outside){
    if(p.x>.459||p.y<.25||p.y>.84)return outside;
    vec2 area=vec2(textureSize(skinMask,0)), start=vec2(0.,597.);
    vec3 col=outside;
    float t=phase*2.*pi;
    float reach=smoothstep(.025,.385,phase)*(1.-smoothstep(.49,.945,phase));
    float drift=sin(t+.18);
    vec2 wrist=vec2(238.,340.);
    vec2 shift=vec2(-2.35*reach+.55*drift,-1.65*reach+1.12*sin(t));
    vec2 q=wrist+rotation(.020*reach-.003*drift)*(p*drawing-wrist-shift)/(1.+.017*reach);
    float release=smoothstep(.38,.57,phase)*(1.-smoothstep(.62,.91,phase));
    vec2 source=q;
    source+=digitDelta(q,vec2(238.,272.),vec2(241.,150.),19.,.026*reach-.020*release);
    source+=digitDelta(q,vec2(191.,282.),vec2(102.,174.),15.,-.024*reach+.018*release);
    source+=digitDelta(q,vec2(149.,305.),vec2(23.,257.),16.,-.037*reach+.016*sin(t-.28));
    source+=digitDelta(q,vec2(127.,340.),vec2(20.,368.),14.,-.047*reach+.025*sin(t-.88));
    source+=digitDelta(q,vec2(249.,352.),vec2(374.,384.),23.,.037*reach-.020*release);
    vec2 uvHand=source/drawing, m=(uvHand*size-start)/area;
    if(all(greaterThanEqual(m,vec2(0)))&&all(lessThanEqual(m,vec2(1)))){
        vec3 flesh=texture(art,uvHand).rgb;
        if(source.x>216.&&source.x<264.&&source.y>155.&&source.y<281.){
            float lit=smoothstep(.19,.57,max(flesh.r,.85*flesh.g));
            vec3 onSkin=prismLight(screen*drawing)-vec3(.5/.85);
            float shine=.9+.20*(.51+.26*sin(2.*t-.8)+.14*sin(3.*t+.65)+.09*sin(t-1.05))
                +.10*exp(-((phase*13.6-11.65)/.34)*((phase*13.6-11.65)/.34));
            flesh+=lit*(onSkin*shine-prismLight(source)+vec3(.5/.85));
        }
        handCoverage=texture(skinMask,m).r;
        col=mix(col,flesh,handCoverage);
    }
    return col;
}
