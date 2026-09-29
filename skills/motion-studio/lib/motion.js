// motion.js: the motion vocabulary for seek(t) films. Every function is a pure function of time:
// no timers, no CSS transitions, no state carried between frames, so any frame can be rendered alone.
// Springs follow the closed-form approach from Movez's Opus 5.5 motion-design course; the seam and cascade
// helpers adapt ideas from HyperFrames' motion doctrine (Apache-2.0) and claude-animation (MIT).

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const ease = {
  out3: k => 1 - Math.pow(1 - clamp(k), 3),
  in3: k => Math.pow(clamp(k), 3),
  inOut3: k => (k = clamp(k)) < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
  outExpo: k => (k = clamp(k)) >= 1 ? 1 : 1 - Math.pow(2, -10 * k),
  power4In: k => Math.pow(clamp(k), 4),            // exit side of a velocity-matched seam
  power4Out: k => 1 - Math.pow(1 - clamp(k), 4),   // entry side
};

// ---------------------------------------------------------------- springs
/** Closed-form damped spring from 0 to 1 at time t (seconds since it started). Pure: no simulation. */
export function spring(t, k = 170, d = 26) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(k), z = d / (2 * w0);
  if (z < 1) {
    const wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
  }
  return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
}
/** Presets by what moves. UI may overshoot a hair; type never does; playful things visibly bounce. */
export const SPRING = {
  snappy: [320, 30],   // buttons, toggles, leading edges, carets
  ui: [220, 24],       // chips, notifications, pills (tiny overshoot)
  base: [170, 26],     // cards, containers, camera
  type: [150, 26],     // big type: critically damped, no overshoot
  heavy: [90, 20],     // logo lockups, huge words landing
  playful: [260, 14],  // stickers, mascots (visible bounce)
};
export const springP = (t, preset = 'base') => spring(t, ...SPRING[preset]);

/**
 * A value with several targets over time: [[t0, v0], [t1, v1], ...]. Each change adds its own spring
 * starting at its own time, so motion stays continuous and frame N never needs frames 0..N-1.
 */
export function track(t, keys, preset = 'base') {
  let v = keys[0][1];
  for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * springP(t - keys[i][0], preset);
  return v;
}

/** Snap, then hold: the change happens in ~2 frames and then sits still. Reads as intentional. */
export const snap = (t, t0, dur = .07) => ease.power4Out((t - t0) / dur);

/** Seconds of delay for the i-th item of a cascade. Heavier items get a longer step. */
export const stagger = (i, step = .06) => i * step;

// ---------------------------------------------------------------- kinetic type
/**
 * Entry of one word/element: rises into place on a spring, sharpens from blur, no overshoot on type.
 * Returns style numbers; the caller turns them into CSS.
 */
export function wordIn(t, at, { preset = 'type', rise = 42, fromScale = 1.18, blur = 14 } = {}) {
  const s = springP(t - at, preset), p = clamp((t - at) / .12);
  return { opacity: p, y: (1 - s) * rise, scale: lerp(fromScale, 1, s), blur: (1 - clamp(s * 1.25)) * blur };
}
/** Exit: accelerate away (power4 in) so a following cut lands on peak velocity, never on a settled frame. */
export function wordOut(t, out, { dur = .16, lift = -30, toScale = 1.08, blur = 12 } = {}) {
  const p = ease.power4In((t - out) / dur);
  return { opacity: 1 - p, y: p * lift, scale: lerp(1, toScale, p), blur: p * blur };
}
export const css = (el, s) => Object.assign(el.style, s);
export const styleOf = ({ opacity, y = 0, x = 0, scale = 1, blur = 0 }) => ({
  opacity, transform: `translate(${x}px,${y}px) scale(${scale})`, filter: blur > .05 ? `blur(${blur}px)` : 'none',
});

/**
 * Binds every `.title` under root. Markup: <div class="title" data-out="2.2"><span class="w" data-at=".3">pov:</span> …</div>
 * Optional data-preset (type|heavy|ui), data-punch="<t>" for a hit on a beat. Returns draw(t).
 */
export function bindTitles(root = document) {
  const titles = [...root.querySelectorAll('.title')].map(el => ({
    el, out: +el.dataset.out, punch: el.dataset.punch ? +el.dataset.punch : null, preset: el.dataset.preset || 'type',
    words: [...el.querySelectorAll('.w')].map(w => ({ el: w, at: +w.dataset.at })),
  }));
  return t => {
    for (const ti of titles) {
      const vis = t >= ti.words[0].at - .01 && t < ti.out + .2;
      ti.el.style.display = vis ? 'block' : 'none';
      if (!vis) continue;
      const o = t >= ti.out ? wordOut(t, ti.out) : { opacity: 1, y: 0, scale: 1, blur: 0 };
      const pun = ti.punch !== null && t >= ti.punch ? 1 + .05 * (1 - springP(t - ti.punch, 'snappy')) * (t - ti.punch < .02 ? 0 : 1) : 1;
      css(ti.el, styleOf({ ...o, scale: o.scale * pun }));
      for (const w of ti.words) css(w.el, styleOf(wordIn(t, w.at, { preset: ti.preset })));
    }
  };
}

// ---------------------------------------------------------------- seams and group motion
/**
 * Nudge curve for moving a group from A to B without a cut: slow start, fast middle, slow settle
 * (roughly 10% / 65% / 25% of the duration). Returns 0..1.
 */
export function nudge(t, t0, dur) {
  const p = clamp((t - t0) / dur);
  if (p < .1) return .03 * ease.in3(p / .1);
  if (p < .75) return .03 + .87 * ((p - .1) / .65);
  return .9 + .1 * ease.out3((p - .75) / .25);
}
/**
 * Velocity-matched seam: exit uses power4-in, entry power4-out over the same distance and duration, so
 * the incoming side starts at the speed the outgoing side left with. Returns {exit, entry} progress 0..1.
 */
export function seam(t, cut, dur = .22) {
  return { exit: ease.power4In((t - (cut - dur)) / dur), entry: ease.power4Out((t - cut) / dur) };
}

// ---------------------------------------------------------------- utilities
/** Seeded PRNG (mulberry32). Never Math.random in a film. */
export function rng(seed) {
  return () => {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
/** Deterministic hash of a number to 0..1. */
export const hash = s => { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

/** Camera shake from impulses [[t, strength px, decay s], ...]; stepped at 2x fps so it reads as a camera. */
export function shake(t, hits, fps = 24) {
  let x = 0, y = 0, r = 0;
  for (const [ti, a, d] of hits) {
    if (t < ti || t > ti + 6 * d) continue;
    const k = Math.exp(-(t - ti) / d) * a, f = Math.floor(t * fps * 2);
    x += (hash(f + ti) - .5) * 2 * k; y += (hash(f * 1.7 + ti) - .5) * 2 * k; r += (hash(f * 2.3 + ti) - .5) * k * .03;
  }
  return { x, y, r };
}

/** 3x3 homography (h22 = 1) mapping four src points to four dst points. */
export function homography(src, dst) {
  const A = [], b = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = src[i], [u, v] = dst[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
  }
  for (let c = 0; c < 8; c++) {
    let p = c; for (let r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
    for (let r = 0; r < 8; r++) if (r !== c) { const f = A[r][c] / A[c][c]; for (let k = c; k < 8; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; }
  }
  const h = b.map((v, i) => v / A[i][i]);
  return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1]];
}
/** CSS matrix3d for an element with transform-origin 0 0 so its box maps onto the quad. */
export const matrix3d = H => `matrix3d(${H[0][0]},${H[1][0]},0,${H[2][0]},${H[0][1]},${H[1][1]},0,${H[2][1]},0,0,1,0,${H[0][2]},${H[1][2]},0,${H[2][2]})`;

/** Film grain into a small canvas (upscaled by CSS); seeded per frame. */
export function grain(canvas, n, amount = 190) {
  const g = canvas.getContext('2d'), img = g.createImageData(canvas.width, canvas.height), d = img.data;
  let s = (n * 9301 + 49297) % 233280;
  for (let i = 0; i < d.length; i += 4) { s = (s * 9301 + 49297) % 233280; const v = 128 + (s / 233280 - .5) * amount; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
  g.putImageData(img, 0, 0);
}

/** Loads an image once per src and waits for decode (use inside an async renderAt). */
export async function setImg(img, src) {
  if (img.dataset.src !== src) { img.dataset.src = src; img.src = src; await img.decode(); }
}

/** Reels/TikTok safe area on 1080x1920: text stays inside; centre on the frame, not on the safe column. */
export const SAFE = { top: 250, bottom: 1440, buttonBand: [880, 1600], left: 190, right: 890, cx: 540 };

/** Plate index for time t. Floor, not round: motion-blur subframes of one frame must share its plate. */
export const plateIndex = (t, fps, count) => Math.min(count - 1, Math.max(0, Math.floor(t * fps + 1e-6)));
