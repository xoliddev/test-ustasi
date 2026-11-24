// JS port of testustasi/core/terms.py: definitions, key terms and passage topics.
import { cap, isWord, low, sortBy, words } from './text.js';
import { COUNTERS, STOP, caseStrip, isContent, stem } from './uzwords.js';

export const PRONOUN_START = new Set(['bu', 'u', 'ular', 'shu', 'ushbu', 'bunda', 'unda', 'uning', 'ularning', 'unga', 'undan', 'buning', 'shuning',
  'natijada', 'shunday', 'bular', "o'sha", 'uni', 'ularni', 'biroq', 'lekin', 'ammo', 'chunki', 'masalan', 'bunga']);
export const ADJ_END = ['li', 'siz', 'iy', 'viy', 'simon', 'dosh', 'dor', 'tik', 'chan'];
const DASH = /^(?<term>[^—,;:()«»]{2,60}?) — (?:bu )?(?<def>[^—]{8,220})\.$/u;
const NAMED = /^(?<head>.{8,240}?) deb (?:ham )?ataladi\.$/u;
const CALLED = /^(?<head>.{8,240}?) deyiladi\.$/u;
const SAID = /^(?<term>[^,;:]{2,60}?) deb (?<def>.{8,220}?)(?<suf>ga|ka|qa) aytiladi\.$/u;
const ends = (w, list) => list.some((e) => w.endsWith(e));
const L = (s) => Array.from(s).length;

function okTerm(ws) {
  if (ws.length < 1 || ws.length > 3 || ws.some((w) => !isWord(w) || /[0-9]/.test(w))) return false;
  const first = low(ws[0]);
  const last = low(ws[ws.length - 1]);
  return !STOP.has(first) && !PRONOUN_START.has(first) && !STOP.has(last) && L(last) >= 2;
}

function okDef(text) {
  const ws = words(text);
  if (ws.length < 3 || L(text) > 220 || PRONOUN_START.has(low(ws[0]))) return false;
  const tail = low(ws[ws.length - 1]);
  const finite = ws.some((w) => ends(low(w), ['adi', 'ydi', 'edi']));
  return !finite && !ends(tail, ['di', 'gan', 'ib', 'moqda']) && !` ${text} `.includes(' bu ') && !text.includes(', u ');
}

function repeated(seq, body, skip) {
  const k = seq.length;
  return body.some((st, i) => i !== skip && Array.from({ length: Math.max(0, st.length - k + 1) }, (_, j) => j)
    .some((j) => seq.every((x, q) => st[j + q] === x)));
}

function tailTerm(ws, body, idx) {
  let k = 1;
  while (k < 3 && ws.length - k > 3) {
    const prev = low(ws[ws.length - k - 1]);
    const first = low(ws[ws.length - k]);
    if (STOP.has(prev) || PRONOUN_START.has(prev) || ends(prev, ['lar', 'dan', 'ning', 'ni']) || (ends(prev, ['da', 'ga', 'ka', 'qa']) && stem(prev) !== prev)) break;
    const izofa = k === 1 && first.endsWith('i') && stem(prev) === prev && isContent(prev);
    const adjective = ends(prev, ADJ_END) && !prev.endsWith('dagi');
    if (izofa || adjective || repeated(ws.slice(ws.length - k - 1).map(stem), body, idx)) {
      k += 1;
      continue;
    }
    break;
  }
  if (k < 3 && ws.length - k > 3 && ws.slice(0, ws.length - k).map(stem).includes(stem(ws[ws.length - 1]))) k += 1;
  return k;
}

function match(s, body, idx) {
  let m = DASH.exec(s);
  if (m) {
    const { term, def } = m.groups;
    if (okTerm(term.split(' ')) && okDef(def)) return [term, def.endsWith('dir') && L(def) > 8 ? def.slice(0, -3) : def, '', 'dash'];
    return null;
  }
  m = SAID.exec(s);
  if (m) return okTerm(m.groups.term.split(' ')) && okDef(m.groups.def) ? [m.groups.term, m.groups.def, m.groups.suf, 'said'] : null;
  m = NAMED.exec(s);
  let form = 'named';
  if (!m) {
    m = CALLED.exec(s);
    form = 'called';
  }
  if (!m) return null;
  const ws = m.groups.head.split(' ');
  let term;
  let head;
  let suf;
  if (form === 'called') {
    let cut = -1;
    ws.slice(0, -1).forEach((w, i) => { if (ends(low(w), ['ga', 'ka', 'qa']) && L(w) > 4) cut = i; });
    if (cut < 2 || ws.length - cut - 1 > 3) return null;
    term = ws.slice(cut + 1);
    head = ws.slice(0, cut + 1);
    suf = low(ws[cut]).slice(-2);
    head = [...head.slice(0, -1), head[head.length - 1].slice(0, -2)];
  } else {
    const k = tailTerm(ws, body, idx);
    term = ws.slice(ws.length - k);
    head = ws.slice(0, ws.length - k);
    suf = '';
  }
  const d = head.join(' ');
  return okTerm(term) && okDef(d) ? [term.join(' '), d, suf, form] : null;
}

export function definitions(passages) {
  const body = passages.flatMap((p) => p.sentences.map((s) => words(s).map(stem)));
  const out = [];
  let idx = -1;
  for (const p of passages) {
    p.sentences.forEach((s, si) => {
      idx += 1;
      const found = match(s, body, idx);
      if (!found) return;
      const [term, d, suf, form] = found;
      const dw = words(d);
      out.push({ term, def: d, suf, form, p: p.n, s: si, sentence: s, key: words(term).map(stem).join(' '), cls: stem(dw[dw.length - 1]) });
    });
  }
  return out;
}

function display(forms, lower) {
  const bases = new Map();
  for (const [surface, n] of forms) {
    const ws = surface.split(' ');
    const base = [...ws.slice(0, -1), caseStrip(ws[ws.length - 1])].join(' ');
    bases.set(base, (bases.get(base) ?? 0) + n);
  }
  const out = sortBy([...bases.entries()], ([b, n]) => [-n, L(b), b])[0][0];
  return lower ? out.toLowerCase() : out;
}

export function keyTerms(passages, defs) {
  const counts = new Map();
  for (const p of passages) {
    p.sentences.forEach((s, si) => {
      const ws = words(s);
      ws.forEach((w, j) => {
        if (!isContent(w)) return;
        const keys = [[stem(w), w]];
        if (j && isContent(ws[j - 1]) && stem(ws[j - 1]) === low(ws[j - 1])) keys.push([`${stem(ws[j - 1])} ${stem(w)}`, `${ws[j - 1]} ${w}`]);
        for (const [key, surface] of keys) {
          if (!counts.has(key)) counts.set(key, { n: 0, sents: new Set(), forms: new Map(), lower: false });
          const c = counts.get(key);
          c.n += 1;
          c.sents.add(`${p.n}:${si}`);
          c.forms.set(surface, (c.forms.get(surface) ?? 0) + 1);
          c.lower = c.lower || (j > 0 && surface.slice(0, 1) !== surface.slice(0, 1).toUpperCase());
        }
      });
    });
  }
  const terms = new Map();
  for (const d of defs) {
    if (terms.has(d.key)) continue;
    let text = d.term;
    const c = counts.get(d.key);
    if ((d.form === 'dash' || d.form === 'said') && !(c && !c.lower)) text = text.slice(0, 1).toLowerCase() + text.slice(1);
    terms.set(d.key, { key: d.key, text, kind: 'def', cls: d.cls, n: c ? c.n : 1 });
  }
  for (const key of [...counts.keys()].sort()) {
    const c = counts.get(key);
    const pair = key.includes(' ');
    if (terms.has(key) || COUNTERS.has(key) || c.sents.size < 2 || c.n < 2) continue;
    const kind = pair ? 'pair' : c.n >= 3 ? 'word' : 'minor';
    const text = display(c.forms, c.lower);
    if (!pair && ((stem(text) !== low(text) && !low(text).endsWith('lar')) || ends(low(text), ADJ_END) || [...c.forms.keys()].every((f) => low(f) === key)
      || (kind === 'minor' && [...terms.keys()].some((t) => t.split(' ').includes(key))))) continue;
    terms.set(key, { key, text, kind, cls: '', n: c.n });
  }
  for (const key of [...terms.keys()].filter((k) => terms.get(k).kind === 'pair')) {
    for (const part of key.split(' ')) {
      const t = terms.get(part);
      if (t && (t.kind === 'word' || t.kind === 'minor') && t.n <= terms.get(key).n + 1) terms.delete(part);
    }
  }
  const order = { def: 0, pair: 1, word: 2, minor: 3 };
  return sortBy([...terms.values()], (t) => [order[t.kind], -t.n, t.key]);
}

export function topics(passages, defs, terms, title) {
  const out = {};
  for (const p of passages) {
    if (p.heading) {
      out[p.n] = Array.from(cap(p.heading.replace(/\?+$/, '').trim())).slice(0, 40).join('');
      continue;
    }
    const d = defs.find((x) => x.p === p.n);
    if (d) {
      out[p.n] = Array.from(cap(d.term)).slice(0, 40).join('');
      continue;
    }
    const stems = words(p.text).map(stem);
    let best = null;
    let score = 0;
    for (const t of terms) {
      const n = stems.filter((s) => s === t.key).length;
      if (n > score) {
        best = t;
        score = n;
      }
    }
    out[p.n] = Array.from(best ? cap(best.text) : title || 'Matn').slice(0, 40).join('');
  }
  return out;
}
