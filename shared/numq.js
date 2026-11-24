// JS port of testustasi/core/numq.py: years, percentages and counts become "qaysi yilda", "necha foiz", "nechta".
import { cap, low, wordRe } from './text.js';
import { COUNTERS, counterOf, numberWord } from './uzwords.js';

const YEAR = /^([0-9]{3,4})-yil(da|dan|i|ga|ning|gi)?$/;
const PCT_CASE = /^ ?(ga|dan|ni|da|ning)(?![a-z])/;
const spans = (s) => [...s.matchAll(wordRe())].map((m) => [m[0], m.index, m.index + m[0].length]);

export function find(sentence) {
  const sp = spans(sentence);
  const toks = sp.map((x) => x[0]);
  for (let i = 0; i < sp.length; i++) {
    const [tok, start, end] = sp[i];
    const y = YEAR.exec(tok);
    if (y) return { kind: 'year', value: Number(y[1]), start, end, ask: `qaysi yil${y[2] ?? ''}`, counter: 'yil' };
    const got = numberWord(toks, i);
    if (got === null) continue;
    const [value, used] = got;
    const lastEnd = sp[i + used - 1][2];
    const nxt = i + used < toks.length ? toks[i + used] : '';
    if (value < 2 || low(nxt) === 'dan' || low(nxt) === '-' || sentence.slice(lastEnd, lastEnd + 1) === '-' || (i && low(toks[i - 1]) === 'dan')) return null;
    if (i && numberWord(toks, i - 1) !== null) continue;
    if (sentence.slice(lastEnd, lastEnd + 1) === '%') {
      const m = PCT_CASE.exec(sentence.slice(lastEnd + 1));
      return { kind: 'pct', value, start, end: m ? lastEnd + 1 + m[0].length : lastEnd + 1, ask: `necha foiz${m ? m[1] : ''}`, counter: 'foiz' };
    }
    const lastTok = toks[i + used - 1];
    if (low(lastTok).endsWith('ta') && !/^[0-9]/.test(lastTok)) return { kind: 'count', value, start, end: lastEnd, ask: 'nechta', counter: 'ta' };
    if (low(nxt) === 'ta') return { kind: 'count', value, start, end: sp[i + used][2], ask: 'nechta', counter: 'ta' };
    const c = nxt ? counterOf(nxt) : null;
    if (c === null) continue;
    const [counter, suf] = c;
    if (suf.endsWith('gacha') && ` ${low(sentence)} `.includes(' dan ')) return null;
    const [, nstart, nend] = sp[i + used];
    return { kind: counter === 'foiz' ? 'pct' : 'count', value, start, end: nend, ask: `necha ${sentence.slice(nstart, nend)}`, counter };
  }
  return null;
}

export function label(kind, value) {
  if (kind === 'year') return `${value}-yil`;
  if (kind === 'pct') return `${value}%`;
  return String(value);
}

export function others(sentences, kind, counter, value) {
  const seen = [];
  for (const s of sentences) {
    const f = find(s);
    if (f && f.kind === kind && (kind !== 'count' || f.counter === counter) && f.value !== value && !seen.includes(f.value)) seen.push(f.value);
  }
  return seen.sort((a, b) => Math.abs(a - value) - Math.abs(b - value) || a - b);
}

export function near(kind, value) {
  const half = Math.floor((value + 1) / 2);
  if (kind === 'year') return [value + 10, value - 10, value + 100, value - 100, value + 50, value - 50, value + 20, value - 20].filter((x) => x > 0 && x <= 2100);
  if (kind === 'pct') return [value + 10, value - 10, value * 2, half, value + 20, value - 5, value + 5].filter((x) => x >= 1 && x <= 100);
  const out = value <= 10 ? [value + 1, value - 1, value + 2, value - 2, value + 3, value + 4]
    : [value * 2, half, value + half, value * 3, value + Math.floor((value + 3) / 4)];
  return out.filter((x) => x >= 1);
}

export function question(sentence, sentences) {
  const f = find(sentence);
  if (f === null) return null;
  const ask = f.start === 0 ? cap(f.ask) : f.ask;
  const stem = `${(sentence.slice(0, f.start) + ask + sentence.slice(f.end)).replace(/[ .!]+$/, '')}?`;
  const pool = [];
  for (const x of [...others(sentences, f.kind, f.counter, f.value), ...near(f.kind, f.value)]) if (x !== f.value && !pool.includes(x)) pool.push(x);
  if (pool.length < 3) return null;
  return { stem, answer: label(f.kind, f.value), distractors: pool.slice(0, 3).map((x) => label(f.kind, x)), kind: f.kind,
    counter: COUNTERS.has(f.counter) ? f.counter : '' };
}
