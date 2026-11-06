// Motion helpers for deterministic scenes. Include via <script src="../tools/motion.js"></script>
// Everything is a pure function of t (seconds). No CSS transitions, no requestAnimationFrame.
const M = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const prog = (t, start, dur) => clamp((t - start) / dur);           // 0..1 over [start, start+dur]
  const E = {
    linear: p => p,
    inCubic: p => p * p * p, outCubic: p => 1 - Math.pow(1 - p, 3), inOutCubic: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    outExpo: p => p === 1 ? 1 : 1 - Math.pow(2, -10 * p), inExpo: p => p === 0 ? 0 : Math.pow(2, 10 * p - 10),
    inOutExpo: p => p === 0 ? 0 : p === 1 ? 1 : p < .5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2,
    outBack: p => { const c = 1.70158; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
    outElastic: p => p === 0 || p === 1 ? p : Math.pow(2, -10 * p) * Math.sin((p * 10 - .75) * (2 * Math.PI) / 3) + 1,
  };
  // tween(t, start, dur, from, to, ease)
  const tw = (t, s, d, a, b, e = 'outCubic') => lerp(a, b, E[e](prog(t, s, d)));
  // in/hold/out opacity envelope
  const life = (t, s, e, fi = .3, fo = .3) => Math.min(E.outCubic(prog(t, s, fi)), 1 - E.inCubic(prog(t, e - fo, fo)));
  // deterministic pseudo-random
  const rand = seed => { let x = Math.sin(seed * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  // camera shake decaying after a hit at time h
  const shake = (t, h, amp = 18, decay = 9, freq = 38) => { const d = t - h; if (d < 0 || d > 1.2) return [0, 0];
    const k = amp * Math.exp(-d * decay); return [k * Math.sin(d * freq * 6.28), k * Math.cos(d * freq * 5.1)]; };
  // flash intensity after a hit
  const flash = (t, h, len = .18) => { const d = t - h; return d < 0 || d > len ? 0 : 1 - d / len; };
  const $ = s => document.querySelector(s);
  const css = (el, o) => { el = typeof el === 'string' ? $(el) : el; for (const k in o) el.style[k] = o[k]; return el; };
  // split text into span per char for staggered reveals
  const split = el => { el = typeof el === 'string' ? $(el) : el; const txt = el.textContent; el.textContent = '';
    return [...txt].map(ch => { const s = document.createElement('span'); s.textContent = ch === ' ' ? ' ' : ch; s.style.display = 'inline-block'; el.appendChild(s); return s; }); };
  // film grain: pre-rendered 256px noise tile (cheap), animate by jittering its position with M.rand per frame
  const grain = sel => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'), im = g.createImageData(256, 256);
    let s = 1; for (let i = 0; i < im.data.length; i += 4) { s = (s * 16807) % 2147483647; const v = s & 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0); css(sel, { backgroundImage: `url(${c.toDataURL()})` }); };
  return { grain, clamp, lerp, prog, E, tw, life, rand, shake, flash, $, css, split };
})();
