float thump(float u,float position,float decay){
    float t=u-position;
    return smoothstep(0.,.042,t)*(1.-smoothstep(.05,decay,t));
}
void main(){
    vec2 uv=gl_FragCoord.xy/size;
    bool later=seconds>=11.28;
    float u=later?(seconds-11.28)/1.02:(seconds-3.00)/.95;
    if(u<=0.||u>=1.){
        frag=vec4(finalPrint(develop(uv),uv),1.);return;
    }
    // Two distinct signal faults. Each has an attack, a sustained channel
    // misregistration and a damped reacquisition, with hard-edged packet slips.
    float env=smoothstep(0.,.075,u)*(1.-smoothstep(.78,1.,u));
    float attack=thump(u,later?.17:.055,.28), echo=thump(u,later?.51:.42,.34);
    float amp=env*(.34+.64*attack+.44*echo);
    float polarity=later?-1.:1.;
    float kick=sin(37.*u+(later?.7:.0))*.70+.30*sin(70.*u);
    vec2 shake=amp*vec2(7.2*kick,3.8*sin(41.*u+.55));
    vec2 p=(uv-.5)*(1.-amp*.008)+.5+shake/size;
    float switchAt=step(later?.48:.41,u);
    // Bands sit across the actual ink of a lock, cuff, alert header and shoulder.
    // Their colour is sampled from the displaced image on three discrete scan lines.
    float band1=patch(uv,vec2(later?.69:.53,(later?.357:.311)+.026*switchAt),vec2(.228,.0055));
    float band2=patch(uv,vec2(later?.23:.28,(later?.545:.670)-.037*switchAt),vec2(.176,.0080));
    float band3=patch(uv,vec2(later?.81:.18,(later?.763:.152)+.012*switchAt),vec2(.135,.0043));
    float band4=patch(uv,vec2(later?.57:.74,(later?.601:.445)-.019*switchAt),vec2(.13,.0022));
    float timing=env*(.40+.60*max(attack,echo));
    float slip=polarity*timing*(31.*band1-24.*band2+38.*band3-18.*band4);
    float edge=smoothstep(0.,.016,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));
    p.x+=slip*edge/size.x;
    float layer=max(max(band1,band2),max(band3,band4));
    vec2 chroma=polarity*vec2(15.3+(later?3.8:0.),-3.1)*amp*(1.+.68*layer)*edge/size;
    vec3 red=develop(p+chroma);
    vec3 green=develop(p+vec2(-.10*chroma.x,.43*chroma.y));
    vec3 blue=develop(p-chroma*.87);
    vec3 col=vec3(red.r,green.g,blue.b);
    vec3 weight=vec3(.213,.715,.072);
    float edgeDiff=max(abs(dot(red-green,weight)),abs(dot(blue-green,weight)));
    float chip=timing*layer*smoothstep(.032,.30,edgeDiff);
    vec3 pigment=mix(vec3(.03,.79,.95),vec3(.96,.086,.35),step(0.,dot(red-blue,weight)*polarity));
    if(band4>.5)pigment=vec3(.15,.89,.49);
    col=mix(col,pigment,.46*chip);
    frag=vec4(col,1.);
}
