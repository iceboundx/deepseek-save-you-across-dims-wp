void main(){
    vec2 uv=gl_FragCoord.xy/size;
    bool later=seconds>=11.28;
    float u=later?(seconds-11.28)/1.02:(seconds-3.00)/.95;
    if(u<=0.||u>=1.){frag=vec4(finalPrint(develop(uv),uv),1.);return;}
    // One displacement for each event, with a single attack, a held offset
    // and a monotone release. Scan strips stay on their original rows.
    float hit=smoothstep(0.,.074,u)*(1.-smoothstep(.117,.91,u));
    float fringe=smoothstep(0.,.074,u)*(1.-smoothstep(.16,1.,u));
    float polarity=later?-1.:1.;
    vec2 travel=polarity*vec2(later?32.:28.,later?-8.5:7.)*hit;
    vec2 p=(uv-.5)*(1.-.020*hit)+.5+travel/size;
    float b1=patch(uv,vec2(later?.69:.53,later?.357:.311),vec2(.228,.0062));
    float b2=patch(uv,vec2(later?.23:.28,later?.545:.670),vec2(.176,.0084));
    float b3=patch(uv,vec2(later?.81:.18,later?.763:.152),vec2(.135,.0046));
    float b4=patch(uv,vec2(later?.57:.74,later?.601:.445),vec2(.130,.0025));
    float edge=smoothstep(0.,.021,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));
    p.x+=polarity*hit*edge*(55.*b1-43.*b2+63.*b3-33.*b4)/size.x;
    float strip=max(max(b1,b2),max(b3,b4));
    vec2 chroma=polarity*vec2(later?25.:22.,-3.7)*fringe*(1.+.64*strip)*edge/size;
    vec3 red=develop(p+chroma),green=develop(p+vec2(-.10*chroma.x,.43*chroma.y)),blue=develop(p-chroma*.87);
    vec3 col=vec3(red.r,green.g,blue.b),w=vec3(.213,.715,.072);
    float contrast=max(abs(dot(red-green,w)),abs(dot(blue-green,w)));
    vec3 pigment=mix(vec3(.03,.79,.95),vec3(.96,.086,.35),step(0.,dot(red-blue,w)*polarity));
    if(b4>.5)pigment=vec3(.15,.89,.49);
    col=mix(col,pigment,.53*hit*strip*smoothstep(.032,.30,contrast));
    frag=vec4(col,1.);
}
