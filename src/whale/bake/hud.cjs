const fs = require('node:fs');
const path = require('node:path');
const { createCanvas } = require('@napi-rs/canvas');

function tracePolygon(context, points) {
  context.beginPath();
  for (const [index, [x, y]] of points.entries()) {
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  context.closePath();
}

function writeHeadingsAndLogs(targetDir, panels, changed) {
  const layout = [
    { size: 18, mat: [1, -.39, -.08, 1], origin: [349, 62] },
    { size: 30, mat: [1, .429, -.14, 1], origin: [19, 694] },
    { size: 17, mat: [.81, -.69, .62, .73], origin: [1417, 648] },
    { size: 16, mat: [1, .45, -.91, .63], origin: [1321, 778] },
  ];
  const W=1536,H=832,rowH=26,atlas=createCanvas(W*2,H*2),g=atlas.getContext('2d');
  const headings=createCanvas(3840,2160),hh=headings.getContext('2d');
  const polygons=[[[339,39],[503,-22],[563,-9],[656,62],[654,73],[332,224],[320,223]],[[-50,623],[397,820],[415,864],[367,992],[-55,1001]],[[1397,647],[1659,415],[1732,425],[1745,689],[1571,751],[1468,716],[1366,755],[1357,750],[1435,673],[1398,659]],[[949,992],[1323,749],[1408,786],[1421,780],[1745,921],[1770,1035],[968,1034]]];
  const mask = changed ? createCanvas(3840, 2160) : null;
  const area = mask?.getContext('2d');
  area?.scale(3840 / 1672, 2160 / 941);
  panels.forEach((copy, n) => {
    if (changed && !changed.includes(n)) return;
    if (area) {
      tracePolygon(area, polygons[n]);
      area.fill();
      // Cover the antialias fringe on the edge of the reference polygon.
      area.stroke();
    }
    const p = { ...layout[n], ...copy };
    const xoff=n%2*W,yoff=Math.floor(n/2)*H;
    g.save();g.translate(xoff,yoff);
    for(let line=0;line<32;line++){
      const y=(line+.77)*rowH;
      for(let col=0;col<2;col++){
        const val=line+col*37+n*71, j=(line*11+col*7+n)%p.records.length;
        const alert=(line+n+col)%5===0;
        const x=col*(W/2);
        g.font='19px Consolas';
        g.fillStyle=alert?'#ff9d70':'#80d2dc';g.fillText((val%256).toString(16).toUpperCase().padStart(2,'0')+'F',x+4,y);
        g.fillStyle=alert?'#ff8258':'#59d4e0';g.fillText(p.type+'-'+String((137+val*7)%1000).padStart(3,'0'),x+52,y);
        g.fillStyle=alert?'#ffe0bd':'#b8e3e7';g.fillText(p.records[j],x+149,y);
        g.fillStyle='#76bac8';g.fillText('0x'+(0x20b1+val*231).toString(16).toUpperCase().slice(-4),x+344,y);
        g.fillStyle=alert?'#ffa071':'#8ed6df';g.fillText(['WAIT','HOLD','DRIFT','RETRY','TRACE','LOW'][j],x+439,y);
        g.fillStyle='#62aebc';g.fillText('CH.'+String(3+(val%13)).padStart(2,'0'),x+534,y);
        g.fillStyle='#94d6dc';g.fillText('dT '+String((47+val*13)%997).padStart(3,'0'),x+628,y);
      }
    }
    g.restore();
    hh.save();hh.scale(3840/1672,2160/941);
    tracePolygon(hh, polygons[n]);
    hh.clip();
    hh.transform(...p.mat,...p.origin);
    const mark=n === 2;
    const typeStart=mark?23:0;
    if(mark){
      // Draw the stem and dot in the same plane as the outline and title.
      hh.translate(2.5,4);
      hh.save();hh.translate(1,0);
      hh.beginPath();hh.moveTo(8,-15.1);hh.lineTo(16.1,-.6);hh.lineTo(-.1,-.6);hh.closePath();
      hh.lineJoin='round';hh.lineWidth=1.75;hh.strokeStyle='#ff9866';hh.stroke();
      hh.fillStyle='#ffb47d';hh.beginPath();hh.moveTo(6.97,-10.3);hh.lineTo(9.03,-10.3);
      hh.lineTo(8.68,-5.5);hh.lineTo(7.32,-5.5);hh.closePath();hh.fill();
      hh.beginPath();hh.arc(8,-3.55,1.06,0,Math.PI*2);hh.fill();hh.restore();
    }
    hh.font='bold '+p.size+'px Arial';hh.fillStyle=n===0?'#7cf5f6':'#ff8554';hh.fillText(p.heading,typeStart,0);
    const len=typeStart+hh.measureText(p.heading).width;
    hh.font='bold 9px Consolas';hh.fillStyle='#e4c7b7';hh.fillText(p.side,len+11,-1);
    hh.fillStyle='#4d9dad';hh.fillRect(-5,5,480,.8);
    hh.restore();
  });
  if (mask) {
    fs.writeFileSync(path.join(targetDir, 'headings-mask.png'), mask.toBuffer('image/png'));
  } else {
    hh.save();hh.scale(3840/1672,2160/941);
    hh.font='bold 11px Consolas';hh.fillStyle='#ff9b73';hh.fillText('E-07',228,223);
    hh.font='8.5px Consolas';hh.fillStyle='#b7e9ed';hh.fillText('LINK  LOST',215,237);
    hh.restore();
  }
  fs.writeFileSync(path.join(targetDir, 'logs.png'),atlas.toBuffer('image/png'));
  fs.writeFileSync(path.join(targetDir, 'headings.png'),headings.toBuffer('image/png'));
}

function writePanel(targetDir) {
  const canvas=createCanvas(3840,2160),g=canvas.getContext('2d');
  g.scale(3840/1672,2160/941);
  function face(points,width){
    g.beginPath();points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();
    g.fillStyle='#0d2c42';g.fill();g.lineJoin='bevel';g.lineWidth=width;g.strokeStyle='#20e5ef';g.stroke();
  }
  face([[339,39],[503,-22],[563,-9],[656,62],[654,73],[332,224],[320,223]],4);
  face([[175,260],[255,178],[327,248],[307,266],[180,265]],2.6);
  face([[-50,623],[397,820],[415,864],[367,992],[-55,1001]],5.2);
  face([[1397,647],[1659,415],[1732,425],[1745,689],[1571,751],[1468,716],[1366,755],[1357,750],[1435,673],[1398,659]],3.5);
  face([[949,992],[1323,749],[1408,786],[1421,780],[1745,921],[1770,1035],[968,1034]],4.1);
  for(let i=0;i<3;i++){g.fillStyle=i===2?'#f47b4d':'#58cbd7';g.fillRect(208+i*23,244,15,2.7);}
  fs.writeFileSync(path.join(targetDir, 'panel.png'), canvas.toBuffer('image/png'));
}

module.exports = { writeHeadingsAndLogs, writePanel };
