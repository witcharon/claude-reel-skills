"""Sound kit for code-scored films: buses, synthesized instruments and effects, perspective, tape-stop, the Nolan ending.

    import sys; sys.path.insert(0, '<skill>/scripts'); from audio_kit import *
    kit = Kit(dur=31.5)                  # holds SR, N, rng and the time axis
    music, sfx = kit.bus(), kit.bus()
    sfx.add(kit.click(pitch=kit.vary()), t_key - kit.EARLY)

Rules baked in (see references/sound.md): cue effects ~0.03 s before the contact frame (EARLY), vary the pitch of
repeated sounds, and treat loudness as measured, never as listened (say so when you deliver).
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile

class Bus:
    def __init__(self, kit): self.kit = kit; self.x = np.zeros((2, kit.N))
    def add(self, sig, start, gain=1.0, pan=0.0):
        SR, N = self.kit.SR, self.kit.N
        i0 = int(round(start * SR))
        if i0 >= N: return
        if sig.ndim == 1:
            th = (pan + 1) * np.pi / 4
            sig = np.stack([sig * np.cos(th), sig * np.sin(th)]) * np.sqrt(2)
        if i0 < 0: sig, i0 = sig[:, -i0:], 0
        n = min(sig.shape[1], N - i0)
        self.x[:, i0:i0 + n] += gain * sig[:, :n]

class Kit:
    EARLY = .03   # effects land slightly before the picture's contact frame: late reads broken, early reads synced

    def __init__(self, dur, sr=48000, seed=7):
        self.SR, self.dur = sr, dur; self.N = int(sr * dur); self.rng = np.random.default_rng(seed)
        self.t_all = np.arange(self.N) / sr

    # -------- basics
    def bus(self): return Bus(self)
    def ts(self, d): return np.arange(int(d * self.SR)) / self.SR
    def noise(self, d): return self.rng.standard_normal(int(d * self.SR))
    def filt(self, x, kind, f, order=2): return signal.sosfilt(signal.butter(order, f, kind, fs=self.SR, output='sos'), x)
    @staticmethod
    def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
    def vary(self, lo=.9, hi=1.25): return float(lo + (hi - lo) * self.rng.random())   # pitch multiplier for repeats

    def chunked(self, x, fn, f0, f1, chunks=48):
        """Time-varying filter by overlap-adding pre-rolled chunks with an exponential sweep f0 -> f1."""
        n = x.shape[-1]; hop = max(1, n // chunks); win = np.hanning(2 * hop); out = np.zeros_like(x)
        for c in range(-1, chunks + 1):
            a = c * hop; a0, b0 = max(0, a), min(n, a + 2 * hop)
            if b0 <= a0: continue
            pre = max(0, a0 - hop); f = f0 * (f1 / f0) ** min(1, max(0, (c + 1) / chunks))
            out[..., a0:b0] += fn(x[..., pre:b0], f)[..., a0 - pre:] * win[a0 - a:b0 - a]
        return out
    def swept_noise(self, d, f0, f1, envf, q=1.4):
        y = self.chunked(self.noise(d), lambda s, f: self.filt(s, 'bandpass', [f / (1 + 1 / q), min(f * (1 + 1 / q), self.SR / 2 - 100)]), f0, f1)
        return y * envf(np.arange(len(y)) / len(y))

    # -------- drums
    def kick(self, level=1.0, tail=.2):
        t = self.ts(.5); f = 45 + 130 * np.exp(-t / .025); ph = 2 * np.pi * np.cumsum(f) / self.SR
        return level * (np.sin(ph) * np.exp(-t / tail) + np.tanh(3.5 * np.sin(ph)) * np.exp(-t / .045) * .35 + self.filt(self.noise(.5), 'highpass', 3500) * np.exp(-t / .003) * .3)
    def hat(self, open_=False, bright=8000):
        t = self.ts(.3); return self.filt(self.noise(.3), 'highpass', bright, 4) * np.exp(-t / (.1 if open_ else .018))
    def clap(self):
        t = self.ts(.45); n = self.filt(self.noise(.45), 'bandpass', [900, 3600])
        return n * (sum(np.where(t >= o, np.exp(-(t - o) / .006), 0) for o in (0, .01, .021)) * .7 + np.where(t >= .026, np.exp(-(t - .026) / .13), 0))
    def snare(self, level=1.0):
        t = self.ts(.3); body = np.sin(2 * np.pi * np.cumsum(200 * np.exp(-t / .03) + 175) / self.SR) * np.exp(-t / .06)
        return level * (body * .6 + self.filt(self.noise(.3), 'bandpass', [1500, 7500]) * np.exp(-t / .08))

    # -------- tonal
    def saw(self, f, t, detune=0.0, nmax=None):
        f = f * 2 ** (detune / 1200); nmax = nmax or int(min(60, 9000 // f)); x = np.zeros_like(t)
        for n in range(1, nmax + 1): x += np.sin(2 * np.pi * n * f * t + n * 1.7) / n
        return x
    def pad(self, notes, d, cutoff, attack=.05, release=.3, width=1.0):
        t = self.ts(d + release); L = np.zeros_like(t); R = np.zeros_like(t)
        for m in notes:
            for dt in (-11, 0, 11):
                L += self.saw(self.hz(m), t, dt - 4 * width); R += self.saw(self.hz(m), t, dt + 4 * width)
        e = np.minimum(1, t / attack) * np.where(t > d, np.exp(-(t - d) / (release / 3)), 1)
        return np.stack([self.filt(L, 'lowpass', cutoff), self.filt(R, 'lowpass', cutoff)]) * e / (3 * len(notes))
    def pluck(self, f, d=.5, bright=1.0):
        t = self.ts(d); x = np.zeros_like(t)
        for n in range(1, 16):
            if n * f > 12000: break
            x += np.sin(2 * np.pi * n * f * t) / n * np.exp(-t * (4 + n * 3 / bright))
        return x * np.minimum(1, t / .002)
    def epiano(self, f, d=.6):
        t = self.ts(d); x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + 2.5 * k)) / k ** 1.4 for k in (1, 2, 3, 4))
        return x * np.minimum(1, t / .003) * (1 + .3 * np.sin(2 * np.pi * 5 * t))
    def bassnote(self, m, d):
        t = self.ts(d + .03); x = self.saw(self.hz(m), t, 0, 24) * .6 + np.sin(2 * np.pi * self.hz(m) * t)
        e = np.minimum(1, t / .004) * np.where(t > d, np.exp(-(t - d) / .01), 1) * np.exp(-t / .6)
        return self.filt(np.tanh(1.6 * x) * e, 'lowpass', 1000)
    def organ(self, notes, d, attack=.7, release=1.2, cutoff=5200):
        t = self.ts(d + release); L = np.zeros_like(t); R = np.zeros_like(t)
        for m in notes:
            f = self.hz(m)
            for mult, amp in ((.5, .45), (1, 1), (2, .6), (3, .32), (4, .28), (6, .1), (8, .08)):
                if f * mult > 9000: continue
                ph = self.rng.random() * 6.28
                L += amp * np.sin(2 * np.pi * f * mult * 2 ** (-3 / 1200) * t + ph)
                R += amp * np.sin(2 * np.pi * f * mult * 2 ** (3 / 1200) * t + ph + .7)
        e = np.minimum(1, t / attack) * np.where(t > d, np.exp(-(t - d) / (release / 3)), 1) * (1 + .03 * np.sin(2 * np.pi * 5.2 * t))
        return np.stack([self.filt(L, 'lowpass', cutoff), self.filt(R, 'lowpass', cutoff)]) * e / (4 * len(notes))

    # -------- effects
    def click(self, pitch=1.0, d=.06):
        t = self.ts(d); return self.filt(self.noise(d), 'bandpass', [1800 * pitch, min(6500 * pitch, 20000)]) * np.exp(-t / .006) + np.sin(2 * np.pi * 210 * pitch * t) * np.exp(-t / .012) * .6
    def blip(self, f, d=.06, decay=.015):
        t = self.ts(d); return np.sin(2 * np.pi * f * t) * np.exp(-t / decay) * np.minimum(1, t / .001)
    def tick(self, pitch=1.0):
        t = self.ts(.06); return self.filt(self.noise(.06), 'bandpass', [2400, 6500]) * np.exp(-t / .004) + .45 * np.sin(2 * np.pi * 1350 * pitch * t) * np.exp(-t / .012)
    def thump(self, f=100, d=.9):
        t = self.ts(d); x = np.sin(2 * np.pi * np.cumsum(f * np.exp(-t / .025) + 55) / self.SR) * np.exp(-t / .14)
        return np.tanh(1.5 * (x + self.filt(self.noise(d), 'bandpass', [900, 4800]) * np.exp(-t / .006) * .6))
    def impact(self, d=2.4, sub=32, weight=1.0):
        t = self.ts(d); boom = np.sin(2 * np.pi * np.cumsum(sub + 85 * np.exp(-t / .09)) / self.SR) * np.exp(-t / .7); boom += .45 * np.tanh(3 * boom)
        return (boom + self.filt(self.noise(d), 'highpass', 1800) * np.exp(-t / .05) * .9 + self.filt(self.noise(d), 'bandpass', [80, 700]) * np.exp(-t / .18) * .7) * weight
    def whoosh(self, d, f0, f1, peak=.6, q=1.2):
        return self.swept_noise(d, f0, f1, lambda p: np.sin(np.pi * np.clip(p / peak, 0, 1) / 2) ** 2 * np.clip((1 - p) / (1 - peak), 0, 1) ** 1.5, q)
    def reverse_swell(self, d, lp=7000):
        t = self.ts(d); x = self.filt(self.noise(d), 'lowpass', lp) * np.exp(-(d - t) / (d / 3.2)); return np.stack([x, np.roll(x, 300)])
    def zipper(self, d=.3, opening=True):
        t = self.ts(d); p = t / d
        rate = 70 + 110 * np.sin(np.pi * (p if opening else 1 - p) ** .8)
        clicks = (np.diff(np.floor(np.cumsum(rate) / self.SR), prepend=0) > 0).astype(float)
        body = signal.lfilter([1], [1, -.93], clicks) * self.filt(self.noise(d), 'bandpass', [1800, 7000]) * 3
        return (body + self.filt(self.noise(d), 'bandpass', [2500, 9000]) * .35) * np.sin(np.pi * p) ** .6
    def shepard(self, d, base=40.0, octaves=7, rate=.55):
        t = self.ts(d); x = np.zeros_like(t)
        for k in range(octaves):
            pos = (k + rate * t) % octaves
            x += np.exp(-((pos - octaves / 2) / (octaves / 4.5)) ** 2) * np.sin(2 * np.pi * np.cumsum(base * 2 ** pos) / self.SR)
        return x / 3
    def horn(self, d=2.4, root=38):
        """The 'BRAAM' under a title card: detuned brass-ish saws on root/fifth/octave plus a sub."""
        t = self.ts(d); x = np.zeros_like(t)
        for m in (root, root + 7, root + 12):
            for dt in (-9, 0, 9): x += self.saw(self.hz(m), t, dt, 40)
        blat = np.stack([self.filt(x, 'lowpass', 1500), self.filt(np.roll(x, 90), 'lowpass', 1500)])
        blat = np.tanh(1.8 * blat / 4) * (np.minimum(1, t / .05) * np.exp(-t / 1.0))
        return blat + .9 * np.sin(2 * np.pi * self.hz(root - 12) * t) * np.minimum(1, t / .03) * np.exp(-t / 1.2)

    # -------- processing
    def reverb_ir(self, d=3.0, decay=.85, lp=6500):
        t = self.ts(d); ir = np.stack([self.filt(self.noise(d), 'lowpass', lp), self.filt(self.noise(d), 'lowpass', lp)]) * np.exp(-t / decay)
        ir[:, :int(.015 * self.SR)] *= np.linspace(0, 1, int(.015 * self.SR))
        return ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    def reverb(self, x, ir=None):
        ir = self.reverb_ir() if ir is None else ir
        return np.stack([signal.fftconvolve(x[0] + x[1] * .3, ir[0])[:self.N], signal.fftconvolve(x[1] + x[0] * .3, ir[1])[:self.N]])
    def openness(self, spans, ramp=.02):
        """0/1 curve over the film: 1 inside spans [(t0, t1), ...] (the camera is exposed), smoothed by ramp seconds."""
        o = np.zeros(self.N)
        for a, b in spans: o[int(a * self.SR):int(b * self.SR)] = 1
        k = max(1, int(ramp * self.SR)); return np.convolve(o, np.ones(k) / k, mode='same')
    def perspective(self, x, openness, cutoff=330, closed_gain=.42):
        """Heard from where the camera is: full band when open, a lowpassed thump when closed (inside a bag, behind a door)."""
        muffled = np.stack([self.filt(x[0], 'lowpass', cutoff, 4), self.filt(x[1], 'lowpass', cutoff, 4)]) * closed_gain
        return x * openness + muffled * (1 - openness)
    def tape_stop(self, x, t0, t1, power=1.6):
        """Playback speed falls from 1 to 0 between t0 and t1 (something falling asleep); silence after."""
        i0, i1 = int(t0 * self.SR), int(t1 * self.SR); pos = i0 + np.cumsum(np.linspace(1, 0, i1 - i0) ** power); out = x.copy()
        for c in range(2): out[c, i0:i1] = np.interp(pos, np.arange(x.shape[1]), x[c])
        out[:, i1:] = 0; return out
    def sidechain(self, times, depth=.45, release=.08):
        duck = np.ones(self.N)
        for tb in times:
            j = int(tb * self.SR); e = 1 - depth * np.exp(-self.ts(.3) / release); n = min(len(e), self.N - j)
            if n > 0: duck[j:j + n] = np.minimum(duck[j:j + n], e[:n])
        return duck
    def hard_cut(self, x, t):
        """Everything stops at t (a 4 ms ramp so it doesn't click). Add post-cut sounds after this."""
        c0 = int(t * self.SR); cut = np.ones(self.N); cut[c0:] = 0; cut[max(0, c0 - int(.004 * self.SR)):c0] = np.linspace(1, 0, min(c0, int(.004 * self.SR)))
        return x * cut
    def finish(self, mix, path, fade=.8, headroom=1.7, sections=()):
        """High-pass, DC, fade out, soft-limit, write 16-bit WAV. Final loudness is set by mux.py (two-pass loudnorm)."""
        mix = self.filt(mix, 'highpass', 28); mix -= mix.mean(axis=1, keepdims=True)
        nf = int(fade * self.SR); mix[:, -nf:] *= np.linspace(1, 0, nf) ** 2
        mix /= np.abs(mix).max() / headroom; mix = np.tanh(mix) / np.tanh(headroom) * 10 ** (-1 / 20)
        for a, b, name in sections:
            s = mix[:, int(a * self.SR):int(b * self.SR)]
            print(f'{name:10s} rms {20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9):6.1f} dB  peak {20 * np.log10(np.abs(s).max() + 1e-9):5.1f}')
        wavfile.write(path, self.SR, (mix.T * 32767).astype(np.int16))
        return mix

def load_wav(path, kit):
    """Reads a WAV as float stereo (2, n) at the kit's rate (resample it with ffmpeg first if it differs)."""
    sr, x = wavfile.read(path); x = x.astype(np.float64)
    x = x / (32768 if np.abs(x).max() > 1.5 else 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    return x.T
