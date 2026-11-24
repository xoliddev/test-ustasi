// The Mini App shell for both roles: a header with "⬅️ Orqaga", the current screen, a language switch, and live
// refreshes. A teacher sees their tests, classes and "Yangi test", a draft's review, the results and the analysis; a
// student sees their tests and solves one. The same code runs in Telegram (HTTP API) and in the demo (in-page backend).
import { renderAnalysis } from './t-analysis.js';
import { renderClasses, renderNew, renderTests } from './t-home.js';
import { renderResults } from './t-results.js';
import { renderReview } from './t-review.js';
import { renderStudentHome } from './s-home.js';
import { renderSolve } from './s-solve.js';
import { errText, fill, h, makeText, toast } from './util.js';

const VIEWS = { t: 'test', r: 'results', a: 'analysis', s: 'solve' };
const TABS = [['tests', 'app.tab_tests', '📋'], ['classes', 'app.tab_classes', '👥'], ['new', 'app.tab_new', '＋']];

export function routeFrom(search) {
  const p = new URLSearchParams(search);
  for (const [k, view] of Object.entries(VIEWS)) if (/^\d{1,12}$/.test(p.get(k) ?? '')) return { view, id: Number(p.get(k)) };
  return null;
}

export function mountApp(root, opts) {
  const T = makeText(opts.catalogs);
  const state = { lang: opts.lang === 'ru' ? 'ru' : 'uz', me: null, route: { view: 'home' }, stack: [], tab: 'tests', busy: false };
  const P = (k, p) => T(state.lang, k, p);
  const ctx = {
    api: opts.api, now: opts.now ?? (() => Date.now()), get lang() { return state.lang; }, P, T, state: {}, catalogs: opts.catalogs,
    toast: (text, kind) => toast(root, text, kind), fail: (e) => toast(root, errText(T, state.lang, e), 'bad'),
    open: (route) => open(route), back: () => back(), refresh: () => refresh(), get me() { return state.me; }, root,
  };
  const backBtn = h('button', { type: 'button', class: 'u-back', 'data-testid': 'app-back', onclick: () => back() });
  const title = h('b', { class: 'u-title', 'data-testid': 'app-title' });
  const role = h('span', { class: 'u-role', 'data-testid': 'app-role' });
  const langBtn = h('button', { type: 'button', class: 'u-lang', 'data-testid': 'app-lang', onclick: () => setLang(state.lang === 'uz' ? 'ru' : 'uz') });
  const body = h('main', { class: 'u-body', 'data-testid': 'app-body' });
  const tabs = h('nav', { class: 'u-tabs', role: 'tablist' });
  fill(root, h('div', { class: 'u-app', 'data-testid': 'uapp' }, h('header', { class: 'u-head' }, backBtn, h('div', { class: 'u-titles' }, title, role), langBtn),
    body, tabs));

  function paintHead(name) {
    title.textContent = name || 'Test Ustasi';
    role.textContent = state.me?.role ? P(`app.role_${state.me.role}`) : '';
    langBtn.textContent = P('app.lang');
    backBtn.textContent = P('app.back');
    backBtn.hidden = !state.stack.length;
    const home = state.route.view === 'home' && state.me?.role === 'teacher';
    tabs.hidden = !home;
    fill(tabs, home ? TABS.map(([key, label, icon]) => h('button', { type: 'button', class: `u-tab${state.tab === key ? ' on' : ''}`, role: 'tab',
      'data-testid': `tab-${key}`, onclick: () => { state.tab = key; paint(); } }, h('span', { class: 'u-tab-i', 'aria-hidden': 'true' }, icon), P(label))) : []);
    if (opts.telegram?.BackButton) {
      if (state.stack.length) opts.telegram.BackButton.show();
      else opts.telegram.BackButton.hide();
    }
  }

  async function paint() {
    const { view, id } = state.route;
    const el = h('section', { class: `u-page u-${view}`, 'data-testid': `page-${view === 'home' ? `${state.me?.role ?? 'none'}-${state.tab}` : view}` });
    let name = '';
    try {
      if (!state.me?.role) el.append(h('p', { class: 'u-outside' }, P('app.no_role')));
      else if (view === 'home' && state.me.role === 'teacher') name = await ({ tests: renderTests, classes: renderClasses, new: renderNew })[state.tab](ctx, el);
      else if (view === 'home') name = await renderStudentHome(ctx, el);
      else if (view === 'test') name = await renderReview(ctx, el, id);
      else if (view === 'results') name = await renderResults(ctx, el, id);
      else if (view === 'analysis') name = await renderAnalysis(ctx, el, id);
      else name = await renderSolve(ctx, el, id);
    } catch (e) {
      ctx.fail(e);
      if (e?.code === 'not_found' || e?.code === 'forbidden') el.append(h('p', { class: 'u-outside' }, errText(T, state.lang, e)));
    }
    paintHead(name);
    fill(body, el);
  }

  async function refresh() {
    if (state.busy) {
      state.again = true;
      return state.running;
    }
    if (ctx.state.hold) return null; // a form is open or a question is on screen: keep it as it is
    state.busy = true;
    state.running = (async () => {
      try {
        state.me = await opts.api.me();
        if (state.me.lang && state.me.lang !== state.lang && !state.langSet) state.lang = state.me.lang;
        await paint();
      } catch (e) {
        ctx.fail(e);
      } finally {
        state.busy = false;
      }
      if (state.again) {
        state.again = false;
        await refresh();
      }
    })();
    return state.running;
  }

  async function open(route) {
    ctx.state.hold = false;
    state.stack.push(state.route);
    state.route = route;
    await paint();
    body.scrollTo?.({ top: 0 });
  }

  async function back() {
    ctx.state.hold = false;
    state.route = state.stack.pop() ?? { view: 'home' };
    await paint();
  }

  async function setLang(l) {
    state.lang = l;
    state.langSet = true;
    opts.onLang?.(l);
    try {
      await opts.api.setLang(l);
    } catch { /* the language still changes on this screen */ }
    await paint();
  }

  opts.telegram?.BackButton?.onClick?.(() => back());
  if (opts.route) {
    state.stack.push({ view: 'home' });
    state.route = opts.route;
  }
  const ready = refresh();
  if (opts.poll) setInterval(() => { if (['home', 'results', 'analysis'].includes(state.route.view)) refresh(); }, opts.poll);
  return {
    ready, refresh, open, back, ctx, root, setLang: (l) => (l !== state.lang ? setLang(l) : null),
    get route() { return state.route; }, get tab() { return state.tab; }, setTab: (t) => { state.tab = t; return paint(); },
    home: () => { state.stack = []; state.route = { view: 'home' }; ctx.state.hold = false; return paint(); },
  };
}
