// A published test's results, live: who finished, the average and the median, the grade chart, the table (tap a
// column to sort), and the CSV for Excel. Every number comes from shared/analysis.js through the server.
import { mmss, pct, when } from '../shared/i18n.js';
import { gradeChart } from './chart.js';
import { h } from './util.js';

const COLS = [['name', 'app.col_name'], ['score', 'app.col_score'], ['pct', 'app.col_pct'], ['seconds', 'app.col_time'], ['status', 'app.col_status']];
const RANK = { done: 0, working: 1, waiting: 2 };

export function head(ctx, res, current) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const bits = [res.code ? P('app.code_line', { code: res.code }) : P('app.st_retest'), res.deadline ? `${P('lbl.deadline')}: ${when(t, ctx.lang, res.deadline, ctx.now())}` : null];
  return [h('div', { class: 'u-hero' }, h('div', { class: 'u-hero-top' }, h('span', {}, bits.filter(Boolean).join(' · ')),
    h('span', { class: 'u-live' }, h('i'), P('app.live'))), h('h2', { 'data-testid': 'res-title' }, res.title)),
  h('div', { class: 'u-seg', role: 'tablist' }, [['results', 'app.results'], ['analysis', 'app.analysis']].map(([view, label]) => h('button', {
    type: 'button', class: view === current ? 'on' : '', 'data-testid': `seg-${view}`, onclick: () => (view === current ? null : ctx.open({ view, id: res.id })) },
  P(label))))];
}

function sortRows(rows, key, dir) {
  const val = (r) => (key === 'status' ? RANK[r.status] : key === 'name' ? r.name : (r[key] ?? -1));
  return [...rows].sort((a, b) => {
    const x = val(a);
    const y = val(b);
    const c = typeof x === 'string' ? x.localeCompare(y) : x - y;
    return (c || a.user - b.user) * dir;
  });
}

export async function renderResults(ctx, el, id) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const res = await ctx.api.results(id);
  const st = res.stats;
  const sort = ctx.state.sort ?? (ctx.state.sort = { key: 'pct', dir: -1 });
  const status = (r) => (r.status === 'done' ? (r.auto ? P('app.s_auto') : P('app.s_done'))
    : r.status === 'working' ? P('app.s_working', { a: r.answered, b: r.total }) : P('app.s_waiting'));
  const table = h('table', { class: 'u-table', 'data-testid': 'results-table' });
  const paintTable = () => {
    table.replaceChildren(h('thead', {}, h('tr', {}, COLS.map(([key, label]) => h('th', { 'data-testid': `sort-${key}`, class: sort.key === key ? 'on' : '',
      onclick: () => { sort.dir = sort.key === key ? -sort.dir : key === 'name' ? 1 : -1; sort.key = key; paintTable(); } },
    P(label), sort.key === key ? (sort.dir > 0 ? ' ↑' : ' ↓') : '')))),
    h('tbody', {}, sortRows(res.rows, sort.key, sort.dir).map((r) => h('tr', { class: `r-${r.status}`, 'data-testid': `row-${r.user}` },
      h('td', {}, r.name), h('td', {}, r.status === 'done' ? `${r.score}/${r.total}` : ''), h('td', {}, r.status === 'done' ? pct(t, ctx.lang, r.pct) : ''),
      h('td', {}, r.status === 'done' ? mmss(t, ctx.lang, r.seconds) : ''), h('td', {}, h('span', { class: `u-chip ${r.status}` }, status(r)))))));
  };
  paintTable();
  const csv = h('button', { type: 'button', class: 'u-btn ghost', 'data-testid': 'csv', disabled: !st.done, onclick: async () => {
    try {
      const out = await ctx.api.csv(id);
      const a = h('a', { href: URL.createObjectURL(new Blob([out.csv], { type: 'text/csv;charset=utf-8' })), download: out.name });
      document.body.append(a);
      a.click();
      a.remove();
    } catch (e) {
      ctx.fail(e);
    }
  } }, P('app.csv'));
  el.append(...head(ctx, res, 'results'),
    h('div', { class: 'u-stats' },
      h('div', { class: 'u-stat' }, h('small', {}, P('lbl.done')), h('b', { 'data-testid': 'stat-done' }, P('fmt.of', { a: st.done, b: st.people }))),
      h('div', { class: 'u-stat' }, h('small', {}, P('lbl.avg')), h('b', { 'data-testid': 'stat-avg' }, st.done ? pct(t, ctx.lang, st.avg) : '—')),
      h('div', { class: 'u-stat' }, h('small', {}, P('lbl.median')), h('b', { 'data-testid': 'stat-median' }, st.done ? pct(t, ctx.lang, st.median) : '—'))),
    h('section', { class: 'u-card' }, h('h3', { class: 'u-h' }, P('app.grades')), gradeChart(st.grades, P('app.grades'))),
    st.done || st.working ? h('div', { class: 'u-scroll' }, table) : h('p', { class: 'u-empty' }, P('app.no_results')), csv);
  return P('app.results');
}
