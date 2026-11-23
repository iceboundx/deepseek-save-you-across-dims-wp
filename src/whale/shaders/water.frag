#version 330
uniform sampler2D ocean;
uniform float phase;
const vec2 size=vec2(3840.,2160.);
const float pi=3.14159265358979;
out vec4 frag;
uniform sampler2D bubbleInk;
const vec2 canvasSize=vec2(900.,506.25);

float lineFlare(vec2 p,vec2 axis,float lengthRay,float widthRay){
    vec2 normAxis=normalize(axis);
    float u=dot(p,normAxis),v=dot(p,vec2(-normAxis.y,normAxis.x));
    return exp(-abs(v)/widthRay-abs(u)/lengthRay);
}
#include "optics.glsl"

vec3 seaColour(vec2 uv,float t){
    vec3 base=texture(ocean,uv).rgb;
    vec2 q=uv*canvasSize;
    float lumen=dot(base,vec3(.2126,.7152,.0722));
    float sea=smoothstep(.015,.29,base.b-base.r);
    // Light travels along the paint. Coordinates of every drawn water line remain fixed.
    float wave=.52+.27*sin(q.x*.024+q.y*.039-2.*t)+.21*sin(q.x*.043-q.y*.016-t+.6);
    float shafts=q.x+.48*q.y+7.*sin(q.y*.018-t);
    float broad=.5+.5*cos(shafts*.039-t);
    float light=pow(broad,3.)*(.35+.65*wave);
    float caustic=smoothstep(.40,.89,lumen)*pow(wave,2.);
    base*=1.-(.020+.025*(1.-wave))*sea;
    base+=(1.-base)*sea*(vec3(.005,.092,.15)*light+vec3(.09,.17,.19)*caustic);
    return mobileOptics(base,q,t);
}
// Distinct one-way paths go from below the frame to above it, or through an occluding lock.
// The two endpoints of each path are either offscreen or fully occluded.
void oneBubble(inout vec3 col,vec2 q,float t,vec4 route,vec4 brush){
    float life=fract(phase+route.w);
    float clock=life*2.*pi;
    float y=mix(route.y,route.z,life);
    float x=route.x+brush.z*sin(clock+brush.w)+brush.z*.33*sin(2.*clock+brush.w*.47);
    vec2 radii=brush.x*vec2(1.+.026*sin(2.*clock+brush.w),1.085-.023*sin(2.*clock+brush.w));
    vec2 delta=(q-vec2(x,y))/radii;
    if(any(greaterThan(abs(delta),vec2(1.145))))return;
    vec2 tile=(delta*.425+.5);
    vec3 ink=texture(bubbleInk,vec2((tile.x+brush.y)/3.,tile.y)).rgb;
    float disc=ink.b;
    if(disc<.001)return;
    float depth=sqrt(max(.01,1.-min(1.,dot(delta,delta))));
    vec2 under=(q-delta*(.40+.90*depth))/canvasSize;
    col+=disc*.50*(texture(ocean,under).rgb-texture(ocean,q/canvasSize).rgb);
    col*=1.-ink.g*.80;
    float glint=.85+.14*sin(2.*clock+brush.w)+.035*sin(t+q.y*.08);
    col=mix(col,vec3(.90,.979,1.),min(1.,ink.r*glint));
}
vec3 animateWater(vec2 uv){
    float t=2.*pi*phase;
    vec2 q=uv*canvasSize;
    vec3 col=seaColour(uv,t);
    if(q.x>675.){
        oneBubble(col,q,t,vec4(836.,529.,-22.,.79),vec4(6.6,0.,11.,.26));
        oneBubble(col,q,t,vec4(855.,535.,-26.,.58),vec4(10.8,2.,10.,1.8));
        oneBubble(col,q,t,vec4(845.,528.,-17.,.84),vec4(4.7,1.,9.,.8));
        oneBubble(col,q,t,vec4(794.,528.,-19.,.22),vec4(4.1,2.,13.,3.1));
        oneBubble(col,q,t,vec4(875.,529.,-16.,.39),vec4(3.2,0.,8.,4.7));
        oneBubble(col,q,t,vec4(813.,532.,-12.,.045),vec4(2.5,1.,17.,3.9));
        oneBubble(col,q,t,vec4(731.,534.,-24.,.36),vec4(8.0,0.,12.,1.1));
        oneBubble(col,q,t,vec4(864.,530.,-22.,.89),vec4(6.0,1.,8.,2.1));
    }else if(q.x<180.){
        oneBubble(col,q,t,vec4(40.,525.,-12.,.37),vec4(3.5,1.,8.,.7));
        oneBubble(col,q,t,vec4(140.,525.,-12.,.62),vec4(2.6,0.,10.,2.6));
    }
    return col;
}

void main(){frag=vec4(animateWater(gl_FragCoord.xy/size),1.);}
