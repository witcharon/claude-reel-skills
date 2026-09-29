#!/usr/bin/env python3
"""Put the score under the picture at a measured loudness (two-pass EBU R128 loudnorm), then report the result.

  python3 mux.py out/video.mp4 out/score.wav ../../final.mp4 [--lufs -15] [--tp -1.5]

-15 LUFS integrated / -1.5 dBTP suits Reels and TikTok (they normalise quieter content up less gracefully than
louder content down). The numbers are measurements, not listening: tell the user to listen once on headphones.
"""
import argparse, json, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('audio'); ap.add_argument('out')
ap.add_argument('--lufs', type=float, default=-15); ap.add_argument('--tp', type=float, default=-1.5); ap.add_argument('--lra', type=float, default=11)
a = ap.parse_args()
first = subprocess.run(['ffmpeg', '-hide_banner', '-i', a.audio, '-af', f'loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', first, re.S).group(0))
af = (f'loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}'
      f':measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true,aresample=48000')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.video, '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', af,
                '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', a.out], check=True)
rep = subprocess.run(['ffmpeg', '-hide_banner', '-i', a.out, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
i = re.findall(r'I:\s+(-?[\d.]+) LUFS', rep)[-1]; tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', rep)[-1]
dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.out], capture_output=True, text=True).stdout.strip()
print(f'{a.out}: {float(dur):.2f} s, {i} LUFS integrated, true peak {tp} dBFS')
