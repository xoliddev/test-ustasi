// The teacher's home: tests (drafts and published, with how many finished), classes (students and the invite link) and
// "Yangi test" (paste a text, choose how many questions and how hard; a PDF goes to the bot as a file).
import { dateText } from '../shared/i18n.js';
import { localDay } from '../shared/clock.js';
import { chips, h } from './util.js';

const COUNTS = [5, 10, 15, 20];
const MIXES = ['easy', 'mixed', 'hard'];

export async function renderTests(ctx, el) {
  const { P } = ctx;
  const { items } = await ctx.api.tests();
  if (!items.length) {
    el.append(h('p', { class: 'u-empty' }, P('app.tests_none')));
    return P('app.tab_tests');
  }
  const day = (ms) => dateText((l, k, p) => ctx.T(l, k, p), ctx.lang, localDay(ms));
  el.append(h('div', { class: 'u-list', 'data-testid': 'tests' }, items.map((t) => {
    const status = t.status === 'draft' ? 'draft' : t.parent ? 'retest' : 'published';
    return h('button', { type: 'button', class: `u-item st-${status}`, 'data-testid': `test-${t.id}`, onclick: () => ctx.open({ view: 'test', id: t.id }) },
      h('div', { class: 'u-item-top' }, h('b', {}, t.title), h('span', { class: `u-chip ${status}` }, P(`app.st_${status}`))),
      h('div', { class: 'u-item-sub' }, [t.class, P('fmt.questions', { n: t.questions }), day(t.published_at ?? t.created_at)].filter(Boolean).join(' · ')),
      t.status === 'published' ? h('div', { class: 'u-meter' }, h('i', { style: { width: `${t.people ? Math.round((100 * t.done) / t.people) : 0}%` } }),
        h('span', {}, P('app.done_of', { a: t.done, b: t.people }))) : null);
  })));
  return P('app.tab_tests');
}

export async function renderClasses(ctx, el) {
  const { P } = ctx;
  const { items } = await ctx.api.classes();
  const list = h('div', { class: 'u-list' });
  const detail = async (k, box) => {
    if (box.childElementCount) {
      box.replaceChildren();
      return;
    }
    const d = await ctx.api.klass(k.id);
    const link = h('div', { class: 'u-link' });
    box.append(h('h4', {}, P('app.students')), d.students.length ? h('p', { class: 'u-names' }, d.students.map((s) => s.name).join(', '))
      : h('p', { class: 'u-empty' }, P('app.students_none')),
    h('button', { type: 'button', class: 'u-btn ghost', onclick: async () => {
      const inv = await ctx.api.invite(k.id).catch(ctx.fail);
      if (!inv) return;
      link.replaceChildren(h('small', {}, P('app.invite', { days: inv.days })), h('code', {}, inv.link),
        h('button', { type: 'button', class: 'u-btn ghost sm', onclick: () => { navigator.clipboard?.writeText(inv.link).catch(() => {}); ctx.toast(P('app.copied')); } },
          P('app.copy')));
    } }, P('app.invite_get')), link);
  };
  for (const k of items) {
    const box = h('div', { class: 'u-detail' });
    list.append(h('div', { class: 'u-item' }, h('button', { type: 'button', class: 'u-item-top plain', 'data-testid': `class-${k.id}`, onclick: () => detail(k, box) },
      h('b', {}, k.name), h('span', { class: 'u-chip' }, P('fmt.students', { n: k.students }))), box));
  }
  const name = h('input', { class: 'u-input', maxlength: 24, placeholder: P('app.class_new'), 'aria-label': P('app.class_new') });
  const add = h('button', { type: 'button', class: 'u-btn', onclick: async () => {
    try {
      await ctx.api.addClass(name.value);
      await ctx.refresh();
    } catch (e) {
      ctx.fail(e);
    }
  } }, P('app.class_add'));
  el.append(items.length ? list : h('p', { class: 'u-empty' }, P('app.classes_none')), h('div', { class: 'u-row' }, name, add));
  return P('app.tab_classes');
}

export async function renderNew(ctx, el) {
  const { P } = ctx;
  const pick = ctx.state.newTest ?? (ctx.state.newTest = { n: 10, mix: 'mixed' });
  const text = h('textarea', { class: 'u-text', rows: 9, maxlength: 30000, placeholder: P('app.new_text'), 'aria-label': P('app.new_text'), 'data-testid': 'new-text' });
  const count = h('small', { class: 'u-hint' });
  const paintCount = () => { count.textContent = P('app.chars', { n: Array.from(text.value).length }); };
  text.addEventListener('input', paintCount);
  paintCount();
  const title = h('input', { class: 'u-input', maxlength: 80, placeholder: P('app.new_name'), 'aria-label': P('app.new_name') });
  const go = h('button', { type: 'button', class: 'u-btn big', 'data-testid': 'new-make', onclick: async () => {
    go.disabled = true;
    try {
      const d = await ctx.api.draft({ text: text.value, title: title.value, n: pick.n, mix: pick.mix });
      await ctx.open({ view: 'test', id: d.id });
    } catch (e) {
      ctx.fail(e);
      go.disabled = false;
    }
  } }, P('app.new_make'));
  el.append(h('h3', { class: 'u-h' }, P('app.new_title')), h('p', { class: 'u-lead' }, P('app.new_lead')), text, count, title,
    h('label', { class: 'u-label' }, P('app.new_count')), chips(COUNTS.map((n) => [n, String(n)]), pick.n, (v) => { pick.n = v; }),
    h('label', { class: 'u-label' }, P('app.new_mix')), chips(MIXES.map((m) => [m, P(`app.mix_${m}`)]), pick.mix, (v) => { pick.mix = v; }), go);
  return P('app.tab_new');
}
