float gauss2(vec2 at,vec2 centre,vec2 radius){
    vec2 n=(at-centre)/radius;return exp(-dot(n,n)*1.75);
}
vec3 waterLight(vec3 col,vec2 p,float t){
    vec2 q=p*vec2(1254.,706.);
    // The body coordinates and the material sampling both follow the artwork.
    float collar=gauss2(q,vec2(730.,489.),vec2(90.,75.));
    float silk=gauss2(q,vec2(726.,614.),vec2(118.,145.));
    float coat=gauss2(q,vec2(607.,592.),vec2(112.,127.));
    float fabric=min(1.,collar+.84*silk+.47*coat)*smoothstep(432.,458.,q.y);
    float scene=min(1.,gauss2(q,vec2(729.,90.),vec2(230.,104.))
                        +.82*gauss2(q,vec2(982.,476.),vec2(155.,210.))
                        +.74*gauss2(q,vec2(403.,458.),vec2(159.,133.))
                        +.84*gauss2(q,vec2(458.,169.),vec2(176.,109.))
                        +gauss2(q,vec2(1190.,263.),vec2(126.,290.))
                        +.78*gauss2(q,vec2(1040.,631.),vec2(236.,106.)));
    float skin=smoothstep(-.01,.095,col.r-col.b)*smoothstep(.015,.15,col.r-col.g);
    float keepSkin=1.-.94*skin;
    float face=gauss2(q,vec2(787.,313.),vec2(143.,102.));
    scene*=keepSkin*(1.-.93*face);
    fabric*=keepSkin;
    float cycle=.68+.21*sin(t-.37)+.11*sin(2.*t-.82);
    float path=.52*q.x+.83*q.y+12.*sin(q.x*.025+t)+7.*sin(q.y*.030-t);
    float wave=cos(path*.069+t);
    float broad=pow(max(wave,0.),4.);
    float crest=pow(max(wave,0.),19.);
    float broken=.23+.77*smoothstep(-.65,.55,sin(q.x*.038-q.y*.019+t));
    vec3 luma=vec3(.2126,.7152,.0722);
    float Y=dot(col,luma);
    float local=dot(texture(art,p+vec2(3.5,-4.)/size).rgb,luma);
    float ridge=smoothstep(.018,.14,Y-local);
    float satin=smoothstep(.18,.72,Y);
    // Mirror the blue bounce on dark satin, with a narrower cyan crest on the lit folds.
    float fill=fabric*(.36+.27*cycle)+scene*(.035+.04*cycle);
    float fleck=broken*(broad*.20+crest*(.27+.39*satin)) + ridge*(.22+.18*broad);
    float reflection=(.86*fabric+.58*scene)*fleck;
    vec3 tint=vec3(.012,.25,.65)*fill+vec3(.055,.42,.68)*reflection;
    col+=(vec3(1.)-col)*tint;
    col.r*=1.-min(.12,fabric*(.035+.035*cycle+.035*broad));
    // The sapphire is the bright source. Bloom is localized to the bow around it.
    vec2 d=q-vec2(730.2,479.3);
    vec2 oriented=vec2(d.x+.16*d.y,d.y);
    float stone=1.-smoothstep(.55,1.08,dot(oriented/vec2(9.4,16.),oriented/vec2(9.4,16.)));
    float spill=gauss2(q,vec2(730.,481.),vec2(32.,29.));
    float down=gauss2(q,vec2(741.,503.),vec2(49.,40.));
    float line=oriented.x+.33*d.y-6.*sin(t-.3);
    float reflectionBand=exp(-.23*line*line);
    col+=(1.-col)*(vec3(.04,.62,1.)*stone*(.37+.48*reflectionBand)*(.7+.3*cycle)
                  +vec3(.014,.32,.75)*(spill*.65+down*.20)*(.69+.31*cycle));
    return col;
}
