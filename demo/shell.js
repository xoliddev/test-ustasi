// Demo page: Nodira ustoz's phone (the bot and the Mini App), Jasur's phone (the bot and the Mini App) and the
// "O'zingiz sinab ko'ring" box, all on the in-page backend; the guided story (in order, all at once, or out of order)
// with a caption for every step, the demo clock, the language switch. On narrow screens one frame at a time.
import { localDay, localMinute } from '../shared/clock.js';
import { dateText, makeT } from '../shared/i18n.js';
import { mountApp, routeFrom } from '../webapp/ui.js';
import { h, loadShared, makeText, store } from '../webapp/util.js';
import { apiFor } from './api.js';
import { BotSim } from './bot.js';
import { makeViews } from './bot-views.js';
import { createPhone, MARK } from './phone.js';
import { createDemo, JASUR, NODIRA } from './seed.js';
import { captionParams, runStep, STEPS } from './story.js';
import { makeUi } from './story-ui.js';
import { createTry } from './try.js';

const shared = await loadShared(new URL('../shared/', import.meta.url), true);
const t = makeT(shared.catalogs);
const T = makeText(shared.catalogs);
let lang = store.get('testustasi.lang') === 'ru' ? 'ru' : 'uz';
const P = (key, params) => T(lang, key, params);
const backend = createDemo({ data: shared, lang });
const views = makeViews(t);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const WHO = { [NODIRA]: 'nodira', [JASUR]: 'jasur' };
const phones = {};
const bots = {};
const apps = {};

const narrow = () => window.matchMedia('(max-width: 760px)').matches;
function focus(uid, pane) {
  phones[uid].show(pane);
  if (narrow()) pick(WHO[uid]);
}

async function downloadCsv(uid, tid) {
  const out = await apiFor(backend, uid, t).csv(tid);
  const a = h('a', { href: URL.createObjectURL(new Blob([out.csv], { type: 'text/csv;charset=utf-8' })), download: out.name });
  document.body.append(a);
  a.click();
  a.remove();
}

for (const uid of [NODIRA, JASUR]) {
  bots[uid] = new BotSim(backend, uid, t, views, { onChange: () => phones[uid]?.renderChat(), onAlert: (x) => phones[uid]?.alert(x), onFile: (tid) => downloadCsv(uid, tid) });
  bots[uid].onLangChange = (l) => setLang(l);
  phones[uid] = createPhone({ who: WHO[uid], bot: bots[uid], texts: { P }, now: () => backend.nowMs(),
    onOpenApp: (where) => { focus(uid, 'app'); const r = routeFrom(where ?? ''); if (r) apps[uid].open(r); else apps[uid].home(); },
    onShowApp: () => apps[uid]?.refresh() });
  apps[uid] = mountApp(phones[uid].appRoot, { catalogs: shared.catalogs, api: apiFor(backend, uid, t), lang, now: () => backend.nowMs(), onLang: (l) => setLang(l) });
}
const tryBox = createTry({ P, texts: shared.texts });

let pending = false;
backend.on((ev) => {
  if (ev.type === 'note') {
    const msg = bots[ev.note.to]?.deliver(ev.note);
    if (msg && phones[ev.note.to]) phones[ev.note.to].ping(msg.html);
  }
  if (ev.type === 'changed' && !pending) {
    pending = true;
    queueMicrotask(async () => {
      pending = false;
      await Promise.all([NODIRA, JASUR].map((uid) => apps[uid].refresh().catch((e) => console.warn(e)))); // eslint-disable-line no-console
      paintClock();
      paintStory();
    });
  }
});

// ── page ──
const timeEl = h('span', { class: 'demo-date', 'data-testid': 'demo-time' });
const badgeText = h('span');
const langBtn = h('button', { class: 'demo-btn', type: 'button', 'data-testid': 'demo-lang', onclick: () => setLang(lang === 'uz' ? 'ru' : 'uz') });
const page = `${window.location.origin}${window.location.pathname.replace(/index\.html$/, '')}`;
const resetBtn = h('button', { class: 'demo-btn', type: 'button', onclick: () => window.location.assign(page) });
const playBtn = h('button', { class: 'demo-btn solid', type: 'button', 'data-testid': 'play', onclick: () => play() });
const bar = h('header', { class: 'demo-bar' },
  h('a', { class: 'demo-logo', href: page }, h('span', { class: 'demo-mark', html: MARK }), 'Test Ustasi'),
  h('span', { class: 'demo-badge', 'data-testid': 'demo-badge' }, h('span', { class: 'dot' }), badgeText), timeEl,
  h('div', { class: 'demo-tools' }, playBtn, langBtn, resetBtn,
    h('a', { class: 'demo-btn gh', href: 'https://github.com/xoliddev/test-ustasi', target: '_blank', rel: 'noopener' }, 'GitHub')));
const title = h('h1');
const lead = h('p');
const caption = h('p', { class: 'story-cap', 'data-testid': 'story-caption', 'aria-live': 'polite' });
const foot = h('p', { class: 'demo-foot' });
const env = { backend, bots, wait, focus, done: new Set(), texts: shared.texts, t, lang: () => lang, s: {} };
env.ui = makeUi({ phones, apps, bots, backend, wait });
let running = false;
let current = 0;
async function step(i) {
  if (running) return;
  running = true;
  current = i + 1;
  paintStory();
  try {
    await runStep(i + 1, env);
  } catch (err) {
    console.warn(err); // eslint-disable-line no-console
  }
  running = false;
  paintStory();
}
async function play() {
  for (let i = 0; i < STEPS.length; i++) if (!env.done.has(i + 1)) await step(i);
}
const storyBtns = STEPS.map((_, i) => h('button', { class: 'story-btn', type: 'button', 'data-testid': `story-${i + 1}`, onclick: () => step(i) },
  h('b', {}, String(i + 1)), h('span')));
function paintStory() {
  const next = STEPS.findIndex((_, i) => !env.done.has(i + 1));
  storyBtns.forEach((b, i) => {
    b.lastChild.textContent = P(`demo.step_${i + 1}`);
    b.classList.toggle('done', env.done.has(i + 1));
    b.classList.toggle('next', i === next && !running);
    b.classList.toggle('now', running && i + 1 === current);
    b.disabled = running;
  });
  playBtn.disabled = running || next < 0;
  let params = {};
  try {
    params = current ? captionParams(current, env) : {};
  } catch { /* a step half-way */ }
  caption.textContent = current ? P(`demo.cap_${current}`, params) : P('demo.cap_0');
}
const SIDES = ['nodira', 'jasur', 'try'];
const whoBtns = SIDES.map((w) => h('button', { type: 'button', 'data-testid': `switch-${w}`, onclick: () => pick(w) }));
const sides = () => [phones[NODIRA].side, phones[JASUR].side, tryBox.side];
function pick(w) {
  whoBtns.forEach((b, i) => b.classList.toggle('on', SIDES[i] === w));
  sides().forEach((s, i) => s.classList.toggle('show', SIDES[i] === w));
}
const paintClock = () => {
  const m = localMinute(backend.nowMs());
  timeEl.textContent = P('demo.time', { date: dateText(t, lang, localDay(backend.nowMs())), time: `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}` });
  for (const uid of [NODIRA, JASUR]) phones[uid].tick();
};
function paintTexts() {
  document.documentElement.lang = lang;
  badgeText.textContent = P('demo.badge');
  langBtn.textContent = lang === 'uz' ? 'RU' : 'UZ';
  resetBtn.textContent = P('demo.reset');
  playBtn.textContent = P('demo.play');
  title.textContent = P('demo.title');
  lead.textContent = P('demo.lead');
  foot.textContent = P('demo.foot');
  whoBtns.forEach((b, i) => { b.textContent = P(`demo.${SIDES[i]}`); });
  for (const uid of [NODIRA, JASUR]) {
    phones[uid].renderLabels(P(`demo.${WHO[uid]}`), P(`demo.role_${WHO[uid]}`));
    phones[uid].renderChat();
  }
  tryBox.renderLabels(lang);
  paintStory();
  paintClock();
}
function setLang(next) {
  if (next === lang) return;
  lang = next;
  store.set('testustasi.lang', lang);
  for (const uid of [NODIRA, JASUR]) {
    backend.setLang(uid, lang);
    apps[uid].setLang(lang);
  }
  paintTexts();
}
setInterval(paintClock, 10_000);

document.body.append(bar, h('section', { class: 'demo-intro' }, title, lead), h('nav', { class: 'story', 'aria-label': 'story' }, storyBtns), caption,
  h('div', { class: 'who-switch', role: 'tablist' }, whoBtns), h('main', { class: 'demo-stage' }, sides()), foot);
for (const uid of [NODIRA, JASUR]) bots[uid].start();
phones[NODIRA].show('chat');
phones[JASUR].show('chat');
pick('nodira');
paintTexts();
await Promise.all([apps[NODIRA].ready, apps[JASUR].ready]);
document.body.dataset.ready = '1';
