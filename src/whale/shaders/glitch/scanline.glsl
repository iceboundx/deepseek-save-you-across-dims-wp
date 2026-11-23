// A rapid attack and a steep first release. The remaining colour separation
// catches up on the following scan lines, without a second camera kick.
float impulse(float f,float peak,float end,float fall){
    if(f<=0.||f>=end)return 0.;
    if(f<=peak)return smoothstep(0.,peak,f);
    float u=(f-peak)/(end-peak);
    return exp(-fall*u)*(1.-smoothstep(.61,1.,u));
}

void main(){
    vec2 uv=gl_FragCoord.xy/size;
    bool later=seconds>=11.28;
    float f=seconds*60.-(later?677.:180.);
    float end=later?15.:13.;
    if(f<=.001||f>=end){frag=vec4(finalPrint(develop(uv),uv),1.);return;}
    float hit=impulse(f,later?1.:1.65,later?9.5:8.,3.65);
    float rowLag=mix(.08,1.12,later?uv.y:1.-uv.y);
    float stripHit=impulse(f-rowLag,later?1.2:1.65,end-rowLag-1.,3.1);
    float fringe=impulse(f-.40,1.85,end-.40,3.05);
    float polarity=later?-1.:1.;
    vec2 travel=polarity*vec2(later?42.:36.,later?-10.:8.)*hit;
    vec2 p=(uv-.5)*(1.-.025*hit)+.5+travel/size;
    // The line tear breaks into coarse and fine scan lines, staggered vertically.
    float b1=patch(uv,vec2(later?.69:.53,later?.357:.311),vec2(.218,.0059));
    float b2=patch(uv,vec2(later?.23:.28,later?.545:.670),vec2(.154,.0079));
    float b3=patch(uv,vec2(later?.81:.18,later?.763:.152),vec2(.118,.0042));
    float b4=patch(uv,vec2(later?.57:.74,later?.601:.445),vec2(.121,.0020));
    float line=mod(floor(uv.y*2160.),8.);
    float teeth=mix(.64,1.,step(1.5,line));
    float edge=smoothstep(0.,.025,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));
    float shear=(uv.y-.5)*9.*hit;
    p.x+=polarity*edge*(stripHit*teeth*(74.*b1-54.*b2+76.*b3-37.*b4)+shear)/size.x;
    float strip=max(max(b1,b2),max(b3,b4));
    vec2 chroma=polarity*vec2(later?28.:25.,-2.6)*edge*
                    (fringe+1.02*stripHit*strip*teeth)/size;
    vec3 red=develop(p+chroma),green=develop(p+vec2(-.06*chroma.x,.26*chroma.y)),blue=develop(p-chroma*.80);
    vec3 col=vec3(red.r,green.g,blue.b),w=vec3(.213,.715,.072);
    float contrast=max(abs(dot(red-green,w)),abs(dot(blue-green,w)));
    vec3 pigment=mix(vec3(.03,.77,.94),vec3(.91,.095,.38),step(0.,dot(red-blue,w)*polarity));
    col=mix(col,pigment,.49*stripHit*strip*smoothstep(.035,.32,contrast));
    frag=vec4(col,1.);
}
