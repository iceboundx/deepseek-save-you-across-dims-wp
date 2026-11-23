// Play back the four panels along independent entry, print and exit cues.
float ellipse(vec2 p,vec2 c,vec2 r) {vec2 q=(p-c)/r;return 1.-smoothstep(.62,1.,dot(q,q));}
int whichPanel(vec2 s){
    if(s.y<315.&&s.x<700.)return 0;
    if(s.x<510.&&s.y>593.)return 1;
    if(s.x>=1320.&&s.y<750.+(s.x-1357.)*.39)return 2;
    return 3;
}
// The signed displacement is sampled on video frames. Visibility is strictly on/off.
float travel(float t){
    const float stepPos[8]=float[8](0.,.055,.19,.43,.69,.88,.97,1.);
    float m=clamp(t,0.,1.)*7.;int k=min(int(m),6);
    return mix(stepPos[k],stepPos[k+1],m-float(k));
}
float hudFocus=0.;
void overlay(inout vec3 col,int i,vec2 uv,mat2 basis,vec2 origin){
    int f=int(floor(phase*408.+.1));
    bool second=f>=204;
    ivec4 enter=second?ivec4(218,227,208,237):ivec4(6,25,12,28);
    ivec4 seat=second?ivec4(227,237,219,245):ivec4(15,36,25,39);
    ivec4 printAt=second?ivec4(233,243,225,250):ivec4(23,41,32,45);
    ivec4 clearAt=second?ivec4(384,363,386,377):ivec4(165,152,158,148);
    ivec4 eject=second?ivec4(396,377,398,388):ivec4(184,167,177,165);
    ivec4 done=second?ivec4(405,389,407,399):ivec4(194,178,187,177);
    if(f<enter[i]||f>=done[i])return;
    vec2 from=i==0?vec2(-.035,-.31):i==1?vec2(-.295,.10):i==2?vec2(.256,-.035):vec2(.044,.31);
    vec2 to=i==0?vec2(.045,-.32):i==1?vec2(-.045,.37):i==2?vec2(.248,.10):vec2(.30,.22);
    if(second && i==1){from=vec2(-.055,.36);to=vec2(-.29,.12);}
    if(second && i==3){from=vec2(.28,.22);to=vec2(.025,.31);}
    float arrival=travel((phase*408.-float(enter[i]))/float(seat[i]-enter[i]));
    float departure=travel((phase*408.-float(eject[i]))/float(done[i]-eject[i]));
    vec2 disp=from*(1.-arrival)+to*departure;
    vec2 uvP=uv-disp;
    if(any(lessThan(uvP,vec2(0)))||any(greaterThan(uvP,vec2(1))))return;
    vec2 s=uvP*design;if(whichPanel(s)!=i)return;
    vec4 pane=texture(panel,uvP);if(pane.a<.001)return;
    vec3 base=pane.rgb;
    vec2 pt=inverse(basis)*(s-origin);
    if(i==2)pt.y-=4.;
    if(i==1){
            float titleBand=1.-smoothstep(28.,111.,abs(pt.y-4.));
            hudFocus=max(hudFocus,pane.a*titleBand*smoothstep(-14.,55.,pt.x));
        }
        bool extraTab=i==0&&s.x<328.&&s.y>164.;
    bool triangle=i==2&&pane.r>1.25*pane.g;
    if(pt.y>9.&&!extraTab&&!triangle){
        vec2 pad=vec2(5.)/design;
        float inner=min(min(texture(panel,uvP+vec2(pad.x,0)).a,texture(panel,uvP-vec2(pad.x,0)).a),
                        min(texture(panel,uvP+vec2(0,pad.y)).a,texture(panel,uvP-vec2(0,pad.y)).a));
        int age=f-printAt[i];
        int stepRate=second?(16+2*i):(21+2*i);
        int positiveAge=max(age,0),cycle=positiveAge/stepRate,sub=positiveAge%stepRate;
        // Three packets land on separate frames, followed by time to read them.
        int offset=cycle*3+(sub>=stepRate-5?1:0)+(sub>=stepRate-2?1:0);
        float rowPos=(pt.y-12.)*2.30/26.;
        int row=max(0,int(floor(rowPos)));
        int group=int(floor(mod(pt.x+780.,160.)/54.));
        bool printed=age>=(row/2)+(row%3==1?1:0)+group;
        bool cleared=f>=clearAt[i]+row/3+(group==2?1:0);
        vec2 tile=fract(vec2(pt.x*2.30/1536.,(rowPos+float(offset+(second?17:0)+3*i))/32.));
        vec2 atlas=(tile+vec2(i%2,i/2))*.5;
        vec4 ink=texture(logAtlas,atlas);
        float inset=step(.90,inner)*step(11.,pt.y);
        if(printed&&!cleared){
            bool newPacket=sub>=stepRate-5 && row%5==cycle%5;
            vec3 typeColor=newPacket?mix(ink.rgb,vec3(.92,1.,1.),.29):ink.rgb;
            base=mix(base,typeColor,ink.a*inset);
        }
    }
    int titleAge=f-(printAt[i]+1);
    bool headerOn=titleAge>=0 && f<clearAt[i]+2;
    if(i==1 && (titleAge==3||titleAge==4||titleAge==36||titleAge==37))headerOn=false;
    if(headerOn){
        vec4 title=texture(headings,uvP);
        base=mix(base,title.rgb,title.a);
    }
    handCoverage*=1.-pane.a;
    col=mix(col,base,pane.a);
}
