#version 330
uniform sampler2D art, lid, eyeMask, panel, headings, logAtlas, dust, motion;
uniform float closed, phase;
layout(location=0) out vec4 frag;
layout(location=1) out float handOut;
// Shared with the finishing pass to localize the skin grade.
float handCoverage=0.;
const vec2 size=vec2(3840.,2160.);
const vec2 design=vec2(1672.,941.);
const float pi=3.14159265359;
uniform sampler2D actor;
const vec2 canvasSize=vec2(900.,506.25);

#include "light.glsl"
#include "hand.glsl"
#include "silk.glsl"
#include "glints.glsl"
#include "focus.glsl"
#include "water-focus.glsl"
#include "chips.glsl"
#include "hair.glsl"
#include "hud.glsl"

void main(){
    vec2 uv=gl_FragCoord.xy/size, dims=vec2(textureSize(motion,0));
    vec2 displacement=texture(motion,(uv*(dims-1.)+.5)/dims).rg;
    vec2 p=uv+displacement/size;
    vec4 person=texture(actor,p);
    vec2 removal=missingInk(p);
    person.rgb=mix(person.rgb,vec3(.19,.84,1.)*person.a,.72*removal.y);
    person*=1.-removal.x;
    vec3 col=person.rgb/max(person.a,0.00001);
    if(closed>.0001){
        vec2 e=(p*size-vec2(1695.,390.))/vec2(1380.,850.);
        if(all(greaterThan(e,vec2(0)))&&all(lessThan(e,vec2(1)))){
            float a=texture(eyeMask,e).r;
            col=mix(col,texture(lid,e).rgb,a);
        }
    }
    col=animateFringe(col,p);
    float time=phase*2.*pi;
    float finger=ellipse(p,vec2(.213,.267),vec2(.057,.095));
    float sparkle=.44+.35*sin(2.*time-.4)+.13*sin(3.*time+1.);
    col+=finger*vec3(.040,.028,.012)*sparkle;
    float water=ellipse(p,vec2(.948,.319),vec2(.077,.179))+ellipse(p,vec2(.81,.756),vec2(.047,.097));
    col+=water*vec3(.003,.010,.014)*sin(3.*time+p.x*52.+p.y*43.);
    col=sapphire(waterLight(ribbon(col,p),p,time),p,time);
    if(person.a<.99995)col=mix(focusWater(uv),col,person.a);
    col=closeGlints(drawHand(p,uv,fragments(col,p)),uv,p);
    vec2 fx=(p*size-vec2(1500,180))/vec2(800,680);
    if(all(greaterThan(fx,vec2(0)))&&all(lessThan(fx,vec2(1)))){
        vec4 spark=texture(dust,fx);col=mix(col,spark.rgb,spark.a);
    }
    overlay(col,0,uv,mat2(1.,-.39,-.08,1.),vec2(349,62));
    overlay(col,1,uv,mat2(1.,.429,-.14,1.),vec2(19,694));
    overlay(col,2,uv,mat2(.81,-.69,.62,.73),vec2(1417,648));
    overlay(col,3,uv,mat2(1.,.45,-.91,.63),vec2(1321,778));
    frag=vec4(col,hudFocus);
    handOut=handCoverage;
}
