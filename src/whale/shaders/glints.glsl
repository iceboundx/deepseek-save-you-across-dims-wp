vec3 closeGlints(vec3 col,vec2 uv,vec2 p){
    float t=phase*2.*pi;
    vec2 q=(uv.x<.18?p:uv)*canvasSize;
    vec2 center=uv.x<.18?vec2(53.,327.):vec2(782.,446.);
    vec2 d=q-center;
    if(max(abs(d.x),abs(d.y))>13.)return col;
    float phi=(uv.x<.18?1.8:.3)+.60*sin(2.*t-.4);
    vec2 v=d-(uv.x<.18?8.7:6.4)*vec2(cos(phi),sin(phi));
    float dotLight=exp(-dot(v,v)/2.1);
    col+=(1.-col)*dotLight*vec3(.37,.56,.69)*(.66+.34*cos(t+phi));
    return col;
}
