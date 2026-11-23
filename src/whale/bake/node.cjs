const fs = require('node:fs');
const path = require('node:path');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const { drawParticles } = require('./particles.cjs');
const { writeHeadingsAndLogs, writePanel } = require('./hud.cjs');

const [group, output] = process.argv.slice(2);
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));

if (group === 'hud') {
  const fontDirectory = process.env.WHALE_FONT_DIR;
  const drawText = !payload.changed || payload.changed.length > 0;
  if (fontDirectory && drawText) {
    for (const [filename, family] of [
      ['arialbd.ttf', 'Arial'], ['consola.ttf', 'Consolas'], ['consolab.ttf', 'Consolas'],
    ]) {
      const fontPath = path.join(fontDirectory, filename);
      if (!GlobalFonts.registerFromPath(fontPath, family)) {
        throw new Error('Cannot load font ' + fontPath);
      }
    }
  }
  const target = path.join(output, 'hud');
  fs.mkdirSync(target, { recursive: true });
  writePanel(target);
  if (drawText) writeHeadingsAndLogs(target, payload.panels, payload.changed);
} else if (group === 'particles') {
  const target = path.join(output, 'fx', 'dust');
  fs.mkdirSync(target, { recursive: true });
  const canvas = createCanvas(800, 680);
  const ctx = canvas.getContext('2d');
  for (let frame = 0; frame < payload.frames; frame++) {
    ctx.resetTransform();
    ctx.clearRect(0, 0, 800, 680);
    ctx.translate(-1500, -180);
    drawParticles(ctx, frame * 12 / payload.frames);
    const name = String(frame).padStart(4, '0') + '.png';
    fs.writeFileSync(path.join(target, name), canvas.toBuffer('image/png'));
  }
} else {
  throw new Error('Unknown bake group ' + group);
}
