// Browser test of the demo at 1440 px and 375 px. Fails on any console error, page error or failed request.
//   PW_CHANNEL=chrome node scripts/e2e.mjs        (needs `playwright`: npm i --no-save playwright)
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { startServer } from './serve.mjs';

const PORT = Number(process.env.E2E_PORT ?? 4394);
const BASE = process.env.E2E_URL ?? `http://127.0.0.1:${PORT}/`;
const server = process.env.E2E_URL ? null : await startServer(PORT);
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined });
const errors = [];
let checks = 0;
const ok = (cond, msg) => {
  assert.ok(cond, msg);
  checks += 1;
};

async function open(width, height, { path = '', ready = true } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height }, locale: 'uz-UZ', timezoneId: 'Asia/Tashkent' });
  await ctx.route('https://telegram.org/**', (route) => route.fulfill({ status: 200, contentType: 'text/javascript', body: '' }));
  await ctx.addInitScript(() => { try { localStorage.setItem('testustasi.lang', 'uz'); } catch { /* */ } });
  const page = await ctx.newPage();
  page.on('console', (m) => m.type() === 'error' && errors.push(`[${width}] ${m.text()}`));
  page.on('pageerror', (e) => errors.push(`[${width}] ${e.message}`));
  page.on('requestfailed', (r) => errors.push(`[${width}] request failed ${r.url()} ${r.failure()?.errorText}`));
  await page.goto(BASE + path);
  if (ready) await page.waitForSelector('body[data-ready="1"]', { timeout: 60_000 });
  return page;
}

const text = (page, sel) => page.evaluate((s) => document.querySelector(s)?.textContent ?? '', sel);
const has = (page, sel, s) => page.waitForFunction(([q, v]) => document.querySelector(q)?.textContent.includes(v), [sel, s], { timeout: 30_000 });
const noScroll = (page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
const done = (page, n) => page.waitForFunction((k) => document.querySelector(`[data-testid=story-${k}]`).classList.contains('done'), n, { timeout: 180_000 });
async function step(page, n) {
  await page.getByTestId(`story-${n}`).click();
  await done(page, n);
}
const N = '[data-testid=nodira-app]';
const J = '[data-testid=jasur-app]';
const chat = (who) => `[data-testid=${who}-chat]`;

async function story(page, mobile) {
  ok((await text(page, '[data-testid=demo-badge]')).includes('brauzeringizda'), 'demo badge');
  if (mobile) ok(await page.getByTestId('nodira-phone').isVisible() && !(await page.getByTestId('jasur-phone').isVisible()), 'one frame at a time');
  else ok(await page.getByTestId('nodira-phone').isVisible() && await page.getByTestId('jasur-phone').isVisible() && await page.getByTestId('try').isVisible(),
    'two phones and the try box at 1440 px');
  ok(await noScroll(page), 'no horizontal scroll');
  ok((await text(page, chat('nodira'))).includes('Sinflar: 1 · testlar: 3'), "Nodira's bot: the teacher's menu");
  ok((await text(page, chat('jasur'))).includes("Jasur Toshpo'latov"), "Jasur's bot: the student's menu");
  await step(page, 1);
  await has(page, chat('nodira'), "11 ta savol (so'ralgani 15 ta edi");
  ok((await text(page, chat('nodira'))).includes('Fotosintez.txt'), 'the file bubble');
  await step(page, 2);
  await has(page, `${N} [data-testid=quote-1]`, 'Matnda:');
  ok(await page.locator(`${N} [data-testid^=quote-]`).count() === 11, 'every question has its quote');
  await step(page, 3);
  await page.waitForFunction((q) => document.querySelectorAll(`${q} [data-testid^=quote-]`).length === 10, N);
  await has(page, `${N} [data-testid=q-6]`, 'Vodorod');
  ok((await text(page, `${N} [data-testid=q-6]`)).includes('tahrirlangan'), 'a question deleted and another edited');
  await step(page, 4);
  await has(page, chat('jasur'), 'Yangi test: Fotosintez');
  ok((await text(page, chat('jasur'))).includes('Muddat: bugun, 23:59'), 'the notification with the deadline');
  await step(page, 5);
  await page.waitForSelector(`${J} [data-testid=solving]`);
  ok((await text(page, `${J} [data-testid=timer]`)).includes(':'), 'the timer');
  await step(page, 6);
  await has(page, `${J} [data-testid=score]`, '7/10');
  ok(await page.locator(`${J} [data-testid^=mistake-]`).count() === 3, 'three mistakes with the correct answers');
  ok((await text(page, `${J} [data-testid=mistakes]`)).includes('Matnda:'), 'and the quotes');
  await step(page, 7);
  await has(page, `${N} [data-testid=stat-done]`, '25/25');
  await has(page, chat('nodira'), 'hamma topshirdi');
  ok(await page.locator(`${N} [data-testid=grade-chart] rect[data-testid^=bar-]`).count() >= 3, 'the grade chart');
  await step(page, 8);
  await has(page, `${N} [data-testid=flag-6]`, "Kuchli o'quvchilar ham xato qildi");
  ok((await text(page, `${N} [data-testid=flag-3]`)).includes('60% «A» variantni tanlagan — mavzuni qayta tushuntiring'), 'question 3: most picked A');
  ok((await text(page, `${N} [data-testid=flag-4]`)).includes('Juda oson'), 'question 4: very easy');
  await step(page, 9);
  await has(page, chat('jasur'), 'Qayta test: Fotosintez');
  ok(true, 'the retest reaches Jasur');
  await step(page, 10);
  await has(page, J, "Xato yo'q — barakalla!");
  ok(true, 'Jasur solves the retest himself, without a mistake');
  await page.waitForSelector(`${N} [data-testid=progress]`);
  const before = Number.parseInt(await text(page, `${N} [data-testid=prog-before]`), 10);
  const after = Number.parseInt(await text(page, `${N} [data-testid=prog-after]`), 10);
  ok(after - before >= 25, `the class's score on those topics rises: ${before}% → ${after}%`);
  ok((await text(page, '[data-testid=story-caption]')).includes(`${before}% → ${after}%`), 'the caption says the same numbers');
  ok(await noScroll(page), 'still no horizontal scroll');
}

async function more(page) {
  await page.getByTestId('try-ex-orol').click();
  await has(page, '[data-testid=try-out]', 'Matnda:');
  ok((await text(page, '[data-testid=try-q-1]')).length > 20, 'the try box makes questions from another text');
  await page.getByTestId('try-input').fill('Qisqa matn.');
  await has(page, '[data-testid=try-out]', '150 belgi');
  ok(true, 'and says when the text is too short');
  await page.getByTestId('demo-lang').click();
  await has(page, '[data-testid=demo-badge]', 'браузере');
  await has(page, `${N} [data-testid=app-back]`, 'Назад');
  ok(true, 'Russian switch');
}

async function outOfOrder() {
  const page = await open(1440, 900);
  await page.getByTestId('story-8').click();
  await done(page, 8);
  ok(await page.evaluate(() => [...document.querySelectorAll('.story-btn.done')].length) === 8, 'step 8 first: the earlier steps happen quietly');
  await has(page, `${N} [data-testid=flag-6]`, "Kuchli o'quvchilar ham xato qildi");
  ok(true, 'and the analysis is there');
  await page.context().close();
}

try {
  for (const [w, h] of [[1440, 900], [375, 812]]) {
    const page = await open(w, h);
    await story(page, w < 760);
    if (w > 760) await more(page);
    await page.context().close();
  }
  await outOfOrder();
  const outside = await open(375, 700, { path: 'webapp/index.html', ready: false });
  await has(outside, '#app', 'Telegram ichida');
  ok(true, 'the Mini App outside Telegram asks to open it in Telegram');
  await outside.context().close();
  assert.deepEqual(errors, [], `console errors:\n${errors.join('\n')}`);
  console.log(`e2e: ${checks} checks passed at 1440 px and 375 px, 0 console errors`); // eslint-disable-line no-console
} finally {
  await browser.close();
  server?.close();
}
