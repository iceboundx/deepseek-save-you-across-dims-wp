// Two painted emissions follow independent optical paths over the sea.
uniform sampler2D optics;
vec4 opticalPlate(vec2 q){
    return texture(optics,(q*size/canvasSize)/vec2(textureSize(optics,0)));
}
vec3 mobileOptics(vec3 base,vec2 q,float t){
    if(q.x>280.||q.y>217.)return base;
    bool disc=q.x<148.&&q.y<101.;
    vec2 centre=disc?vec2(35.,8.):vec2(193.9,134.);
    vec2 d=q-centre;
    if(!disc&&length(d)>74.)return base;
    float swell=.5+.5*sin(2.*t-.8+.53*sin(t+.5));
    float bend=sin(2.*t-.95+.40*sin(t+.9));
    vec2 travel=disc?vec2(15.*bend+4.*sin(t+.5),8.5*sin(2.*t-.23)):
                     vec2(7.8*bend+1.6*sin(t+.34),4.8*sin(2.*t-.5));
    vec2 stretch=disc?vec2(.86+.30*swell,.88+.28*swell):
                      vec2(.79+.46*swell,1.07-.19*swell);
    float roll=disc?.039*sin(t+.4):.155*bend;
    float cs=cos(roll),sn=sin(roll);
    vec2 sampleAt=centre+mat2(cs,-sn,sn,cs)*(d-travel)/stretch;
    // On the star plate, prevent samples from the corner ghost on the far side.
    vec4 rest=opticalPlate(q),moving=opticalPlate(sampleAt);
    float feather=disc?(1.-smoothstep(126.,148.,q.x))*(1.-smoothstep(86.,101.,q.y)):
                         (1.-smoothstep(55.,73.,length(d)));
    float gain=disc?(.71+.38*swell):(.83+.24*swell);
    vec3 delta=feather*rest.a*(moving.rgb*gain-rest.rgb);
    if(disc){
        base+=min(delta,vec3(0.))*smoothstep(vec3(.02),vec3(.62),base)
            +(1.-base)*(1.-exp(-2.2*max(vec3(0.),delta)));
    }else base+=delta;
    if(disc){
        vec2 s=(d-travel)/stretch;
        float ring=length(vec2(s.x*.90+.19*s.y,s.y));
        float arc=exp(-pow((ring-63.)/2.35,2.))*(.22+.78*swell);
        base+=(1.-base)*vec3(.23,.095,.15)*arc*rest.a*feather;
    }else{
        vec2 s=d-travel;
        float beam=lineFlare(s,vec2(.94,-.27+.13*bend),11.+41.*swell,.70)
                 +.65*lineFlare(s,vec2(.52+.11*bend,.86),10.+24.*swell,.58);
        base+=(1.-base)*vec3(.95,.78,.48)*beam*(.42+.49*swell)*feather;
    }
    return clamp(base,0.,1.);
}
