#!/usr/bin/env python3
"""Put the score under the picture at a measured loudness with a true-peak ceiling, then verify both.

  python3 mux.py out/video.mp4 out/score.wav ../../final.mp4 [--lufs -15] [--tp -1.5] [--allow-short]

Master: a gain to the target loudness, then a 4x-oversampled limiter (so it catches inter-sample peaks) with its
ceiling a little under --tp. Limiting eats loudness, so the gain is measured and corrected until the loudness is
within 0.2 LU. After the AAC encode the file is measured again; if the codec pushed the true peak over --tp the
ceiling comes down and it re-encodes. It exits non-zero if the target still isn't met, or if the video is shorter
than the score (a render that stopped early), unless --allow-short.
(A two-pass loudnorm alone can't do this: a punchy mix with a wide loudness range pushes it out of linear mode or
over the peak target, and it only reports that.)
-15 LUFS / -1.5 dBTP suits Reels and TikTok. The numbers are measurements, not listening: tell the user to listen once on headphones.
"""
import argparse, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('audio'); ap.add_argument('out')
ap.add_argument('--lufs', type=float, default=-15); ap.add_argument('--tp', type=float, default=-1.5)
ap.add_argument('--allow-short', action='store_true')
a = ap.parse_args()

def duration(path, stream=None):
    q = ['-select_streams', stream, '-show_entries', 'stream=duration'] if stream else ['-show_entries', 'format=duration']
    out = subprocess.run(['ffprobe', '-v', 'error', *q, '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.split()
    return float(out[0]) if out and out[0] != 'N/A' else 0.0
def measure(path, chain=None):
    af = f'{chain},ebur128=peak=true' if chain else 'ebur128=peak=true'
    rep = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-map', '0:a', '-af', af, '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', rep)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+|-inf) dBFS', rep)[-1])
def master(gain, ceiling):
    lim = min(1.0, 10 ** (ceiling / 20))
    return f'volume={gain:.2f}dB,aresample=192000,alimiter=limit={lim:.4f}:attack=1:release=80:level=disabled,aresample=48000'

vid, aud = duration(a.video, 'v:0') or duration(a.video), duration(a.audio)
if vid < aud - .1:
    msg = f'video is {vid:.2f} s but the score is {aud:.2f} s: the render may have stopped early'
    if not a.allow_short: sys.exit(f'mux: {msg} (use --allow-short if that is intended)')
    print(f'warning: {msg}')

i_in, tp_in = measure(a.audio)
gain, ceiling = a.lufs - i_in, a.tp - .5                     # headroom for the AAC encoder's overshoot
for _ in range(4):
    for _ in range(5):                                        # the limiter eats loudness: measure and correct
        i, tp = measure(a.audio, master(gain, ceiling))
        if abs(i - a.lufs) <= .2: break
        gain += a.lufs - i
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.video, '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-af', master(gain, ceiling), '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', a.out], check=True)
    i, tp = measure(a.out)
    if tp <= a.tp: break
    ceiling -= tp - a.tp + .1                                 # the codec overshot (dense mixes: ~1 dB): lower the ceiling, recalibrate
print(f'score in: {i_in:.1f} LUFS, true peak {tp_in:+.1f} dBTP | gain {gain:+.1f} dB, limiter ceiling {ceiling:.1f} dBFS (4x oversampled)')
print(f'{a.out}: {duration(a.out):.2f} s, {i:.1f} LUFS integrated, true peak {tp:.1f} dBTP')
if tp > a.tp or abs(i - a.lufs) > .5:
    sys.exit(f'mux: missed the target ({a.lufs} LUFS / {a.tp} dBTP); the file is written but check the mix')
