// "O'zingiz sinab ko'ring": the visitor pastes any Uzbek paragraph and instantly gets test questions from the very
// rule-based generator the server uses (the same function, nothing is sent anywhere), each with its quote.
import { LETTERS } from '../shared/analysis.js';
import { generate } from '../shared/generate.js';
import { h } from '../webapp/util.js';

const EXAMPLES = ['ulugbek', 'orol', 'tovush', 'hujayra'];

export function createTry({ P, texts }) {
  const byId = Object.fromEntries(texts.map((t) => [t.id, t]));
  const input = h('textarea', { rows: 7, maxlength: 6000, 'data-testid': 'try-input', 'aria-label': 'try' });
  const out = h('div', { class: 'try-out', 'data-testid': 'try-out', 'aria-live': 'polite' });
  const count = h('span', { class: 'try-kind', 'data-testid': 'try-count' });
  const title = h('h2');
  const lead = h('p', { class: 'try-lead' });
  const exLabel = h('span', { class: 'try-ex-l' });
  const chipBtns = EXAMPLES.map((id) => h('button', { type: 'button', class: 'try-chip', 'data-testid': `try-ex-${id}`,
    onclick: () => { input.value = byId[id].body; paint(); } }));
  const chips = h('div', { class: 'try-ex' }, exLabel, chipBtns);
  let timer = null;

  function paint() {
    const text = input.value.trim();
    if (Array.from(text).length < 150) {
      count.textContent = '';
      out.replaceChildren(h('p', { class: 'try-hint' }, P(text ? 'demo.try_short' : 'demo.try_empty')));
      return;
    }
    const qs = generate(text, 10, 'mixed');
    count.textContent = qs.length ? P('demo.try_count', { n: qs.length }) : '';
    out.replaceChildren(...(qs.length ? qs.map((q, i) => h('article', { class: 'try-q', 'data-testid': `try-q-${i + 1}` },
      h('p', { class: 'try-stem' }, h('b', {}, `${i + 1}. `), q.stem),
      h('ol', { class: 'try-opts' }, q.options.map((o, k) => h('li', { class: k === q.correct ? 'ok' : '' }, h('b', {}, LETTERS[k]), ` ${o}`, k === q.correct ? ' ✓' : ''))),
      h('blockquote', { class: 'try-quote' }, h('b', {}, `${P('app.quote')} `), `«${q.quote}»`))) : [h('p', { class: 'try-hint' }, P('demo.try_empty'))]));
  }

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(paint, 250);
  });
  const root = h('section', { class: 'side try', 'data-who': 'try', 'data-testid': 'try' },
    h('div', { class: 'try-card' }, title, lead, input, chips, h('div', { class: 'try-res' }, count, out)));
  function renderLabels() {
    title.textContent = P('demo.try_title');
    lead.textContent = P('demo.try_lead');
    input.placeholder = P('demo.try_ph');
    exLabel.textContent = P('demo.try_examples');
    chipBtns.forEach((b, i) => { b.textContent = P(`demo.ex_${EXAMPLES[i]}`); });
    paint();
  }
  input.value = byId.ulugbek.body;
  return { side: root, renderLabels, input, paint };
}
