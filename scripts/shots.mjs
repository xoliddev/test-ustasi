// README media from the real demo: desktop + phone screenshots (JPEG), an 800x500 portfolio thumbnail and a GIF from a
// pasted text to the draft with quotes, a student solving, and the analysis of wrong answers. JPEG is encoded by the
// browser (canvas), the GIF by gifenc.
//   PW_CHANNEL=chrome node scripts/shots.mjs [outDir]       (needs playwright + gifenc)
import { mkdirSync, writeFileSync } from 'node:fs';
import gifenc from 'gifenc';
import { chromium } from 'playwright';
import { startServer } from './serve.mjs';
import { thumb } from './thumb.mjs';

const { GIFEncoder, quantize, applyPalette } = gifenc;
const OUT = process.argv[2] ?? 'docs/media';
const PORT = Number(process.env.SHOTS_PORT ?? 4396);
mkdirSync(OUT, { recursive: true });
const server = await startServer(PORT);
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined });
const b64 = (buf) => buf.toString('base64');
const ONLY = new Set((process.env.ONLY ?? 'desktop,thumb,mobile,gif').split(','));

async function open(width, height) {
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, timezoneId: 'Asia/Tashkent' });
  await ctx.route('https://telegram.org/**', (route) => route.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
  await ctx.addInitScript(() => { try { localStorage.setItem('testustasi.lang', 'uz'); } catch { /* */ } });
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:${PORT}/`);
  await page.waitForSelector('body[data-ready="1"]');
  return page;
}
const done = (page, n) => page.waitForFunction((k) => document.querySelector(`[data-testid=story-${k}]`).classList.contains('done'), n, { timeout: 120_000 });
const step = async (page, n) => { await page.evaluate((k) => document.querySelector(`[data-testid=story-${k}]`).click(), n); await done(page, n); };
const toStage = (page, gap = 40) => page.evaluate((g) => {
  const top = document.querySelector('[data-testid=nodira-phone]').getBoundingClientRect().top + window.scrollY;
  window.scrollTo(0, top - g);
}, gap);
/** Scroll a phone's Mini App so ``sel`` is near the top. */
const appTo = (page, who, sel, gap = 12) => page.evaluate(([w, s, g]) => {
  const body = document.querySelector(`[data-testid=${w}-app] .u-body`);
  const el = document.querySelector(`[data-testid=${w}-app] ${s}`);
  if (body && el) body.scrollTop += el.getBoundingClientRect().top - body.getBoundingClientRect().top - g;
}, [who, sel, gap]);

async function jpeg(page, png, name, w, h) {
  const out = await page.evaluate(async ([src, W, H]) => {
    const img = new Image();
    img.src = `data:image/png;base64,${src}`;
    await img.decode();
    const cv = document.createElement('canvas');
    cv.width = W;
    cv.height = H;
    const g = cv.getContext('2d');
    g.imageSmoothingQuality = 'high';
    g.drawImage(img, 0, 0, W, H);
    return cv.toDataURL('image/jpeg', 0.88).split(',')[1];
  }, [b64(png), w, h]);
  writeFileSync(`${OUT}/${name}`, Buffer.from(out, 'base64'));
  console.log('wrote', name); // eslint-disable-line no-console
}

if (ONLY.has('desktop') || ONLY.has('thumb')) {
  const page = await open(1440, 900);
  await step(page, 6);
  await page.waitForTimeout(900);
  await appTo(page, 'jasur', '[data-testid=mistakes]', 4);
  await page.waitForTimeout(400);
  const jasur = await page.getByTestId('jasur-phone').screenshot();
  await step(page, 7);
  await page.waitForTimeout(800);
  if (ONLY.has('desktop')) {
    await toStage(page, 92);
    await page.waitForTimeout(300);
    await jpeg(page, await page.screenshot(), 'demo-desktop.jpg', 1440, 900);
  }
  if (ONLY.has('thumb')) {
    await step(page, 8);
    await page.waitForTimeout(600);
    await appTo(page, 'nodira', '[data-testid=aq-6]', 6);
    await page.waitForTimeout(500);
    const nodira = await page.getByTestId('nodira-phone').screenshot();
    writeFileSync(`${OUT}/thumb.jpg`, Buffer.from(await thumb(page, jasur, nodira), 'base64'));
    console.log('wrote thumb.jpg'); // eslint-disable-line no-console
  }
  await page.context().close();
}

if (ONLY.has('mobile')) {
  const page = await open(390, 844);
  await step(page, 8);
  await page.getByTestId('switch-nodira').click();
  await toStage(page, 50);
  await page.waitForTimeout(800);
  await appTo(page, 'nodira', '[data-testid=aq-3]', 6);
  await page.waitForTimeout(500);
  await jpeg(page, await page.screenshot(), 'demo-mobile.jpg', 390, 844);
  await page.context().close();
}

if (ONLY.has('gif')) {
  const page = await open(1360, 860);
  await toStage(page, 4);
  const clip = await page.evaluate(() => {
    const a = document.querySelector('[data-testid=nodira-phone]').getBoundingClientRect();
    const c = document.querySelector('[data-testid=jasur-phone]').getBoundingClientRect();
    return { x: Math.max(0, a.left - 6), y: Math.max(0, a.top - 4), width: c.right - a.left + 12, height: Math.min(window.innerHeight - a.top - 4, a.height + 8) };
  });
  const W = 560;
  const H = Math.round((W * clip.height) / clip.width / 2) * 2;
  const gif = GIFEncoder();
  async function frame(delay) {
    const png = await page.screenshot({ clip });
    const rgba = await page.evaluate(async ([src, w, h]) => {
      const img = new Image();
      img.src = `data:image/png;base64,${src}`;
      await img.decode();
      const c = document.createElement('canvas');
      c.width = w;
      c.height = h;
      const g = c.getContext('2d');
      g.imageSmoothingQuality = 'high';
      g.drawImage(img, 0, 0, w, h);
      const bytes = g.getImageData(0, 0, w, h).data;
      let bin = '';
      for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
      return btoa(bin);
    }, [b64(png), W, H]);
    const data = new Uint8Array(Buffer.from(rgba, 'base64'));
    const palette = quantize(data, 96);
    gif.writeFrame(applyPalette(data, palette), W, H, { palette, delay });
  }
  async function film(n, every = 1100, max = 16) {
    await page.evaluate((k) => document.querySelector(`[data-testid=story-${k}]`).click(), n);
    for (let k = 0; k < max; k++) {
      await frame(every);
      if (await page.evaluate((s) => document.querySelector(`[data-testid=story-${s}]`).classList.contains('done'), n)) break;
      await page.waitForTimeout(every - 250);
    }
  }
  await frame(1200);
  for (const n of [1, 2, 5, 6, 8]) await film(n);
  await frame(3600);
  gif.finish();
  writeFileSync(`${OUT}/matn-test-tahlil.gif`, gif.bytes());
  console.log('wrote matn-test-tahlil.gif'); // eslint-disable-line no-console
  await page.context().close();
}
await browser.close();
server.close();
