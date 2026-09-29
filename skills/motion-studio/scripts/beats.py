#!/usr/bin/env python3
"""Measure a supplied music track so the picture can sit on it.

  python3 beats.py song.wav > beats.json      ->  {"bpm", "beats", "downbeats", "hits"}

State changes go on beats, big moments on downbeats, sound effects and punches on hits. Uses librosa when installed
(pip install librosa soundfile); otherwise a spectral-flux onset + autocorrelation tempo fallback.
"""
import json, sys
import numpy as np

path = sys.argv[1]
try:
    import librosa
    y, sr = librosa.load(path, sr=None, mono=True)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beats = librosa.frames_to_time(frames, sr=sr).round(3).tolist()
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=.5, wait=10)
    hits = librosa.frames_to_time(peaks, sr=sr).round(3).tolist(); bpm = float(np.atleast_1d(tempo)[0])
except ImportError:
    from scipy.io import wavfile
    from scipy import signal
    sr, x = wavfile.read(path); x = x.astype(float); x = x.mean(1) if x.ndim > 1 else x
    hop = 512; f, t, S = signal.stft(x, sr, nperseg=2048, noverlap=2048 - hop); mag = np.abs(S)
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(0); flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fr = sr / hop; ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    lags = np.arange(len(ac)) / fr; ok = (lags > 60 / 180) & (lags < 60 / 70)
    period = lags[ok][np.argmax(ac[ok])]; bpm = 60 / period
    phase = max(range(int(period * fr)), key=lambda p: flux[p::max(1, int(round(period * fr)))].sum())
    beats = [round((phase + k * period * fr) / fr, 3) for k in range(int((len(flux) / fr - phase / fr) / period))]
    pk, _ = signal.find_peaks(flux, height=1.5, distance=int(.1 * fr)); hits = (pk / fr).round(3).tolist()
json.dump({'bpm': round(bpm, 2), 'beats': beats, 'downbeats': beats[::4], 'hits': hits}, sys.stdout, indent=1)
