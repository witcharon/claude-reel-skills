#!/usr/bin/env python3
"""Look at a generated take before planning the edit.

  python3 ingest.py source.mp4 [--dir .] [--every 0.33]

Writes, inside --dir:
  frames/src_%04d.png   every source frame (for tracking and plates)
  out/contact.png       labelled contact sheet (frame number and seconds)
  out/ingest.json       probe, cuts (big frame differences), dark runs, per-frame motion/luma, audio loudness per 0.25 s
Read the contact sheet with your eyes before deciding anything; the numbers only point at where to look.
"""
import argparse, json, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('source'); ap.add_argument('--dir', default='.'); ap.add_argument('--every', type=float, default=.33)
ap.add_argument('--cut', type=float, default=28, help='mean abs diff (0-255 at 180x320) that counts as a cut')
ap.add_argument('--dark', type=float, default=8, help='mean luma below this is darkness')
a = ap.parse_args()
os.makedirs(os.path.join(a.dir, 'frames'), exist_ok=True); os.makedirs(os.path.join(a.dir, 'out'), exist_ok=True)

probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,nb_frames,sample_rate:format=duration',
                                   '-of', 'json', a.source], capture_output=True, text=True, check=True).stdout)
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
num, den = map(int, v['r_frame_rate'].split('/')); fps = num / den
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.source, '-fps_mode', 'passthrough', os.path.join(a.dir, 'frames/src_%04d.png')], check=True)
files = sorted(f for f in os.listdir(os.path.join(a.dir, 'frames')) if f.startswith('src_'))
n = len(files)

motion, luma, prev = [], [], None
for f in files:
    g = cv2.resize(cv2.imread(os.path.join(a.dir, 'frames', f), 0), (180, 320)).astype(np.float32)
    motion.append(0.0 if prev is None else float(np.abs(g - prev).mean())); luma.append(float(g.mean())); prev = g
cuts = [{'frame': i, 't': round(i / fps, 3), 'diff': round(d, 1)} for i, d in enumerate(motion) if d > a.cut]
runs = []
for i, l in enumerate(luma):
    if l < a.dark:
        if runs and runs[-1][1] == i - 1: runs[-1][1] = i
        else: runs.append([i, i])
dark = [{'frames': [s, e], 't': [round(s / fps, 3), round((e + 1) / fps, 3)]} for s, e in runs]

audio = []
has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])
if has_audio:
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', a.source, '-ac', '1', '-ar', '32000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32); hop = 8000
    audio = [{'t': round(i / 32000, 2), 'db': round(float(20 * np.log10(np.sqrt((x[i:i + hop] ** 2).mean()) + 1e-9)), 1)} for i in range(0, len(x) - hop, hop)]

step = max(1, round(a.every * fps)); idx = list(range(0, n, step))
tw, th = 144, int(144 * v['height'] / v['width']); cols = max(1, min(16, len(idx)))
sheet = Image.new('RGB', (tw * cols, th * ((len(idx) + cols - 1) // cols))); d = ImageDraw.Draw(sheet)
for k, i in enumerate(idx):
    x0, y0 = (k % cols) * tw, (k // cols) * th
    sheet.paste(Image.open(os.path.join(a.dir, 'frames', files[i])).convert('RGB').resize((tw, th)), (x0, y0))
    d.rectangle([x0, y0, x0 + 70, y0 + 13], fill='black'); d.text((x0 + 2, y0 + 1), f'{i} {i / fps:.2f}', fill='yellow')
sheet.save(os.path.join(a.dir, 'out/contact.png'))

json.dump({'source': a.source, 'fps': fps, 'frames': n, 'size': [v['width'], v['height']], 'duration': float(probe['format']['duration']),
           'cuts': cuts, 'dark': dark, 'audio_db_per_0.25s': audio, 'motion': [round(m, 2) for m in motion], 'luma': [round(l, 1) for l in luma]},
          open(os.path.join(a.dir, 'out/ingest.json'), 'w'), indent=1)
print(f'{n} frames @ {fps:g} fps, {v["width"]}x{v["height"]}, {float(probe["format"]["duration"]):.2f} s')
print('cuts:', [(c['frame'], c['t']) for c in cuts])
print('dark runs (s):', [r['t'] for r in dark])
print('contact sheet -> out/contact.png')
