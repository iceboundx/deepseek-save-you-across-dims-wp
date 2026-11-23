uniform sampler2D hairMatte,faceUnder;
uniform vec2 lockNow[3],lockLate[3];
uniform float hairGain;
const vec2 faceCrop=vec2(1818.,286.);
vec2 lockUV(vec2 p){
    return (p*size-faceCrop)/vec2(textureSize(hairMatte,0));
}
vec2 lockBend(vec2 q){
    float t=phase*2.*pi;
    // Displacement rises along each lock. Root highlights remain anchored.
    float bang=smoothstep(88.,217.,q.y)*smoothstep(493.,540.,q.x)
              *(1.-smoothstep(623.,671.,q.x))*(1.-smoothstep(228.,251.,q.y));
    float left=smoothstep(103.,228.,q.y)*smoothstep(438.,471.,q.x)
              *(1.-smoothstep(497.,528.,q.x))*(1.-smoothstep(239.,252.,q.y));
    float right=smoothstep(177.,266.,q.y)*smoothstep(588.,614.,q.x)
               *(1.-smoothstep(682.,722.,q.x))*(1.-smoothstep(280.,301.,q.y));
    vec2 fringe=mix(lockNow[0],lockLate[0],bang);
    fringe.x+=.72*sin(t-.06*(q.x-551.))+.45*sin(2.*t+.035*q.x);
    vec2 leftLock=mix(lockNow[1],lockLate[1],left);
    leftLock.x+=1.18*sin(t-.052*(q.y-204.));
    vec2 rightLock=mix(lockNow[2],lockLate[2],right);
    rightLock.x+=1.42*sin(t+.5-.038*(q.y-244.));
    return bang*fringe+left*leftLock+right*rightLock;
}
vec3 separateFringe(vec3 scene,vec2 p){
    vec2 q=p*canvasSize;
    if(q.x<435.||q.x>723.||q.y<86.||q.y>302.)return scene;
    vec4 backing=texture(faceUnder,lockUV(p));
    vec2 difference=lockBend(q)*(hairGain*backing.a);
    float amount=length(difference);
    if(amount<.016)return scene;
    vec2 moving=p-difference/canvasSize;
    vec2 a=texture(hairMatte,lockUV(p)).rg,b=texture(hairMatte,lockUV(moving)).rg;
    if(max(a.y,b.y)<.002)return scene;
    // If both points are hair, the moving pigment fully covers this pixel.
    float influence=backing.a*smoothstep(.016,.20,amount);
    if(b.x>.996)return mix(scene,texture(art,moving).rgb,influence);
    vec3 under=scene;
    if(a.y>.001)under=mix(under,backing.rgb,a.y);
    if(b.y>.001){
        vec3 paint=texture(art,moving).rgb;
        vec3 residual=paint-texture(faceUnder,lockUV(moving)).rgb;
        under=mix(under,paint,b.x)+(1.-b.x)*b.y*residual;
    }
    return mix(scene,under,influence);
}

vec3 animateFringe(vec3 scene,vec2 p){
    vec2 q=p*canvasSize;
    float cheek=smoothstep(578.,599.,q.x)*smoothstep(233.,253.,q.y);
    float collar=(1.-smoothstep(502.,522.,q.x))*smoothstep(215.,234.,q.y);
    float junction=max(cheek,collar);
    if(junction<.001 || q.x<435. || q.x>723. || q.y>302.)
        return separateFringe(scene,p);

    // At these junctions the backing is another lock. Carry both painted
    // edges through a shared continuous bend, including their original ink.
    float guard=texture(faceUnder,lockUV(p)).a;
    vec2 excursion=lockBend(q)*hairGain*guard;
    vec3 original=texture(art,p).rgb;
    vec3 bent=texture(art,p-excursion/canvasSize).rgb;
    vec3 joined=clamp(scene+guard*(bent-original),0.,1.);
    if(junction>.999)return joined;
    return mix(separateFringe(scene,p),joined,junction);
}
