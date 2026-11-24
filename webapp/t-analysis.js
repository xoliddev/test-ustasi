// The analysis of wrong answers: per question the share who got it right, how the strong and the weaker students did,
// which option each share picked, and a flag with plain advice; the topics where the class is weak (and who struggled
// most); the one-tap retest for the most-missed topics, and after it the class's progress on them.
import { LETTERS, MIN_FLAGS } from '../shared/analysis.js';
import { flagText, pct } from '../shared/i18n.js';
import { pctBar } from './chart.js';
import { head } from './t-results.js';
import { confirmBox, h } from './util.js';

const FLAG_CLASS = { key: 'bad', hard: 'warn', easy: 'ok' };

function question(ctx, r) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const advice = flagText(t, ctx.lang, r);
  return h('article', { class: `u-aq${r.flag ? ` f-${r.flag}` : ''}`, 'data-testid': `aq-${r.pos}` },
    h('div', { class: 'u-q-top' }, h('b', {}, P('app.q', { n: r.pos })), h('span', { class: 'u-chip' }, r.topic),
      h('span', { class: 'u-aq-pct', 'data-testid': `aq-pct-${r.pos}` }, P('app.q_right', { p: pct(t, ctx.lang, r.pct) }))),
    pctBar(r.pct, r.pct < 50 ? 'low' : r.pct >= 90 ? 'high' : ''),
    h('p', { class: 'u-stem' }, r.stem),
    h('ol', { class: 'u-picks' }, r.options.map((o, i) => h('li', { class: i === r.correct ? 'ok' : r.pick?.option === i ? 'lead' : '' },
      h('b', {}, LETTERS[i]), h('span', { class: 'u-pick-o' }, o), h('span', { class: 'u-pick-p' }, pct(t, ctx.lang, r.picks[i])), pctBar(r.picks[i])))),
    r.top !== null ? h('p', { class: 'u-disc' }, P('app.disc', { top: pct(t, ctx.lang, r.top), bottom: pct(t, ctx.lang, r.bottom) })) : null,
    advice ? h('p', { class: `u-flag ${FLAG_CLASS[r.flag]}`, 'data-testid': `flag-${r.pos}` }, advice) : null);
}

function retestBox(ctx, an) {
  const { P } = ctx;
  if (an.parent || an.retest) return null;
  const plan = an.plan;
  if (!plan.topics.length || !plan.count) return h('section', { class: 'u-card' }, h('p', { class: 'u-empty' }, P('app.retest_none')));
  const go = h('button', { type: 'button', class: 'u-btn big', 'data-testid': 'retest', onclick: async () => {
    const ask = P('app.retest_lead', { topics: plan.topics.join(', '), count: plan.count });
    if (!(await confirmBox(ctx.root, ask, P('app.retest_go'), P('app.cancel')))) return;
    go.disabled = true;
    try {
      const info = await ctx.api.retest(an.id);
      ctx.toast(P('app.retest_sent', { n: info.students }), 'ok');
      await ctx.refresh();
    } catch (e) {
      ctx.fail(e);
      go.disabled = false;
    }
  } }, P('app.retest_go'));
  return h('section', { class: 'u-card u-retest', 'data-testid': 'retest-box' }, h('h3', { class: 'u-h' }, P('app.retest_title')),
    h('p', {}, P('app.retest_lead', { topics: plan.topics.join(', '), count: plan.count })), h('p', { class: 'u-names' }, plan.names.join(', ')),
    plan.skipped.length ? h('p', { class: 'u-note' }, P('app.retest_skip', { list: plan.skipped.join(', ') })) : null, go);
}

function progressBox(ctx, an) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const pr = an.progress;
  if (!pr || !pr.retook) return null;
  const other = an.parent ? h('button', { type: 'button', class: 'u-btn ghost', onclick: () => ctx.open({ view: 'results', id: an.parent }) }, P('app.open_parent'))
    : h('button', { type: 'button', class: 'u-btn ghost', 'data-testid': 'open-retest', onclick: () => ctx.open({ view: 'results', id: an.retest }) }, P('app.open_retest'));
  return h('section', { class: 'u-card u-progress', 'data-testid': 'progress' }, h('small', {}, `${P('app.progress')} · ${pr.topics.join(', ')}`),
    h('div', { class: 'u-prog' }, h('b', { class: 'before', 'data-testid': 'prog-before' }, pct(t, ctx.lang, pr.before)), h('span', {}, '→'),
      h('b', { class: 'after', 'data-testid': 'prog-after' }, pct(t, ctx.lang, pr.after))), other);
}

function topicsBox(ctx, an) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  return h('section', { class: 'u-card', 'data-testid': 'topics' }, h('h3', { class: 'u-h' }, P('app.topics')), an.topics.map((tp) => h('div', { class: 'u-topic' },
    h('div', { class: 'u-topic-top' }, h('span', {}, tp.topic), h('b', {}, pct(t, ctx.lang, tp.pct))), pctBar(tp.pct, tp.pct < 60 ? 'low' : ''),
    tp.pct < 60 ? h('p', { class: 'u-names' }, `${P('app.topics_people')}: `, tp.people.filter((x) => x.pct < 50).slice(0, 6).map((x) => `${x.name.split(' ')[0]} (${pct(t, ctx.lang, x.pct)})`).join(', ')) : null)));
}

export async function renderAnalysis(ctx, el, id) {
  const { P } = ctx;
  const an = await ctx.api.analysis(id);
  el.append(...head(ctx, an, 'analysis'), progressBox(ctx, an) ?? h('span'));
  if (an.n < MIN_FLAGS) el.append(h('p', { class: 'u-note' }, P('flag.few')));
  el.append(...an.questions.map((r) => question(ctx, r)), topicsBox(ctx, an), retestBox(ctx, an) ?? h('span'));
  return P('app.analysis');
}
