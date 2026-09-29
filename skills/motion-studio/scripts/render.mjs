// Frame-exact renderer: serves the film folder, drives window.renderAt(t) in headless Chromium and pipes PNGs to ffmpeg.
// Motion blur: --sub N renders N subframes per frame across the shutter and ffmpeg averages them (tmix).
//
//   node render.mjs --root <film dir> --page edit.html --fps 24 --from 0 --to 31.5 --sub 4 --shutter .5 --out out/video.mp4
//   node render.mjs --root <film dir> --stills 1.2,5.5,18.9          -> out/stills/still-<t>.png
// Encoder: the Apple Media Engine (h264_videotoolbox, --bitrate 24M) when a test encode proves it works on this machine,
// otherwise libx264 on the CPU. Force one with --encoder videotoolbox | x264.
//
// The page must set window.ready = true when loaded and expose async window.renderAt(t).
// Playwright is resolved from the film dir's node_modules (or set NODE_PATH).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';

const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) => {
  if (!a.startsWith('--')) return [];
  const s = a.slice(2), eq = s.indexOf('=');
  if (eq >= 0) return [s.slice(0, eq), s.slice(eq + 1)];
  const next = all[i + 1];
  return [s, next && !next.startsWith('--') ? next : 'true'];
}).filter(p => p.length));
const ROOT = path.resolve(args.root ?? '.');
const PAGE = args.page ?? 'edit.html';
const FPS = Number(args.fps ?? 24), SUB = Math.max(1, Number(args.sub ?? 1)), SHUTTER = Number(args.shutter ?? .5);
const FROM = Number(args.from ?? 0), TO = Number(args.to ?? 10);
const [VW, VH] = (args.size ?? '1080x1920').split('x').map(Number);
const OUT = path.resolve(ROOT, args.out ?? 'out/video.mp4');
const STILLS = args.stills ? String(args.stills).split(',').map(Number) : null;
function pickEncoder() {
  if (args.encoder) return args.encoder;
  if (process.platform !== 'darwin') return 'x264';
  // listed is not enough (Intel Macs without the hardware list it too): do a tiny hardware-only encode
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=256x256:d=0.2',
    '-c:v', 'h264_videotoolbox', '-allow_sw', '0', '-f', 'null', '-'], { timeout: 15000 });
  return r.status === 0 ? 'videotoolbox' : 'x264';
}
const ENCODER = STILLS ? 'none' : pickEncoder();
const VCODEC = ENCODER === 'videotoolbox'
  ? ['-c:v', 'h264_videotoolbox', '-b:v', args.bitrate ?? '24M', '-maxrate', '32M', '-profile:v', 'high', '-allow_sw', '0']
  : ['-c:v', 'libx264', '-preset', 'slow', '-crf', '16'];

const require = createRequire(path.join(ROOT, 'package.json'));
const { chromium } = require('playwright-core');

function findChromium() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const tails = ['chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
                 'chrome-mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing', 'chrome-linux/chrome'];
  if (fs.existsSync(cache)) {
    const dirs = fs.readdirSync(cache).filter(d => /^chromium-\d+$/.test(d)).sort((a, b) => +b.split('-')[1] - +a.split('-')[1]);
    for (const d of dirs) for (const t of tails) { const p = path.join(cache, d, t); if (fs.existsSync(p)) return p; }
  }
  const sys = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  return fs.existsSync(sys) ? sys : undefined;   // undefined: let Playwright try its default
}

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.mp4': 'video/mp4' };
const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));   // decodes non-ASCII folder names
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] ?? 'application/octet-stream' }); res.end(data);
  });
}).listen(0);

const browser = await chromium.launch({ executablePath: findChromium(), args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: VW, height: VH }, deviceScaleFactor: Number(args.scale ?? 1) });
page.on('pageerror', e => console.log('[pageerror]', e.message));
page.on('console', m => { if (m.type() === 'error' && !/404/.test(m.text())) console.log('[page]', m.text()); });
await page.goto(`http://localhost:${server.address().port}/${PAGE}`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
const time = { render: 0, capture: 0, encode: 0 };           // where the wall time goes
const shot = async t => {
  const a = performance.now(); await page.evaluate(t => window.renderAt(t), t);
  const b = performance.now(); const png = await page.screenshot({ type: 'png' });
  time.render += b - a; time.capture += performance.now() - b; return png;
};

if (STILLS) {
  const dir = path.join(ROOT, 'out/stills'); fs.mkdirSync(dir, { recursive: true });
  for (const t of STILLS) fs.writeFileSync(path.join(dir, `still-${t.toFixed(2)}.png`), await shot(t));
  console.log(`stills -> ${dir}`);
} else {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const vf = SUB > 1 ? `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB,` : '';
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-i', '-',
    '-vf', `${vf}scale=${VW}:${VH}:flags=lanczos,format=yuv420p`, '-r', String(FPS), ...VCODEC,
    '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  console.log(`encoder: ${ENCODER}`);
  const frames = Math.round((TO - FROM) * FPS), t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    for (let j = 0; j < SUB; j++) {
      const buf = await shot(FROM + (i + (SUB > 1 ? j / SUB * SHUTTER : 0)) / FPS);
      const c = performance.now();
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      time.encode += performance.now() - c;
    }
    if (i % FPS === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / (i + 1) / 1000).toFixed(2)} s/frame`);
  }
  const f0 = performance.now(); ff.stdin.end(); await new Promise(r => ff.on('close', r)); time.encode += performance.now() - f0;
  const wall = (Date.now() - t0) / 1000, pct = v => `${(v / 10 / wall).toFixed(0)}%`;
  console.log(`video -> ${OUT}`);
  console.log(`time: ${wall.toFixed(1)} s wall, ${(wall / frames).toFixed(2)} s/frame (${SUB} subframes) | page render ${pct(time.render)}, capture ${pct(time.capture)}, waiting on encoder ${pct(time.encode)} | encoder ${ENCODER}`);
}
await browser.close(); server.close();
