// The subject reaches, the focus releases into the water, then catches the
// second reach. Endpoint value and slope match across the wallpaper loop.
float lensPull(float sec){
#ifdef FIXED_FOCUS
    return .34;
#else
    float towardHand=smoothstep(.28,2.69,sec);
    float throughWater=smoothstep(3.22,6.66,sec);
    float backToEyes=smoothstep(7.40,10.82,sec);
    float settle=smoothstep(11.69,13.48,sec);
    return .34+.62*towardHand-.88*throughWater+.77*backToEyes-.51*settle;
#endif
}
