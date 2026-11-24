// The student's tests: new ones, the one in progress, the finished ones with the score, and the closed ones.
import { questions, minutes, when } from '../shared/i18n.js';
import { h } from './util.js';

export async function renderStudentHome(ctx, el) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const { items } = await ctx.api.tests();
  if (!items.length) {
    el.append(h('p', { class: 'u-empty' }, P('app.my_none')));
    return P('app.my_tests');
  }
  el.append(h('div', { class: 'u-list', 'data-testid': 'my-tests' }, items.map((it) => {
    const chip = it.status === 'done' ? P('app.m_done', { s: it.score, n: it.count }) : P(`app.m_${it.status}`);
    const sub = [questions(t, ctx.lang, it.count), minutes(t, ctx.lang, it.minutes), it.deadline ? `${P('lbl.deadline')}: ${when(t, ctx.lang, it.deadline, ctx.now())}` : null];
    return h('button', { type: 'button', class: `u-item st-${it.status}`, 'data-testid': `my-${it.id}`, onclick: () => ctx.open({ view: 'solve', id: it.id }) },
      h('div', { class: 'u-item-top' }, h('b', {}, it.retest ? `🔁 ${it.title}` : it.title), h('span', { class: `u-chip ${it.status}` }, chip)),
      h('div', { class: 'u-item-sub' }, sub.filter(Boolean).join(' · ')));
  })));
  return P('app.my_tests');
}
