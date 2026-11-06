#!/usr/bin/env python3
"""Procedural SFX library + cue mixer (numpy only, 48 kHz stereo).

Usage:
  python3 sfx.py mix cues.json out.wav        # build the full soundtrack from cues
  python3 sfx.py preview out_dir               # render every SFX to separate wavs
  python3 sfx.py list                          # list SFX names and params

cues.json: {"duration": 12, "cues": [{"t": 0.5, "sfx": "whoosh", "gain": -6, "pan": 0.2, "dur": 0.8}, ...]}
  t     start time in seconds (for "riser"/"reverse_swell" t is the END/peak moment if "align":"end")
  gain  dB (default 0), pan -1..1, any extra keys are passed to the generator
  sfx   a name from SFX below, or "file" with {"path": "assets/sfx/x.wav"}
"""
import json, sys, wave, os, inspect
import numpy as np

SR = 48000
RNG = np.random.default_rng(7)

# ---------------------------------------------------------------- utilities
def t_axis(dur): return np.arange(int(dur * SR)) / SR
def env_exp(n, k): return np.exp(-np.arange(n) / SR * k)
def env_adsr(n, a=0.005, r=0.05):
    e = np.ones(n); ia, ir = int(a * SR), int(r * SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    if ir: e[-ir:] *= np.linspace(1, 0, ir)
    return e
def noise(n): return RNG.standard_normal(n)
def db(x): return 10 ** (x / 20)
def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1; return x / m * peak
def sweep_phase(f0, f1, n, curve='exp'):
    if curve == 'exp': f = f0 * (f1 / f0) ** np.linspace(0, 1, n)
    else: f = np.linspace(f0, f1, n)
    return 2 * np.pi * np.cumsum(f) / SR

def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))

def moving_band(x, centers, q=1.5, block=1024):
    """Time-varying band-pass via overlap-add. centers: array of center freq per sample."""
    hop = block // 2; win = np.hanning(block); out = np.zeros(len(x) + block)
    f = np.fft.rfftfreq(block, 1 / SR); xp = np.concatenate([x, np.zeros(block)])
    for i in range(0, len(x), hop):
        c = centers[min(i + hop, len(centers) - 1)]
        bw = c / q
        g = np.exp(-0.5 * ((f - c) / bw) ** 2)
        seg = np.fft.irfft(np.fft.rfft(xp[i:i + block] * win) * g, block)
        out[i:i + block] += seg
    return out[:len(x)]

def reverb(x, dur=1.6, mix=0.25, damp=6000):
    n = int(dur * SR); ir = noise(n) * env_exp(n, 6.9 / dur)
    ir = fft_filter(ir, lo=200, hi=damp); ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n; N = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:L]
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - mix) + wet * mix * 0.6

def sat(x, drive=2.0): return np.tanh(x * drive) / np.tanh(drive)

# ---------------------------------------------------------------- SFX generators (return mono float)
def whoosh(dur=0.8, f0=300, f1=4000, peak=0.6):
    """Air swoosh passing by. peak = relative position of loudest point."""
    n = int(dur * SR); x = noise(n)
    p = np.linspace(0, 1, n)
    centers = np.where(p < peak, f0 * (f1 / f0) ** (p / peak), f1 * (f0 / f1) ** ((p - peak) / (1 - peak)))
    y = moving_band(x, centers, q=1.2)
    e = np.where(p < peak, (p / peak) ** 2, ((1 - p) / (1 - peak)) ** 1.5)
    return norm(y * e, 0.8)

def swish(dur=0.25):
    return whoosh(dur, 1500, 9000, peak=0.35) * 0.8

def impact(dur=2.2, f0=140, f1=38, punch=1.0):
    """Cinematic hit: sub sine sweep + noise crack + saturation + tail."""
    n = int(dur * SR)
    sub = np.sin(sweep_phase(f0, f1, n)) * env_exp(n, 2.6)
    crack = fft_filter(noise(n), lo=800, hi=9000) * env_exp(n, 35) * 0.9 * punch
    body = fft_filter(noise(n), lo=60, hi=900) * env_exp(n, 9) * 0.6
    y = sat(sub * 1.2 + crack + body, 2.5)
    return norm(reverb(y, 2.0, 0.3, 4000)[:n + SR], 0.95)

def boom(dur=3.0): return impact(dur, 90, 28, 0.5)

def sub_drop(dur=1.8, f0=110, f1=25):
    n = int(dur * SR)
    return norm(sat(np.sin(sweep_phase(f0, f1, n)) * env_adsr(n, 0.01, dur * 0.5), 1.5), 0.9)

def riser(dur=3.0, f0=200, f1=6000):
    """Tension build: rising filtered noise + rising detuned saw, crescendo to the end."""
    n = int(dur * SR); p = np.linspace(0, 1, n)
    air = moving_band(noise(n), f0 * (f1 / f0) ** p, q=2.0)
    ph = sweep_phase(80, 640, n)
    saw = sum(((ph * k / (2 * np.pi) + d) % 1.0 * 2 - 1) for k, d in [(1, 0), (1.007, .3), (0.994, .6)]) / 3
    saw = fft_filter(saw, hi=3000)
    trem = 1 + 0.35 * np.sin(2 * np.pi * np.cumsum(2 + 18 * p ** 2) / SR)
    y = (air * 0.9 + saw * 0.35) * (p ** 2.2) * trem
    return norm(y, 0.85)

def reverse_swell(dur=1.6):
    """Reverse cymbal: bright decaying noise, reversed."""
    n = int(dur * SR)
    y = fft_filter(noise(n), lo=3000, hi=14000) * env_exp(n, 4.5)
    return norm(reverb(y, 1.0, 0.4)[:n][::-1], 0.7)

def tick(dur=0.06, f=2800):
    n = int(dur * SR); t = t_axis(dur)
    y = np.sin(2 * np.pi * f * t) * env_exp(n, 90) + fft_filter(noise(n), lo=4000) * env_exp(n, 400) * 0.5
    return norm(y, 0.7)

def click(dur=0.03): return tick(dur, 4200) * 0.8

def typing(dur=1.0, rate=14, seed=3):
    r = np.random.default_rng(seed); out = np.zeros(int(dur * SR) + SR // 10); t = 0.0
    while t < dur:
        k = tick(0.04, r.uniform(1800, 3200)) * r.uniform(0.4, 0.9); i = int(t * SR)
        out[i:i + len(k)] += k; t += r.exponential(1 / rate) + 0.02
    return norm(out, 0.6)

def glitch(dur=0.5, seed=1):
    r = np.random.default_rng(seed); n = int(dur * SR); out = np.zeros(n); i = 0
    while i < n:
        L = int(r.uniform(0.005, 0.05) * SR); t = np.arange(L) / SR; kind = r.integers(3)
        if kind == 0: s = np.sign(np.sin(2 * np.pi * r.uniform(80, 1200) * t))
        elif kind == 1: s = fft_filter(noise(L), lo=r.uniform(500, 4000))
        else: s = np.round(np.sin(2 * np.pi * r.uniform(200, 3000) * t) * 3) / 3
        out[i:i + L] = s[:max(0, min(L, n - i))] * r.uniform(0.3, 1.0) * (r.random() > 0.2); i += L
    return norm(out, 0.6)

def shimmer(dur=2.0, base=880):
    """Sparkle / gold glint: high bell partials with tremolo and fade."""
    n = int(dur * SR); t = t_axis(dur); y = np.zeros(n)
    for k, a in [(1, 1), (1.5, .6), (2, .5), (2.997, .35), (4.01, .25), (5.4, .15)]:
        y += a * np.sin(2 * np.pi * base * k * t + RNG.uniform(0, 6)) * env_exp(n, 1.5 + k * 0.6)
    y *= 1 + 0.3 * np.sin(2 * np.pi * 9 * t); y *= env_adsr(n, 0.01, 0.2)
    return norm(reverb(y, 2.5, 0.45, 12000)[:n + SR], 0.55)

def chime(dur=1.5, f=1320): return shimmer(dur, f)

def braam(dur=3.0, f=55):
    """Low brass-like 'BRAAM' hit (detuned saws, lowpass, saturation)."""
    n = int(dur * SR); t = t_axis(dur); y = np.zeros(n)
    for k in [1, 1.004, 0.996, 2.003, 1.498]:
        y += ((f * k * t) % 1.0 * 2 - 1)
    y = fft_filter(y, hi=900) * env_adsr(n, 0.04, dur * 0.6) * env_exp(n, 0.9)
    return norm(reverb(sat(y, 3), 2.5, 0.3, 3000)[:n + SR], 0.9)

def heartbeat(dur=1.0):
    n = int(dur * SR); out = np.zeros(n)
    for off, g in [(0, 1), (0.22, 0.7)]:
        k = sub_drop(0.25, 70, 35) * g; i = int(off * SR); out[i:i + len(k)] += k[:n - i]
    return norm(out, 0.9)

def tape_stop(dur=0.8, f=220):
    n = int(dur * SR); f_t = f * np.linspace(1, 0.02, n) ** 1.5
    ph = 2 * np.pi * np.cumsum(f_t) / SR
    return norm(sat(np.sin(ph) + 0.5 * np.sin(2 * ph), 2) * env_adsr(n, 0.005, 0.1), 0.7)

def pad(dur=10.0, root=55.0, chord=(1, 1.5, 2, 2.52, 3), lfo=0.12):
    """Atmospheric drone bed (use as a long cue at low gain)."""
    n = int(dur * SR); t = t_axis(dur); y = np.zeros(n)
    for i, k in enumerate(chord):
        for d in (-0.15, 0.15):
            y += np.sin(2 * np.pi * (root * k + d) * t + i) / (1 + i * 0.4)
    y = fft_filter(y + fft_filter(noise(n), lo=100, hi=600) * 0.05, hi=1800)
    y *= 0.8 + 0.2 * np.sin(2 * np.pi * lfo * t); y *= env_adsr(n, min(2.0, dur / 4), min(2.5, dur / 3))
    return norm(y, 0.6)

def pulse(dur=4.0, bpm=120, f=50):
    """Driving sub pulse (tempo kicks) for montage energy."""
    n = int(dur * SR); out = np.zeros(n + SR); step = 60 / bpm
    for i in range(int(dur / step) + 1):
        k = sub_drop(0.35, 150, f) * (1 if i % 4 == 0 else 0.75); j = int(i * step * SR); out[j:j + len(k)] += k
    return norm(out[:n], 0.9)

def logo_hit(dur=3.5):
    """Layered signature hit: impact + braam + shimmer."""
    a, b, c = impact(dur), braam(dur, 49), shimmer(dur, 1046)
    L = max(len(a), len(b), len(c)); y = np.zeros(L)
    for s, g in [(a, 1.0), (b, 0.55), (c, 0.4)]: y[:len(s)] += s * g
    return norm(y, 0.95)

SFX = {k: v for k, v in dict(whoosh=whoosh, swish=swish, impact=impact, boom=boom, sub_drop=sub_drop, riser=riser,
       reverse_swell=reverse_swell, tick=tick, click=click, typing=typing, glitch=glitch, shimmer=shimmer, chime=chime,
       braam=braam, heartbeat=heartbeat, tape_stop=tape_stop, pad=pad, pulse=pulse, logo_hit=logo_hit).items()}
END_ALIGNED = {'riser', 'reverse_swell'}

# ---------------------------------------------------------------- io
def read_wav(path):
    with wave.open(path) as w:
        ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype={2: np.int16, 4: np.int32}[sw]).astype(float)
        x /= 2 ** (8 * sw - 1); x = x.reshape(-1, ch).mean(1)
    if sr != SR: x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)
    return x

def write_wav(path, st):
    st = np.clip(st, -1, 1); d = (st * 32767).astype(np.int16)
    with wave.open(path, 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())

def render_cue(c):
    name = c['sfx']; params = {k: v for k, v in c.items() if k not in ('t', 'sfx', 'gain', 'pan', 'align', 'path', 'width')}
    if name == 'file':
        p = c['path']; p = p if os.path.isabs(p) else os.path.join(os.path.dirname(__file__), '..', p); return read_wav(p)
    fn = SFX[name]; ok = inspect.signature(fn).parameters
    return fn(**{k: v for k, v in params.items() if k in ok})

def mix(cues_path, out_path):
    spec = json.load(open(cues_path)); dur = spec['duration']
    bus = np.zeros((int((dur + 4) * SR), 2))
    for c in spec['cues']:
        y = render_cue(c) * db(c.get('gain', 0)); pan = c.get('pan', 0.0)
        start = c['t'] - (c.get('dur', 0) if (c['sfx'] in END_ALIGNED and c.get('align', 'end') == 'end' and 'dur' in c) else 0)
        if c['sfx'] in END_ALIGNED and 'dur' not in c and c.get('align', 'end') == 'end':
            start = c['t'] - len(y) / SR
        i = max(0, int(start * SR)); y = y[max(0, -int(start * SR)):]
        L = min(len(y), len(bus) - i)
        if L <= 0: continue
        w = c.get('width', 0.15)  # tiny Haas widening for space
        d = int(w * 0.012 * SR)
        l = y[:L] * np.sqrt((1 - pan) / 2) * 1.414; r = y[:L] * np.sqrt((1 + pan) / 2) * 1.414
        bus[i:i + L, 0] += l
        r_d = np.concatenate([np.zeros(d), r])[:L]; bus[i:i + L, 1] += r_d
    bus = bus[:int(dur * SR)]
    # master: glue saturation + peak normalize to -1 dBFS (loudness handled by ffmpeg loudnorm in mux)
    bus = sat(bus / (np.max(np.abs(bus)) or 1) * 1.2, 1.4) * db(-1)
    fade = int(0.05 * SR); bus[-fade:] *= np.linspace(1, 0, fade)[:, None]
    write_wav(out_path, bus); print(f'mixed {len(spec["cues"])} cues -> {out_path} ({dur:.2f}s)')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    if cmd == 'mix': mix(sys.argv[2], sys.argv[3])
    elif cmd == 'preview':
        os.makedirs(sys.argv[2], exist_ok=True)
        for k, fn in SFX.items():
            y = fn(); write_wav(os.path.join(sys.argv[2], k + '.wav'), np.stack([y, y], 1)); print('ok', k)
    else:
        for k, fn in SFX.items():
            print(f'{k:14s} {str(inspect.signature(fn)):45s} {(fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""}')
