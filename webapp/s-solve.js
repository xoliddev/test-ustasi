// Solving: the test's card, then one question per screen with the progress and the server's timer (answers saved the
// moment they are tapped; a reload continues where it stopped), "Topshirish" with a check for unanswered questions,
// an automatic submit at time-out, and the result: the score, the time and — when allowed — each mistake with the
// correct answer, the explanation and the quote from the text.
import { LETTERS } from '../shared/analysis.js';
import { minutes, mmss, pct, questions, when } from '../shared/i18n.js';
import { confirmBox, h } from './util.js';

const tt = (ctx) => (l, k, p) => ctx.T(l, k, p);

function result(ctx, el, r, card) {
  const { P } = ctx;
  const t = tt(ctx);
  ctx.state.hold = false;
  const box = h('div', { class: 'u-result', 'data-testid': 'result' },
    h('div', { class: `u-ring g${r.grade}` }, h('b', { 'data-testid': 'score' }, `${r.score}/${r.total}`), h('span', {}, `${pct(t, ctx.lang, r.pct)} · ${P('fmt.grade', { g: r.grade })}`)),
    h('p', {}, P('app.r_time', { t: mmss(t, ctx.lang, r.seconds) })), r.auto ? h('p', { class: 'u-note' }, P('app.r_auto')) : null,
    r.rank ? h('p', { class: 'u-rank', 'data-testid': 'rank' }, P('app.r_rank', r.rank)) : null);
  const list = h('section', { class: 'u-mistakes', 'data-testid': 'mistakes' }, h('h3', { class: 'u-h' }, P('app.mistakes')));
  if (r.reveal) {
    if (!r.mistakes.length) list.append(h('p', { class: 'u-empty' }, P('app.no_mistakes')));
    for (const m of r.mistakes) {
      list.append(h('article', { class: 'u-q', 'data-testid': `mistake-${m.n}` }, h('b', {}, P('app.q', { n: m.n })), h('p', { class: 'u-stem' }, m.stem),
        h('p', { class: 'u-your' }, `${P('app.your')} `, h('b', {}, m.chosen ?? P('app.none'))), h('p', { class: 'u-right' }, `${P('app.right')} `, h('b', {}, m.correct)),
        m.explanation ? h('p', { class: 'u-why' }, m.explanation) : null, h('blockquote', { class: 'u-quote' }, h('b', {}, `${P('app.quote')} `), `«${m.quote}»`)));
    }
  } else list.append(h('p', { class: 'u-note' }, P(r.left ? 'app.hidden_left' : 'app.hidden_teacher')));
  const again = r.left && !r.closed ? h('button', { type: 'button', class: 'u-btn', onclick: () => start(ctx, el, card) }, P('app.again')) : null;
  el.replaceChildren(h('h2', { class: 'u-h2' }, r.title), box, list, h('div', { class: 'u-row' }, again,
    h('button', { type: 'button', class: 'u-btn ghost', 'data-testid': 'to-list', onclick: () => ctx.back() }, P('app.to_list'))));
}

function solving(ctx, el, v, card) {
  const { P } = ctx;
  const t = tt(ctx);
  ctx.state.hold = true;
  const skew = v.now - ctx.now();
  const left = () => v.deadline_at - (ctx.now() + skew);
  const s = ctx.state.solve?.attempt === v.attempt ? ctx.state.solve : (ctx.state.solve = { attempt: v.attempt, idx: 0 });
  const chosen = { ...v.answers };
  const timer = h('b', { class: 'u-timer', 'data-testid': 'timer' });
  const count = h('span', { 'data-testid': 'progress' });
  const bar = h('div', { class: 'u-prog-bar' }, h('i'));
  const stage = h('div', { class: 'u-stage' });
  const dots = h('div', { class: 'u-dots' });
  let done = false;
  const finish = async () => {
    if (done) return;
    done = true;
    clearInterval(tick);
    try {
      result(ctx, el, await ctx.api.submit(v.attempt), card);
    } catch (e) {
      ctx.fail(e);
      result(ctx, el, await ctx.api.result(card.id), card);
    }
  };
  const tick = setInterval(() => {
    if (!el.isConnected) {
      clearInterval(tick);
      return;
    }
    const ms = left();
    timer.textContent = mmss(t, ctx.lang, Math.max(0, Math.ceil(ms / 1000)));
    timer.classList.toggle('low', ms < 60_000);
    if (ms <= 0) finish();
  }, 500);
  timer.textContent = mmss(t, ctx.lang, Math.max(0, Math.ceil(left() / 1000)));
  const paint = () => {
    const q = v.questions[s.idx];
    const n = v.questions.length;
    count.textContent = P('app.of', { a: s.idx + 1, b: n });
    bar.firstChild.style.width = `${Math.round((100 * Object.keys(chosen).length) / n)}%`;
    stage.replaceChildren(h('p', { class: 'u-stem big', 'data-testid': 'stem' }, q.stem), h('div', { class: 'u-choices' }, q.options.map((o, i) => h('button', {
      type: 'button', class: `u-choice${chosen[q.pos] === i ? ' on' : ''}`, 'data-testid': `opt-${i}`, onclick: async () => {
        chosen[q.pos] = i;
        paint();
        try {
          const res = await ctx.api.answer(v.attempt, q.pos, i);
          if (res.time_up) {
            done = true;
            clearInterval(tick);
            result(ctx, el, await ctx.api.result(card.id), card);
          }
        } catch (e) {
          ctx.fail(e);
        }
      } }, h('b', {}, LETTERS[i]), h('span', {}, o)))));
    dots.replaceChildren(...v.questions.map((x, k) => h('button', { type: 'button', class: `u-dot${k === s.idx ? ' on' : ''}${x.pos in chosen ? ' done' : ''}`,
      'aria-label': String(k + 1), onclick: () => { s.idx = k; paint(); } }, String(k + 1))));
    prev.disabled = s.idx === 0;
    next.hidden = s.idx === n - 1;
    submit.hidden = s.idx !== n - 1;
  };
  const prev = h('button', { type: 'button', class: 'u-btn ghost', 'data-testid': 'prev', onclick: () => { s.idx -= 1; paint(); } }, P('app.prev'));
  const next = h('button', { type: 'button', class: 'u-btn', 'data-testid': 'next', onclick: () => { s.idx += 1; paint(); } }, P('app.next'));
  const submit = h('button', { type: 'button', class: 'u-btn', 'data-testid': 'submit', onclick: async () => {
    const blank = v.questions.length - Object.keys(chosen).length;
    const ask = blank ? `${P('app.submit_ask')} ${P('app.submit_blank', { n: blank })}` : P('app.submit_ask');
    if (await confirmBox(ctx.root, ask, P('app.submit_yes'), P('app.cancel'))) await finish();
  } }, P('app.submit'));
  el.replaceChildren(h('div', { class: 'u-solve', 'data-testid': 'solving' }, h('div', { class: 'u-solve-top' }, count, h('span', { class: 'u-time' },
    h('small', {}, P('app.time_left')), timer)), bar, stage, h('div', { class: 'u-row nav' }, prev, next, submit), dots));
  paint();
}

async function start(ctx, el, card) {
  try {
    solving(ctx, el, await ctx.api.start(card.id), card);
  } catch (e) {
    ctx.fail(e);
  }
}

export async function renderSolve(ctx, el, id) {
  const { P } = ctx;
  const t = tt(ctx);
  const card = await ctx.api.test(id);
  if (card.open) {
    solving(ctx, el, await ctx.api.attempt(card.open), card);
    return card.title;
  }
  if (card.done) {
    result(ctx, el, await ctx.api.result(id), card);
    return card.title;
  }
  ctx.state.hold = false;
  const info = [questions(t, ctx.lang, card.count), minutes(t, ctx.lang, card.minutes)];
  el.append(h('div', { class: 'u-hero' }, h('h2', { 'data-testid': 'card-title' }, card.retest ? `🔁 ${card.title}` : card.title), h('p', {}, info.join(' · ')),
    card.deadline ? h('p', {}, `${P('lbl.deadline')}: ${when(t, ctx.lang, card.deadline, ctx.now())}`) : null,
    card.attempts > 1 ? h('p', {}, P('app.attempts_left', { left: card.left, all: card.attempts })) : null),
  h('p', { class: 'u-lead' }, P('app.rules')),
  card.closed ? h('p', { class: 'u-note' }, P('err.closed'))
    : h('button', { type: 'button', class: 'u-btn big', 'data-testid': 'start', onclick: () => start(ctx, el, card) }, P('app.start')));
  return card.title;
}
