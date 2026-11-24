// JS port of testustasi/core/generate.py: the rule-based question generator (definitions both ways, numbers, gaps),
// distractors from the same text, fewer questions rather than bad ones.
import { question as numQuestion } from './numq.js';
import { canonical, split, titleOf } from './passages.js';
import { PRONOUN_START, definitions, keyTerms, topics } from './terms.js';
import { cap, h32, low, normMatch, sortBy, wordRe, words } from './text.js';
import { inflect, stem } from './uzwords.js';

export const LEVEL = { def: 1, rev: 2, num: 2, gap: 3 };
export const ORDERS = { easy: ['def', 'num', 'rev', 'gap'], hard: ['gap', 'rev', 'num', 'def'], mixed: ['def', 'gap', 'num', 'rev'] };
const WEIGHTS = { easy: { def: 5, num: 3, rev: 2, gap: 1 }, hard: { gap: 5, rev: 3, num: 2, def: 1 }, mixed: { def: 4, gap: 4, num: 2, rev: 2 } };
const SAFE = ['', 'ni', 'ning', 'ga', 'ka', 'qa', 'da', 'dan'];
const PROCESS = new Set(['jarayon', 'hodisa', 'harakat', 'usul', 'qaytish']);
export const MIXES = Object.keys(ORDERS);
export const COUNTS = [5, 10, 15, 20];
const L = (s) => Array.from(s).length;

export function analyse(text, title = '') {
  const ps = split(text);
  const defs = definitions(ps);
  const terms = keyTerms(ps, defs);
  const name = title || titleOf(ps, '');
  return { passages: ps, defs, terms, topics: topics(ps, defs, terms, name), title: name, body: canonical(ps) };
}

const stems = (text) => words(text).map(stem);

function related(a, b) {
  const wa = a.key.split(' ');
  const wb = b.key.split(' ');
  if (wa.every((x) => wb.includes(x)) || wb.every((x) => wa.includes(x))) return true;
  return wa.some((x) => wb.some((y) => L(x) >= 4 && L(y) >= 4 && x !== y && (x.includes(y) || y.includes(x))));
}

function distractors(answer, terms, context, seed) {
  const seen = new Set(stems(context));
  const ranked = [];
  for (const k of terms) {
    if (k.key === answer.key || related(k, answer) || k.key.split(' ').every((w) => seen.has(w))) continue;
    const same = answer.cls && k.cls === answer.cls ? 0 : PROCESS.has(k.cls) !== PROCESS.has(answer.cls) ? 2 : 1;
    const group = k.kind === 'minor' ? 2 : (k.kind === 'def') === (answer.kind === 'def') ? 0 : 1;
    ranked.push([[same, group, Math.floor(Math.abs(L(k.text) - L(answer.text)) / 10), h32(`${seed}|${k.key}`)], k]);
  }
  sortBy(ranked, (x) => x[0]);
  return ranked.length >= 3 ? ranked.slice(0, 3).map((x) => x[1]) : null;
}

function q(kind, p, s, stemQ, answer, others, expl, quote, key, topic) {
  const opts = others.map(cap);
  if (new Set([answer, ...opts].map(normMatch)).size < 4) return null;
  const pos = h32(`${kind}|${stemQ}`) % 4;
  opts.splice(pos, 0, cap(answer));
  return { kind, passage: p, sent: s, uid: `${kind}:${p}:${s}`, key, level: LEVEL[kind], topic, stem: stemQ, options: opts, correct: pos, explanation: expl, quote };
}

function usable(s) {
  const ws = words(s);
  return L(s) >= 25 && L(s) <= 220 && !s.endsWith('?') && ws.length >= 4 && !PRONOUN_START.has(low(ws[0]));
}

function gap(s, p, si, a, titleKeys) {
  if (s.includes("bo'lmasa") || low(s).includes('agar ') || s.includes('sa, ')) return null;
  const toks = [...s.matchAll(wordRe())];
  const st = toks.map((m) => stem(m[0]));
  for (const t of a.terms) {
    const ks = t.key.split(' ');
    if (t.kind === 'minor' || ks.every((k) => titleKeys.has(k))) continue;
    for (let j = 0; j < st.length - ks.length + 1; j++) {
      if (!ks.every((k, i) => st[j + i] === k)) continue;
      const lastTok = toks[j + ks.length - 1];
      const last = low(lastTok[0]);
      const tw = t.text.split(' ');
      const base = low(tw[tw.length - 1]);
      const allowed = t.kind === 'def' || t.kind === 'pair' ? SAFE : ['', 'ni'];
      if (!last.startsWith(base) || !allowed.includes(last.slice(base.length))) break;
      const suf = last.slice(base.length);
      const start = toks[j].index;
      const end = lastTok.index + lastTok[0].length;
      const gapped = `${s.slice(0, start)}____${s.slice(end)}`;
      const ds = distractors(t, a.terms, gapped, s);
      if (ds === null) break;
      return q('gap', p, si, `Bo'sh joyga mos javobni tanlang: «${gapped}»`, inflect(t.text, suf), ds.map((x) => inflect(x.text, suf)),
        '', s, t.key, a.topics[p]);
    }
  }
  return null;
}

export function candidates(a) {
  const out = [];
  const sentences = a.passages.flatMap((p) => p.sentences);
  const byKey = new Map(a.terms.map((t) => [t.key, t]));
  for (const d of a.defs) {
    const t = byKey.get(d.key);
    const topic = a.topics[d.p];
    const verb = d.form === 'called' ? 'nima deyiladi' : d.form === 'said' ? 'nima deb aytiladi' : 'nima deb ataladi';
    const stemQ = `${cap(d.def)}${d.suf} ${verb}?`;
    const ds = distractors(t, a.terms, stemQ, stemQ);
    if (ds) {
      const x = q('def', d.p, d.s, stemQ, t.text, ds.map((y) => y.text), `${cap(d.def)} — bu ${t.text}.`, d.sentence, t.key, topic);
      if (x) out.push(x);
    }
    const own = d.key.split(' ');
    const others = a.defs.filter((x) => x.key !== d.key && L(x.def) <= 110 && !stems(x.def).some((w) => own.includes(w)) && !related(byKey.get(x.key), t));
    sortBy(others, (x) => [x.cls === d.cls ? 0 : 1, Math.floor(Math.abs(L(x.def) - L(d.def)) / 8), h32(`rev|${d.key}|${x.key}`)]);
    if (L(d.def) <= 110 && others.length >= 3) {
      const x = q('rev', d.p, d.s, `${cap(t.text)} deb nimaga aytiladi?`, d.def, others.slice(0, 3).map((y) => y.def), `${cap(t.text)} — ${d.def}.`, d.sentence, t.key, topic);
      if (x) out.push(x);
    }
  }
  const defined = new Set(a.defs.map((d) => `${d.p}:${d.s}`));
  const titleKeys = new Set(stems(a.title));
  for (const p of a.passages) {
    p.sentences.forEach((s, si) => {
      if (defined.has(`${p.n}:${si}`) || !usable(s)) return;
      const nq = numQuestion(s, sentences);
      if (nq) {
        const x = q('num', p.n, si, nq.stem, nq.answer, nq.distractors, '', s, `num:${p.n}:${si}`, a.topics[p.n]);
        if (x) out.push(x);
      }
      const g = gap(s, p.n, si, a, titleKeys);
      if (g) out.push(g);
    });
  }
  return sortBy(out, (x) => [x.passage, x.sent, x.uid]);
}

export function select(cands, n, mix = 'mixed', used = [], sameAnswer = false) {
  const order = ORDERS[mix] ?? ORDERS.mixed;
  const weight = WEIGHTS[mix] ?? WEIGHTS.mixed;
  const byP = new Map();
  for (const c of cands) {
    if (!byP.has(c.passage)) byP.set(c.passage, []);
    byP.get(c.passage).push(c);
  }
  const keys = new Set(sameAnswer ? [] : used.map((u) => u.key));
  const sents = new Set(used.map((u) => `${u.passage}:${u.sent}`));
  const uids = new Set(used.map((u) => u.uid));
  const chosen = [];
  const count = Object.fromEntries(order.map((k) => [k, 0]));
  const ps = [...byP.keys()].sort((x, y) => x - y);
  let moved = true;
  while (chosen.length < n && moved) {
    moved = false;
    for (const p of ps) {
      if (chosen.length >= n) break;
      const free = byP.get(p).filter((c) => !uids.has(c.uid) && !keys.has(c.key) && !sents.has(`${c.passage}:${c.sent}`));
      if (!free.length) continue;
      const rank = (c) => [Math.floor(((count[c.kind] + 1) * 60) / weight[c.kind]), order.indexOf(c.kind), c.sent, c.uid];
      const c = sortBy([...free], rank)[0];
      count[c.kind] += 1;
      chosen.push(c);
      keys.add(c.key);
      sents.add(`${c.passage}:${c.sent}`);
      uids.add(c.uid);
      moved = true;
    }
  }
  return sortBy(chosen, (x) => [x.passage, x.sent, x.uid]);
}

export const generate = (text, n = 10, mix = 'mixed', title = '') => select(candidates(analyse(text, title)), n, mix);
