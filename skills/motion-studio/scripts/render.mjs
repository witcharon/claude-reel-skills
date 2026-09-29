// Frame-exact renderer: serves the film folder, drives window.renderAt(t) in headless Chromium and pipes frames to ffmpeg.
// Motion blur: --sub N renders N subframes per frame across the shutter and ffmpeg averages them (tmix).
//
//   node render.mjs --root <film dir> --page edit.html --fps 24 --from 0 --to 31.5 --sub 4 --shutter .5 --out out/video.mp4
//   node render.mjs --root <film dir> --stills 1.2,5.5,18.9          -> out/stills/still-<t>.png
//
// Speed: capture is nearly all the cost, so frames are captured through CDP (Page.captureScreenshot, optimizeForSpeed)
// by --workers pages in parallel (default: half the CPU cores, at most 6), each in its own context, and written to
// ffmpeg in order. --capture jpeg is faster still (quality 95) at a tiny cost before the final encode.
// Safety: each capture has a timeout and retries; the encode goes to <out>.partial.mp4 and only becomes <out> after
// ffprobe counts the expected frames. Any failure exits non-zero and leaves no file at <out>.
// Encoder: the Apple Media Engine (h264_videotoolbox, --bitrate 24M) when a test encode proves it works on this machine,
// otherwise libx264 on the CPU. Force one with --encoder videotoolbox | x264.
//
// The page must set window.ready = true when loaded and expose async window.renderAt(t) as a pure function of time.
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
const WORKERS = STILLS ? 1 : Math.max(1, Number(args.workers ?? Math.min(6, Math.floor(os.cpus().length / 2))));
const CAPTURE = !STILLS && args.capture === 'jpeg' ? 'jpeg' : 'png';   // stills are always PNG
const TIMEOUT = Number(args.timeout ?? 90) * 1000, RETRIES = 3;

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

const withTimeout = (p, ms, what) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(`${what} timed out after ${ms / 1000} s`)), ms))]);
const time = { render: 0, capture: 0, encode: 0 };           // summed over workers: where the time goes

async function openWorker(browser) {
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: Number(args.scale ?? 1) });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  page.on('console', m => { if (m.type() === 'error' && !/404/.test(m.text())) console.log('[page]', m.text()); });
  await page.goto(`http://localhost:${server.address().port}/${PAGE}`);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  const cdp = await ctx.newCDPSession(page);
  const shot = async t => {
    for (let attempt = 1; ; attempt++) {
      try {
        const a = performance.now(); await withTimeout(page.evaluate(t => window.renderAt(t), t), TIMEOUT, `renderAt(${t})`);
        const b = performance.now();
        const { data } = await withTimeout(cdp.send('Page.captureScreenshot', {
          format: CAPTURE, ...(CAPTURE === 'jpeg' ? { quality: 95 } : {}), optimizeForSpeed: true, fromSurface: true, captureBeyondViewport: false,
        }), TIMEOUT, `capture at ${t}`);
        time.render += b - a; time.capture += performance.now() - b;
        return Buffer.from(data, 'base64');
      } catch (e) {
        if (attempt >= RETRIES) throw e;
        console.log(`[retry ${attempt}] ${e.message}`);
      }
    }
  };
  return { ctx, shot };
}

let browser, ff, exitCode = 0;
const partial = OUT.replace(/(\.[a-z0-9]+)$/i, '.partial$1');
try {
  browser = await chromium.launch({ executablePath: findChromium(), args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--force-color-profile=srgb'] });
  const workers = await Promise.all(Array.from({ length: WORKERS }, () => openWorker(browser)));

  if (STILLS) {
    const dir = path.join(ROOT, 'out/stills'); fs.mkdirSync(dir, { recursive: true });
    for (const t of STILLS) {
      const buf = await workers[0].shot(t);
      fs.writeFileSync(path.join(dir, `still-${t.toFixed(2)}.png`), buf);
    }
    console.log(`stills -> ${dir}`);
  } else {
    fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.rmSync(partial, { force: true });
    const vf = SUB > 1 ? `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB,` : '';
    ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-i', '-',
      '-vf', `${vf}scale=${VW}:${VH}:flags=lanczos,format=yuv420p`, '-r', String(FPS), ...VCODEC,
      '-movflags', '+faststart', partial], { stdio: ['pipe', 'inherit', 'inherit'] });
    const ffDone = new Promise(r => ff.on('close', code => r(code)));
    let ending = false, failRej;
    const ffEarly = new Promise((_, rej) => ffDone.then(code => { if (!ending) rej(new Error(`ffmpeg exited early (code ${code})`)); }));
    const failP = new Promise((_, rej) => { failRej = rej; });
    ffEarly.catch(() => {}); failP.catch(() => {});
    console.log(`encoder: ${ENCODER} | workers: ${WORKERS} | capture: ${CAPTURE}`);

    const frames = Math.round((TO - FROM) * FPS), t0 = Date.now(), AHEAD = WORKERS * 3;
    const slots = new Map();                                  // frame index -> {promise, resolve, reject}
    const slot = i => { if (!slots.has(i)) { let res, rej; const p = new Promise((a, b) => { res = a; rej = b; }); p.catch(() => {}); slots.set(i, { p, res, rej }); } return slots.get(i); };
    let next = 0, written = 0, failed = null;
    const work = async w => {
      while (!failed) {
        while (next - written > AHEAD && !failed) await new Promise(r => setTimeout(r, 4));   // backpressure on memory
        const i = next++; if (i >= frames) return;
        try {
          const bufs = [];
          for (let j = 0; j < SUB; j++) bufs.push(await w.shot(FROM + (i + (SUB > 1 ? j / SUB * SHUTTER : 0)) / FPS));
          slot(i).res(bufs);
        } catch (e) { failed = e; slot(i).rej(e); failRej(e); }
      }
    };
    const running = workers.map(work);
    for (let i = 0; i < frames; i++) {
      const bufs = await Promise.race([slot(i).p, ffEarly, failP]);
      slots.delete(i);
      const c = performance.now();
      for (const buf of bufs) if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      time.encode += performance.now() - c; written++;
      if (i % FPS === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / (i + 1) / 1000).toFixed(2)} s/frame`);
    }
    await Promise.all(running);
    ending = true; const f0 = performance.now(); ff.stdin.end(); const code = await ffDone; time.encode += performance.now() - f0;
    if (code !== 0) throw new Error(`ffmpeg exited with code ${code}`);
    // the file must hold every frame before it gets the real name
    const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', partial], { encoding: 'utf8' });
    const got = parseInt(probe.stdout, 10);
    if (got !== frames) throw new Error(`encoded ${got} frames, expected ${frames}`);
    fs.renameSync(partial, OUT);
    const wall = (Date.now() - t0) / 1000, busy = v => `${(v / 1000).toFixed(0)} s`;
    console.log(`video -> ${OUT} (${frames} frames, ${(frames / FPS).toFixed(2)} s)`);
    console.log(`time: ${wall.toFixed(1)} s wall, ${(wall / frames).toFixed(2)} s/frame (${SUB} subframes, ${WORKERS} workers) | worker time: page render ${busy(time.render)}, capture ${busy(time.capture)} | writing to encoder ${busy(time.encode)} | encoder ${ENCODER}`);
  }
} catch (e) {
  exitCode = 1;
  console.error(`render failed: ${e.message}`);
  if (ff && ff.exitCode === null) ff.kill('SIGKILL');
  fs.rmSync(partial, { force: true });
} finally {
  if (browser) await browser.close().catch(() => {});
  server.close();
}
process.exit(exitCode);
