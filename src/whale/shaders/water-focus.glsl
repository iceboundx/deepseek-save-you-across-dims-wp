uniform sampler2D waterPlane;
uniform float depthAmount;
vec3 focusWater(vec2 uv){
    // Circle of confusion in master pixels. No character, eyelid, fingertip or HUD
    // is present on this plate, even beneath a subpixel silhouette edge.
    vec2 q=uv*vec2(900.,506.25);
    float distant=smoothstep(605.,895.,q.x);
    float farFloor=smoothstep(305.,499.,q.y);
    float surface=1.-smoothstep(28.,245.,q.y);
    float radius=5.8+4.3*distant+1.8*farFloor+.6*surface;
    vec2 v=(q-vec2(194.,134.))/vec2(49.,45.);
    radius=mix(radius,1.25,exp(-dot(v,v)));
    radius*=depthAmount*mix(.40,1.46,lensPull(phase*13.6));
    vec3 sum=texture(waterPlane,uv).rgb*.13;
    for(int i=0;i<7;i++){
        float angle=float(i)*.897598;
        sum+=.058*texture(waterPlane,uv+vec2(cos(angle),sin(angle))*radius*.42/size).rgb;
    }
    for(int i=0;i<13;i++){
        float angle=float(i)*.483322+.225;
        sum+=(.464/13.)*texture(waterPlane,uv+vec2(cos(angle),sin(angle))*radius*.86/size).rgb;
    }
    // Retain a little air in the upper water, let the distant lower corner recede.
    float cool=smoothstep(.06,.36,sum.b-sum.r);
    return max(vec3(0),sum-vec3(.005,.018,.027)*distant*(.36+.64*farFloor)*cool);
}
