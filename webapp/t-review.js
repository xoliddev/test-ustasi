// A draft's review: every question with its options (the correct one marked), the explanation and the quote from the
// text ("Matnda: «…»"); edit, delete, another question in its place, move up or down; then the settings and
// "🚀 Nashr qilish". A published test opens on its results.
import { LETTERS } from '../shared/analysis.js';
import { renderResults } from './t-results.js';
import { renderSettings } from './t-settings.js';
import { confirmBox, h } from './util.js';

function editForm(ctx, d, q, done) {
  const { P } = ctx;
  const stem = h('textarea', { class: 'u-text', rows: 3, maxlength: 300, 'data-testid': 'edit-stem' });
  stem.value = q.stem;
  let correct = q.correct;
  const opts = q.options.map((o, i) => {
    const input = h('input', { class: 'u-input', maxlength: 120, 'aria-label': P('app.f_option', { l: LETTERS[i] }), 'data-testid': `edit-opt-${i}` });
    input.value = o;
    return input;
  });
  const radios = opts.map((_, i) => h('input', { type: 'radio', name: `correct-${q.id}`, checked: i === correct, 'aria-label': P('app.f_correct'),
    onchange: () => { correct = i; } }));
  const expl = h('textarea', { class: 'u-text', rows: 2, maxlength: 400 });
  expl.value = q.explanation;
  const topic = h('input', { class: 'u-input', maxlength: 40 });
  topic.value = q.topic;
  const save = h('button', { type: 'button', class: 'u-btn', 'data-testid': 'edit-save', onclick: async () => {
    try {
      await ctx.api.edit(d.id, q.id, { stem: stem.value, options: opts.map((x) => x.value), correct, explanation: expl.value, topic: topic.value });
      ctx.toast(P('app.saved'), 'ok');
      done(true);
    } catch (e) {
      ctx.fail(e);
    }
  } }, P('app.save'));
  return h('div', { class: 'u-form', 'data-testid': 'edit-form' }, h('label', { class: 'u-label' }, P('app.f_stem')), stem,
    opts.map((o, i) => h('div', { class: 'u-optedit' }, h('label', { class: 'u-radio' }, radios[i], h('b', {}, LETTERS[i])), o)),
    h('label', { class: 'u-label' }, P('app.f_expl')), expl, h('label', { class: 'u-label' }, P('app.f_topic')), topic,
    h('div', { class: 'u-row' }, h('button', { type: 'button', class: 'u-btn ghost', onclick: () => done(false) }, P('app.cancel')), save));
}

function card(ctx, d, q, n, total) {
  const { P } = ctx;
  const act = async (fn) => {
    try {
      await fn();
      await ctx.refresh();
    } catch (e) {
      ctx.fail(e);
    }
  };
  const box = h('article', { class: 'u-q', 'data-testid': `q-${n}`, 'data-qid': String(q.id) });
  const view = h('div', {}, h('div', { class: 'u-q-top' }, h('b', {}, P('app.q', { n })), h('span', { class: 'u-chip' }, q.topic),
    q.edited ? h('span', { class: 'u-chip warn' }, P('app.edited')) : null),
  h('p', { class: 'u-stem' }, q.stem),
  h('ol', { class: 'u-opts' }, q.options.map((o, i) => h('li', { class: i === q.correct ? 'ok' : '' }, h('b', {}, LETTERS[i]), h('span', {}, o), i === q.correct ? h('i', {}, '✓') : null))),
  q.explanation ? h('p', { class: 'u-why' }, h('b', {}, `${P('app.why')} `), q.explanation) : null,
  h('blockquote', { class: 'u-quote', 'data-testid': `quote-${n}` }, h('b', {}, `${P('app.quote')} `), `«${q.quote}»`),
  h('div', { class: 'u-actions' },
    h('button', { type: 'button', 'data-testid': `edit-${n}`, onclick: () => {
      ctx.state.hold = true;
      box.replaceChildren(editForm(ctx, d, q, (saved) => { ctx.state.hold = false; if (saved) ctx.refresh(); else box.replaceChildren(view); }));
    } }, `✏️ ${P('app.edit')}`),
    h('button', { type: 'button', 'data-testid': `regen-${n}`, onclick: () => act(() => ctx.api.regen(d.id, q.id)) }, `🔄 ${P('app.regen')}`),
    h('button', { type: 'button', disabled: n === 1, 'aria-label': P('app.up'), onclick: () => act(() => ctx.api.move(d.id, q.id, -1)) }, '↑'),
    h('button', { type: 'button', disabled: n === total, 'aria-label': P('app.down'), onclick: () => act(() => ctx.api.move(d.id, q.id, 1)) }, '↓'),
    h('button', { type: 'button', class: 'bad', 'data-testid': `delete-${n}`, onclick: async () => {
      if (await confirmBox(ctx.root, P('app.delete_ask', { n }), P('app.delete'), P('app.cancel'))) await act(() => ctx.api.remove(d.id, q.id));
    } }, `🗑 ${P('app.delete')}`)));
  box.append(view);
  return box;
}

export async function renderReview(ctx, el, id) {
  const d = await ctx.api.test(id);
  if (d.status === 'published') return renderResults(ctx, el, id, d);
  const { P } = ctx;
  const n = d.questions.length;
  el.append(h('div', { class: 'u-hero' }, h('small', {}, `${P('app.review')} · ${d.source}`), h('h2', {}, d.title),
    h('p', {}, P('fmt.questions', { n })), n < d.asked ? h('p', { class: 'u-note', 'data-testid': 'fewer' }, P('app.fewer', { asked: d.asked, n })) : null),
  h('p', { class: 'u-lead' }, P('app.review_lead')),
  h('div', { class: 'u-qs', 'data-testid': 'questions' }, d.questions.map((q, i) => card(ctx, d, q, i + 1, n))));
  renderSettings(ctx, el, d);
  return P('app.review');
}
