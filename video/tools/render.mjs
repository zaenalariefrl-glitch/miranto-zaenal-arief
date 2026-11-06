#!/usr/bin/env node
// Deterministic frame renderer: HTML scene -> high-fps MP4 (silent) + cues.json
// Usage: node render.mjs <scene.html> <out_dir> [--fps 60] [--workers 4] [--from 0] [--to <sec>] [--scale 1]
// The scene must define:
//   window.SCENE = { width, height, duration, fps?, cues: [{t, sfx, gain?, pan?, ...params}] }
//   window.seek(tSeconds)  -> sets the visual state for time t (pure function of t, no real timers)
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
if (args.length < 2) { console.error('usage: render.mjs scene.html out_dir [--fps N] [--workers N] [--from s] [--to s] [--scale k]'); process.exit(1); }
const scene = path.resolve(args[0]);
const outDir = path.resolve(args[1]);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? Number(args[i + 1]) : d; };
fs.mkdirSync(outDir, { recursive: true });

const browsers = [];
const launch = async () => { const b = await chromium.launch({ args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-gpu-vsync'] }); browsers.push(b); return b; };

async function openPage(scale) {
  const browser = await launch(); // one browser process per worker = real multi-core rendering
  const probe = await browser.newPage();
  await probe.goto(pathToFileURL(scene).href);
  const meta = await probe.evaluate(() => ({ ...window.SCENE, cues: window.SCENE.cues || [] }));
  await probe.close();
  const ctx = await browser.newContext({ viewport: { width: meta.width, height: meta.height }, deviceScaleFactor: scale });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.error('[scene error]', e.message));
  await page.goto(pathToFileURL(scene).href);
  await page.evaluate(async () => { await document.fonts.ready; if (window.preload) await window.preload(); });
  return { page, meta };
}

const scale = opt('scale', 1);
const FMT = args.includes('--png') ? 'png' : 'jpeg'; // jpeg q95 = ~2x faster; --png for lossless masters
const first = await openPage(scale);
const meta = first.meta;
const fps = opt('fps', meta.fps || 60);
const t0 = opt('from', 0);
const t1 = opt('to', meta.duration);
const total = Math.round((t1 - t0) * fps);
const workers = Math.max(1, Math.min(opt('workers', 4), total));
const W = meta.width * scale, H = meta.height * scale;

fs.writeFileSync(path.join(outDir, 'cues.json'), JSON.stringify({ duration: meta.duration, fps, cues: meta.cues }, null, 2));
console.log(`scene ${path.basename(scene)}  ${W}x${H}  ${fps}fps  ${total} frames  ${workers} workers`);

const per = Math.ceil(total / workers);
const started = Date.now();
let done = 0;

async function renderChunk(w, pg) {
  const a = w * per, b = Math.min(total, a + per);
  if (a >= b) return null;
  const seg = path.join(outDir, `seg_${String(w).padStart(2, '0')}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', FMT === 'png' ? 'png' : 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(fps), seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const page = pg || (await openPage(scale)).page;
  for (let f = a; f < b; f++) {
    const t = t0 + f / fps;
    await page.evaluate(t => window.seek(t), t);
    const buf = await page.screenshot(FMT === 'png' ? { type: 'png', caret: 'hide' } : { type: 'jpeg', quality: 95, caret: 'hide' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    done++;
    if (done % fps === 0) {
      const el = (Date.now() - started) / 1000;
      process.stdout.write(`\r  ${done}/${total} frames  ${(done / el).toFixed(1)} fr/s  eta ${((total - done) / (done / el)).toFixed(0)}s   `);
    }
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));
  return seg;
}

const segs = (await Promise.all([...Array(workers).keys()].map(w => renderChunk(w, w === 0 ? first.page : null)))).filter(Boolean);
await Promise.all(browsers.map(b => b.close()));
const list = path.join(outDir, 'segs.txt');
fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', path.join(outDir, 'video.mp4')], { stdio: 'inherit' })
  .on('close', c => c === 0 ? res() : rej(new Error('concat failed'))));
segs.forEach(s => fs.unlinkSync(s)); fs.unlinkSync(list);
console.log(`\n  video.mp4 done in ${((Date.now() - started) / 1000).toFixed(1)}s`);
