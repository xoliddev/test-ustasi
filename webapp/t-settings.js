// A draft's publishing settings, each saved on the server the moment it is picked (and checked there): the class, the
// time limit, attempts, the deadline, the order, showing answers afterwards, the student's place; then "Nashr qilish".
import { atLocal, localDay } from '../shared/clock.js';
import { minutes as minText, questions } from '../shared/i18n.js';
import { chips, confirmBox, h } from './util.js';

const MINUTES = [10, 15, 20, 30, 45];
const ATTEMPTS = [1, 2, 3];

function deadlines(now) {
  const today = localDay(now);
  const out = [];
  if (atLocal(today, 23 * 60 + 59) - now > 10 * 60_000) out.push(['today', atLocal(today, 23 * 60 + 59)]);
  out.push(['tomorrow', atLocal(today + 1, 23 * 60 + 59)], ['week', atLocal(today + 7, 23 * 60 + 59)], ['none', null]);
  return out;
}

export function renderSettings(ctx, el, d) {
  const { P } = ctx;
  const t = (l, k, p) => ctx.T(l, k, p);
  const save = async (data) => {
    try {
      Object.assign(d, await ctx.api.settings(d.id, data));
    } catch (e) {
      ctx.fail(e);
    }
  };
  const dls = deadlines(ctx.now());
  const current = dls.find(([, v]) => v === d.deadline)?.[0] ?? (d.deadline ? 'custom' : 'none');
  const toggle = (key) => h('label', { class: 'u-toggle' }, h('input', { type: 'checkbox', checked: d[key], 'data-testid': `set-${key}`,
    onchange: (e) => save({ [key]: e.target.checked }) }), h('span', {}, P(`app.s_${key}`)));
  const classes = d.classes.length ? chips(d.classes.map((k) => [k.id, k.name]), d.grp, (v) => save({ grp: v }), 'set-class')
    : h('p', { class: 'u-empty' }, P('app.classes_none'));
  const publish = h('button', { type: 'button', class: 'u-btn big', 'data-testid': 'publish', onclick: async () => {
    if (!d.grp) {
      ctx.toast(P('err.no_class'), 'bad');
      return;
    }
    const cls = d.classes.find((k) => k.id === d.grp)?.name ?? '';
    const ask = P('app.publish_ask', { title: d.title, cls, count: questions(t, ctx.lang, d.questions.length), minutes: minText(t, ctx.lang, d.minutes) });
    if (!(await confirmBox(ctx.root, ask, P('app.publish'), P('app.cancel')))) return;
    publish.disabled = true;
    try {
      await ctx.api.publish(d.id);
      ctx.toast(P('app.published'), 'ok');
      await ctx.refresh();
    } catch (e) {
      ctx.fail(e);
      publish.disabled = false;
    }
  } }, P('app.publish'));
  el.append(h('section', { class: 'u-card u-settings', 'data-testid': 'settings' }, h('h3', { class: 'u-h' }, P('app.settings')),
    h('label', { class: 'u-label' }, P('app.s_class')), classes,
    h('label', { class: 'u-label' }, P('app.s_minutes')), chips(MINUTES.map((m) => [m, minText(t, ctx.lang, m)]), d.minutes, (v) => save({ minutes: v }), 'set-minutes'),
    h('label', { class: 'u-label' }, P('app.s_attempts')), chips(ATTEMPTS.map((a) => [a, String(a)]), d.attempts, (v) => save({ attempts: v }), 'set-attempts'),
    h('label', { class: 'u-label' }, P('app.s_deadline')), chips(dls.map(([k]) => [k, P(`app.dl_${k}`)]), current,
      (v) => save({ deadline: dls.find(([k]) => k === v)[1] }), 'set-deadline'),
    toggle('shuffle'), toggle('reveal'), toggle('rank'), publish));
}
