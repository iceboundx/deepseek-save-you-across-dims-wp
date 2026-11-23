uniform sampler2D silk;

float satinRoot(vec2 v){return smoothstep(16.,168.,length(v-vec2(226.,147.)));}
vec2 ribbonSource(vec2 local){
    float clock=phase*2.*pi;
    float lengthwise=clamp((local.y-170.)/341.,0.,1.);
    float tail=smoothstep(200.,294.,local.y)*(1.-smoothstep(-10.,50.,local.x-.72*local.y-151.));
    float wave=sin(clock-.4-1.22*lengthwise)+.26*sin(2.*clock+.8-1.05*lengthwise);
    float wing=sin(clock+.14)+.25*sin(2.*clock+1.1);
    vec2 relative=local-vec2(227.,153.);
    float turn=satinRoot(local)*mix(.016*wing,.043*wave,tail);
    float c=cos(turn),s=sin(turn);
    return vec2(227.,153.)+mat2(c,s,-s,c)*relative-vec2(1.1,1.4)*lengthwise*wave;
}
vec3 ribbon(vec3 cloth,vec2 p){
    vec2 local=p*size-vec2(2010.,1325.);
    if(local.x<3.||local.x>520.||local.y<40.||local.y>544.)return cloth;
    vec2 dims=vec2(525.,550.);
    vec2 q=ribbonSource(local);
    vec4 clothInk=texture(silk,q/dims);
    float shadow=texture(silk,ribbonSource(local-vec2(2.,8.))/dims).a;
    vec3 behind=cloth*(1.-.16*shadow);
    return mix(behind,clothInk.rgb,clothInk.a);
}
