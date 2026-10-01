#!/usr/bin/env python3
"""Look at your own frames: the part that separates a finished film from a first try.

  python3 qc.py sheet  final.mp4 [--fps 4]            contact sheet with timestamps          -> out/qc/sheet.jpg
  python3 qc.py strip  final.mp4 --at 5.5 [--n 12] [--w 1080]   consecutive frames around a fast moment (full size with --w 1080) -> out/qc/strip_5.50.jpg
  python3 qc.py phone  final.mp4                      1 fps at 360 px wide: does it read on a phone? -> out/qc/phone.jpg
  python3 qc.py safe   final.mp4 --at 1.3,18.9,29      frames with Reels/TikTok danger zones drawn -> out/qc/safe.jpg
  python3 qc.py centre final.mp4 --at 29 --band 740:830 [--mode bg|bright|dark] [--thr N] [--save]
                                                      x-span and centre of what stands out in a band; bg (default) measures
                                                      against the local background, so it works on gradients, white and dark;
                                                      --save writes the detected pixels so you can check what was measured
  python3 qc.py loud   final.mp4                      integrated LUFS and true peak
  python3 qc.py motion final.mp4 [--shutter .5]       fluidity: still frames, jumps, long holds, and the fast stretches with
                                                      their on-screen speed (px per frame) to judge motion blur and subframes
  python3 qc.py compare final.mp4 --ref other.mp4 [--n 6]   the same relative moments of both films, ref on top -> out/qc/compare.jpg

Then score (references/critique.md), write the three worst problems with timestamps, fix, re-render, repeat.
"""
import argparse, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('cmd'); ap.add_argument('video'); ap.add_argument('--fps', type=float, default=4); ap.add_argument('--at', default='')
ap.add_argument('--n', type=int, default=12); ap.add_argument('--band', default=''); ap.add_argument('--thr', type=int, default=None)
ap.add_argument('--mode', default='bg', choices=['bg', 'bright', 'dark']); ap.add_argument('--save', action='store_true')
ap.add_argument('--w', type=int, default=270); ap.add_argument('--shutter', type=float, default=.5)
ap.add_argument('--out', default='out/qc'); ap.add_argument('--ref', default='')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
tmp = os.path.join(a.out, '_f.png')

def grab(t, w=None):
    vf = ['-vf', f'scale={w}:-1'] if w else []
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t}', '-i', a.video, '-frames:v', '1', *vf, tmp], check=True)
    return Image.open(tmp).convert('RGB')
def video_fps(v=None):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', v or a.video], capture_output=True, text=True).stdout
    num, den = map(float, out.split()[0].strip(',').split('/')); return num / den
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
    t0 = times[0]; fps = video_fps(); ts = [t0 + (k - a.n // 2) / fps for k in range(a.n)]
    tile([grab(max(0, t), a.w) for t in ts], a.n if a.w <= 400 else 4, [f'{t:.3f}' for t in ts]).save(os.path.join(a.out, f'strip_{t0:.2f}.jpg'), quality=88)
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
    from scipy.ndimage import median_filter
    y0, y1 = map(int, a.band.split(':'))
    for t in times:
        im = np.asarray(grab(t)).astype(np.float32); band = im[y0:y1]; W = im.shape[1]
        if a.mode == 'bg':     # what differs from the local background (a wide running median per row), so gradients and white grounds work
            bg = median_filter(band, size=(1, 301, 1), mode='nearest')
            ink = np.sqrt(((band - bg) ** 2).sum(axis=2)) > (a.thr or 48)
        else:
            lum = band @ np.float32([.299, .587, .114])
            ink = lum > (a.thr or 200) if a.mode == 'bright' else lum < (a.thr or 110)
        cols = ink.sum(axis=0) >= 2; xs = np.nonzero(cols)[0]
        if not len(xs): print(f'{t:.2f}s  band {y0}-{y1}: nothing stands out ({a.mode}); widen the band or lower --thr'); continue
        x0, x1 = xs.min(), xs.max(); c = (x0 + x1) / 2
        print(f'{t:.2f}s  band {y0}-{y1}: x {x0}-{x1}  centre {c:.0f} (frame centre 540, off by {c - 540:+.0f})')
        if x0 <= 2 or x1 >= W - 3: print('         the span reaches the frame edge: the band likely holds a full-width element, a vignette or a background change; tighten --band or check with --save')
        if a.save:
            o = Image.fromarray(im.astype(np.uint8)); dr = ImageDraw.Draw(o, 'RGBA')
            ys, xs2 = np.nonzero(ink); dr.point(list(zip(xs2.tolist(), (ys + y0).tolist())), fill=(255, 0, 255, 255))
            dr.rectangle([0, y0, W - 1, y1], outline=(0, 255, 255, 255), width=2); dr.line([540, y0 - 20, 540, y1 + 20], fill=(0, 255, 255, 255), width=2)
            dr.line([c, y0 - 20, c, y1 + 20], fill=(255, 0, 255, 255), width=2)
            o.crop((0, max(0, y0 - 60), W, min(im.shape[0], y1 + 60))).save(os.path.join(a.out, f'centre_{t:.2f}_{y0}.png')); print('         ->', os.path.join(a.out, f'centre_{t:.2f}_{y0}.png'))
elif a.cmd == 'motion':
    # mean absolute change between consecutive frames at 108x192 grey: still frames read as a slideshow, big jumps as stutter
    fps = video_fps()
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
    # on-screen speed: dense optical flow at 270x480, scaled to the film's width. Subframe motion blur averages N sharp
    # copies spread over (speed x shutter) px; when the gap between copies grows past a few px, edges can show doubled.
    import cv2
    W = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width', '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout.split()[0].strip(','))
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', a.video, '-vf', 'scale=270:480,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    g = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270); k = W / 270; spd = np.zeros(len(g))
    for i in range(1, len(g)):
        if cuts[i - 1]: continue
        fl = cv2.calcOpticalFlowFarneback(g[i - 1], g[i], None, .5, 3, 15, 3, 5, 1.2, 0)
        spd[i] = np.percentile(np.hypot(fl[..., 0], fl[..., 1]), 95) * k
    hot = spd > 24                                                  # the gap between copies passes ~6 px at sub 2
    fast, i = [], 0
    while i < len(spd):
        if hot[i]:
            j = i
            while j + 1 < len(spd) and (hot[j + 1] or (j + 6 < len(spd) and hot[j + 2:j + 7].any())): j += 1   # bridge short dips
            fast.append((i / fps, (j + 1) / fps, spd[i:j + 1].max())); i = j + 1
        else: i += 1
    print(f'on-screen speed (p95 of each frame): median {np.median(spd):.1f} px/frame, max {spd.max():.0f} px/frame')
    if fast:
        sh = a.shutter
        print(f'fast stretches. A subframe render stacks N sharp copies over speed x shutter ({sh}); the gap between copies is what can show:')
        print('     time         peak     gap at sub 2 / 4 / 6     sub for a ~4 px gap')
        for s0, s1, v in fast:
            need = int(np.ceil(v * sh / 4)); note = str(need) if need <= 8 else f'{need}: more than subframes can carry'
            print(f'  {s0:6.2f}-{s1:6.2f}s  {v:5.0f} px/f   {v * sh / 2:5.0f} / {v * sh / 4:4.0f} / {v * sh / 6:4.0f} px        {note}')
        print('  Measured on the whole frame (95th percentile): one fast object can dominate it. Look before acting:')
        print('  `qc.py strip <film> --at <t> --w 1080` shows the frames at full size. Doubled or stepped edges you can see are the')
        print('  problem; numbers alone are not. The options and when each fits are in references/doctrine.md (Craft: motion blur).')
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
