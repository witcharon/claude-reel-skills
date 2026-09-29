#!/usr/bin/env python3
"""Retime a take onto the edit timeline and write graded, upscaled plates.

  python3 plates.py edit.json

edit.json:
{
  "fps": 24, "size": [1080, 1920], "duration": 31.5,
  "segments": [                                   // everything not covered is black (no plate)
    {"name": "cafe", "out": [0, 4], "src": [0.04, 4.04]},              // same length: 1x, nearest frame
    {"name": "stow", "out": [4, 6], "src": [4, 7.5], "blend": true},  // faster than 1x: average the shutter (speed ramp blur)
    {"name": "wake", "out": [22, 25], "src": [25.88, 28.04], "slow": {"dir": "frames", "prefix": "slow_", "t0": 25.8, "fps": 48}}
  ],
  "grade": {"contrast": 0.08, "saturation": 1.06}, "sharpen": 0.32
}
Slow segments read frames interpolated beforehand, e.g.
  ffmpeg -ss 25.8 -i source.mp4 -vf "minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -start_number 0 frames/slow_%04d.png
Writes plates/p_%04d.jpg (one per output frame that has picture) and plates/meta.json:
  {"fps", "size", "segments", "frames": [{"t", "seg", "src", "plate": 1}, ...]}
Film-specific data (screen quads, mattes, sun positions) is added to meta.json by the film's own scripts.
"""
import json, os, sys
import numpy as np
import cv2

cfg = json.load(open(sys.argv[1]))
FPS, (W, H) = cfg.get('fps', 24), cfg.get('size', [1080, 1920])
G = cfg.get('grade', {}); CON, SAT = G.get('contrast', .08), G.get('saturation', 1.06); SHARP = cfg.get('sharpen', .32)
SRC_FPS = cfg.get('src_fps', 24)
src_frames = sorted(f for f in os.listdir('frames') if f.startswith('src_'))
cache = {}

def load(path):
    if path not in cache:
        cache[path] = cv2.imread(path).astype(np.float32)
        if len(cache) > 16: cache.pop(next(iter(cache)))
    return cache[path]
def src(k): return load(f'frames/{src_frames[int(np.clip(k, 0, len(src_frames) - 1))]}')
def grade(img):
    x = img / 255.0
    x = x + CON * (x - .5) * (1 - np.abs(2 * x - 1))
    luma = x @ np.float32([.114, .587, .299])
    return np.clip((luma[..., None] + SAT * (x - luma[..., None])) * 255, 0, 255)
def upscale(img):
    big = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
    return big + SHARP * (big - cv2.GaussianBlur(big, (0, 0), 1.3))

os.makedirs('plates', exist_ok=True)
meta, n_plates = [], 0
for n in range(int(round(cfg['duration'] * FPS))):
    t = n / FPS; e = {'t': round(t, 4)}
    seg = next((s for s in cfg['segments'] if s['out'][0] <= t < s['out'][1]), None)
    if seg:
        (o0, o1), (s0, s1) = seg['out'], seg['src']
        speed = (s1 - s0) / (o1 - o0); s = s0 + (t - o0) * speed
        if 'slow' in seg:
            sl = seg['slow']; files = sorted(f for f in os.listdir(sl['dir']) if f.startswith(sl['prefix']))
            img = load(os.path.join(sl['dir'], files[int(np.clip(round((s - sl['t0']) * sl['fps']), 0, len(files) - 1))]))
        elif seg.get('blend') and speed > 1.2:   # a speed ramp: average what a shutter would have seen
            span = speed * .8; c = s * SRC_FPS
            ks = np.arange(np.floor(c - span / 2), np.ceil(c + span / 2) + 1)
            w = np.clip(np.minimum(ks + .5, c + span / 2) - np.maximum(ks - .5, c - span / 2), 0, None)
            img = sum(wi * src(k) for k, wi in zip(ks, w) if wi > 0) / w.sum()
        else:
            img = src(round(s * SRC_FPS))
        cv2.imwrite(f'plates/p_{n:04d}.jpg', upscale(grade(img)).clip(0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
        e.update(seg=seg.get('name', ''), src=round(s, 4), plate=1); n_plates += 1
    meta.append(e)
json.dump({'fps': FPS, 'size': [W, H], 'segments': cfg['segments'], 'frames': meta}, open('plates/meta.json', 'w'))
print(f'{len(meta)} frames, {n_plates} plates -> plates/')
