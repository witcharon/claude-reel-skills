#!/usr/bin/env python3
"""Replace stretches of a rendered film with re-rendered patches, frame-exact, and check the result.

  python3 splice.py out/video.mp4 out/video_fixed.mp4 out/fix_a.mp4@14.0 out/fix_b.mp4@24.5

Each patch is a render of the same page from its start time (`render.mjs --from 14.0 --to 14.5 ...`) at the same fps
and size; it replaces exactly as many frames as it holds. Useful to re-render only what changed, or only the fast
stretches with more subframes (`--sub 6`), instead of the whole film. The output keeps the base's frame count; it is
re-encoded once (VideoToolbox when available, else libx264) and verified by ffprobe.
"""
import subprocess, sys

def probe(v, entry):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', f'stream={entry}', '-of', 'csv=p=0', v], capture_output=True, text=True).stdout
    return out.split()[0].strip(',')
base, out, patches = sys.argv[1], sys.argv[2], [(p.split('@')[0], float(p.split('@')[1])) for p in sys.argv[3:]]
num, den = map(float, probe(base, 'r_frame_rate').split('/')); fps = num / den; total = int(probe(base, 'nb_read_packets'))
spans, prev = [], 0
for i, (p, t0) in sorted(enumerate(patches), key=lambda e: e[1][1]):
    f0, n = round(t0 * fps), int(probe(p, 'nb_read_packets'))
    if f0 < prev: sys.exit(f'splice: {p} starts at frame {f0}, inside the previous patch')
    if f0 + n > total: sys.exit(f'splice: {p} runs past the end of the film')
    spans.append((prev, f0, i + 1, n)); prev = f0 + n
chains, labels = [], []
for k, (b0, b1, pi, n) in enumerate(spans):
    if b1 > b0: chains.append(f'[0:v]trim=start_frame={b0}:end_frame={b1},setpts=PTS-STARTPTS[b{k}]'); labels.append(f'[b{k}]')
    chains.append(f'[{pi}:v]trim=end_frame={n},setpts=PTS-STARTPTS[p{k}]'); labels.append(f'[p{k}]')
if prev < total: chains.append(f'[0:v]trim=start_frame={prev},setpts=PTS-STARTPTS[tail]'); labels.append('[tail]')
fc = ';'.join(chains) + ';' + ''.join(labels) + f'concat=n={len(labels)}:v=1[v]'
vt = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=256x256:d=0.2', '-c:v', 'h264_videotoolbox', '-allow_sw', '0', '-f', 'null', '-'], capture_output=True).returncode == 0
enc = ['-c:v', 'h264_videotoolbox', '-b:v', '24M', '-maxrate', '32M', '-profile:v', 'high', '-allow_sw', '0'] if vt else ['-c:v', 'libx264', '-preset', 'slow', '-crf', '16']
inputs = sum((['-i', p] for p, _ in patches), [])
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', base, *inputs, '-filter_complex', fc, '-map', '[v]', *enc, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], check=True)
got = int(probe(out, 'nb_read_packets'))
if got != total: sys.exit(f'splice: {out} has {got} frames, expected {total}')
print(f'{out}: {got} frames @ {fps:.0f} fps, {len(patches)} patch(es) spliced')
