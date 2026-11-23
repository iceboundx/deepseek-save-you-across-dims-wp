float patch(vec2 p,vec2 center,vec2 halfSize){
    vec2 e=halfSize-abs(p-center);
    return smoothstep(-.00035,.0004,min(e.x,e.y));
}
