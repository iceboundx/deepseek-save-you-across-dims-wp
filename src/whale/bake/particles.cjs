let seed=0x3ad7ec11;
function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
const between=(a,b)=>a+(b-a)*random();
const particles=Array.from({length:136},()=>{
  const group=random(), angle=group<.49?between(-2.77,-2.12):group<.72?between(-2.17,-1.6):group<.9?between(-3.08,-2.61):between(-3.45,-2.94);
  return {phase:random(),cycles:Math.floor(between(2,5)),angle,reach:between(185,445),bend:between(-59,57),
    swirl:between(6,30),offset:between(0,Math.PI*2),size:between(5,25)*(random()<.15?1.58:1),
    tilt:between(-.36,.35),spin:between(-.64,.65),depth:between(.69,1),tint:random(),hollow:random()<.11,
    startX:between(-18,14),startY:between(-23,20)};
});
function drawParticles(g,seconds){
  const cycle=((seconds%12)+12)%12/12;
  g.save();g.translate(2112,720);
  const glow=g.createRadialGradient(0,0,1,-11,-5,86);
  glow.addColorStop(0,'rgba(170,255,255,.84)');glow.addColorStop(.16,'rgba(34,240,255,.56)');
  glow.addColorStop(.53,'rgba(0,194,255,.17)');glow.addColorStop(1,'rgba(0,112,255,0)');
  g.fillStyle=glow;g.fillRect(-100,-96,192,192);
  for(const p of particles){
    const t=(p.phase+cycle*p.cycles)%1, progress=t*(1.56-.56*t);
    const travel=p.reach*progress,angle=p.angle+p.bend/p.reach*t;
    const curl=p.swirl*Math.sin(t*5+p.offset)*t;
    const x=p.startX+Math.cos(angle)*travel-Math.sin(angle)*curl;
    const y=p.startY+Math.sin(angle)*travel+Math.cos(angle)*curl;
    const size=Math.max(1.4,p.size*(1-.7*t));
    const alpha=Math.min(1,t/.08,(1-t)/.23)*p.depth;
    const tint=p.tint-.31*(1-t);
    const color=t<.14&&tint<.42?'#c2ffff':tint<.28?'#36f8fb':tint<.60?'#00d7ff':tint<.80?'#329eff':'#627fff';
    g.save();g.translate(x,y);g.rotate(p.tilt+p.spin*t);g.globalAlpha=alpha;g.fillStyle=color;
    if(p.hollow && size>8){g.strokeStyle=color;g.lineWidth=Math.max(1.4,size*.16);g.strokeRect(-size/2,-size/2,size,size);}
    else{
      if(size>14 && t<.62){g.shadowColor=color;g.shadowBlur=3;}
      g.fillRect(-size/2,-size/2,size,size);g.shadowBlur=0;
      if(size>15 && p.tint<.37){g.fillStyle='rgba(209,255,255,.65)';g.fillRect(-size/2,-size/2,size,1.5);}
    }
    g.restore();
  }
  g.restore();
}

module.exports = { drawParticles };
