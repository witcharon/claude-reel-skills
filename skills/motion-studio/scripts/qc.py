#!/usr/bin/env python3
"""Look at your own frames: the part that separates a finished film from a first try.

  python3 qc.py sheet  final.mp4 [--fps 4]            contact sheet with timestamps          -> out/qc/sheet.jpg
  python3 qc.py strip  final.mp4 --at 5.5 [--n 12]    consecutive frames around a fast moment -> out/qc/strip_5.50.jpg
  python3 qc.py phone  final.mp4                      1 fps at 360 px wide: does it read on a phone? -> out/qc/phone.jpg
  python3 qc.py safe   final.mp4 --at 1.3,18.9,29      frames with Reels/TikTok danger zones drawn -> out/qc/safe.jpg
  python3 qc.py centre final.mp4 --at 29 --band 740:830 [--thr 200]   x-span and centre of bright text in a band
  python3 qc.py loud   final.mp4                      integrated LUFS and true peak
  python3 qc.py motion final.mp4                      fluidity: fps, share of still frames, frame-to-frame jumps, the biggest jumps with times
  python3 qc.py compare final.mp4 --ref other.mp4 [--n 6]   the same relative moments of both films, ref on top -> out/qc/compare.jpg

Then score (references/critique.md), write the three worst problems with timestamps, fix, re-render, repeat.
"""
import argparse, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('cmd'); ap.add_argument('video'); ap.add_argument('--fps', type=float, default=4); ap.add_argument('--at', default='')
ap.add_argument('--n', type=int, default=12); ap.add_argument('--band', default=''); ap.add_argument('--thr', type=int, default=200)
ap.add_argument('--out', default='out/qc'); ap.add_argument('--ref', default='')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
tmp = os.path.join(a.out, '_f.png')

def grab(t, w=None):
    vf = ['-vf', f'scale={w}:-1'] if w else []
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t}', '-i', a.video, '-frames:v', '1', *vf, tmp], check=True)
    return Image.open(tmp).convert('RGB')
def duration():
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout)
def tile(ims, cols, labels):
    w, h = ims[0].size; o = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols))); d = ImageDraw.Draw(o)
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * w, (i // cols) * h; o.paste(im, (x, y)); d.rectangle([x, y, x + 46, y + 15], fill='black'); d.text((x + 3, y + 2), lab, fill='yellow')
    return o
times = [float(x) for x in a.at.split(',') if x]

if a.cmd == 'sheet':
    ts = np.arange(0, duration(), 1 / a.fps); ims = [grab(t, 180) for t in ts]
    tile(ims, 16, [f'{t:.2f}' for t in ts]).save(os.path.join(a.out, 'sheet.jpg'), quality=85)
elif a.cmd == 'strip':
    t0 = times[0]; fps = 24; ts = [t0 + (k - a.n // 2) / fps for k in range(a.n)]
    tile([grab(max(0, t), 270) for t in ts], a.n, [f'{t:.3f}' for t in ts]).save(os.path.join(a.out, f'strip_{t0:.2f}.jpg'), quality=88)
elif a.cmd == 'phone':
    ts = np.arange(0, duration(), 1.0); tile([grab(t, 360) for t in ts], 8, [f'{t:.0f}s' for t in ts]).save(os.path.join(a.out, 'phone.jpg'), quality=85)
elif a.cmd == 'safe':
    ims = []
    for t in times:
        im = grab(t); d = ImageDraw.Draw(im, 'RGBA'); W, H = im.size
        d.rectangle([0, 0, W, 250], fill=(255, 0, 0, 60)); d.rectangle([0, 1440, W, H], fill=(255, 0, 0, 60))
        d.rectangle([890, 880, W, 1600], fill=(255, 160, 0, 60)); d.line([540, 0, 540, H], fill=(0, 255, 255, 140), width=3)
        ims.append(im.resize((360, 640)))
    tile(ims, len(ims), [f'{t:.2f}' for t in times]).save(os.path.join(a.out, 'safe.jpg'), quality=88)
elif a.cmd == 'centre':
    y0, y1 = map(int, a.band.split(':'))
    for t in times:
        g = np.asarray(grab(t).convert('L'))[y0:y1].astype(int); xs = np.nonzero((g > a.thr).any(axis=0))[0]
        print(f'{t:.2f}s  band {y0}-{y1}: ' + (f'x {xs.min()}-{xs.max()}  centre {(xs.min() + xs.max()) / 2:.0f} (frame centre 540)' if len(xs) else 'nothing above threshold'))
elif a.cmd == 'motion':
    # mean absolute change between consecutive frames at 108x192 grey: still frames read as a slideshow, big jumps as stutter
    fps = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout.strip()
    num, den = map(float, fps.split('/')); fps = num / den
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', a.video, '-vf', 'scale=108:192,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 192, 108).astype(np.float32); d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    cuts = d > 25                                                   # whole-frame changes: hard cuts, planned or not
    moving = d[~cuts]
    print(f'{len(f)} frames @ {fps:.0f} fps | still (Δ<0.15): {(d < .15).mean() * 100:.0f}% | median Δ {np.median(moving):.2f} | p95 Δ {np.percentile(moving, 95):.2f} | hard cuts: {int(cuts.sum())}')
    top = np.argsort(-d)[:6]
    print('biggest jumps (check each is a planned cut): ' + ', '.join(f'{(i + 1) / fps:.2f}s Δ{d[i]:.1f}' for i in sorted(top)))
    runs, n = [], 0
    for i, v in enumerate(d < .15):
        n = n + 1 if v else 0
        if n == int(fps * .8): runs.append((i + 1 - n + 1) / fps)
    if runs: print('holds longer than 0.8 s start at: ' + ', '.join(f'{r:.1f}s' for r in runs))
elif a.cmd == 'compare':
    def dur(v): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', v], capture_output=True, text=True).stdout)
    n = a.n if a.n != 12 else 6; rows = []
    for v in (a.ref, a.video):
        D = dur(v); ims = []
        for k in range(n):
            t = (k + .5) * D / n; subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t}', '-i', v, '-frames:v', '1', '-vf', 'scale=-2:640', tmp], check=True)
            im = Image.open(tmp).convert('RGB'); ims.append(im.resize((int(im.width * 640 / im.height), 640)))
        rows.append((v, ims))
    w = max(sum(im.width for im in ims) for _, ims in rows); o = Image.new('RGB', (w, 1300), 'white'); dr = ImageDraw.Draw(o)
    for r, (v, ims) in enumerate(rows):
        x = 0
        for im in ims: o.paste(im, (x, r * 660)); x += im.width
        dr.rectangle([0, r * 660, 360, r * 660 + 16], fill='black'); dr.text((3, r * 660 + 2), ('ref: ' if r == 0 else 'film: ') + os.path.basename(v), fill='yellow')
    o.save(os.path.join(a.out, 'compare.jpg'), quality=88)
elif a.cmd == 'loud':
    rep = subprocess.run(['ffmpeg', '-hide_banner', '-i', a.video, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    print('integrated', re.findall(r'I:\s+(-?[\d.]+) LUFS', rep)[-1], 'LUFS | true peak', re.findall(r'Peak:\s+(-?[\d.]+) dBFS', rep)[-1], 'dBFS')
if a.cmd in ('sheet', 'strip', 'phone', 'safe', 'compare'): print('->', a.out)
