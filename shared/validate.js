// JS port of testustasi/core/validate.py: the deterministic checks every drafted question must pass (shape, four
// distinct options, one correct, lengths, a quote that occurs in the source, a grounded answer), and the field rules
// for a teacher's edit.
import { InputError, clean, h32, normMatch } from './text.js';

export const LIMITS = { stem: [8, 300], option: [1, 120], explanation: [0, 400], topic: [2, 40], quote: [12, 400] };
const LEVELS = { oson: 1, "o'rta": 2, orta: 2, qiyin: 3, easy: 1, medium: 2, hard: 3 };
const L = (s) => Array.from(s).length;
const ALNUM = /[\p{L}\p{N}]/u;

export class Rejected extends Error {}

export function field(value, name) {
  const [lo, hi] = LIMITS[name];
  if (typeof value !== 'string') throw new Rejected(name);
  const s = clean(value, hi + 1);
  if (L(s) > hi || L(s) < lo || (lo && !ALNUM.test(s))) throw new Rejected(name);
  return s;
}

export function options(value) {
  if (!Array.isArray(value) || value.length !== 4) throw new Rejected('options');
  const opts = value.map((v) => field(v, 'option'));
  if (new Set(opts.map(normMatch)).size !== 4 || opts.some((o) => !normMatch(o))) throw new Rejected('distinct');
  return opts;
}

export function correctIndex(value) {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0 || value > 3) throw new Rejected('correct');
  return value;
}

export function occurs(quote, sourceNorm) {
  const q = normMatch(quote);
  return L(q) >= 12 && ` ${sourceNorm} `.includes(` ${q} `);
}

export function grounded(answer, quote) {
  const qwords = normMatch(quote).split(' ');
  for (const w of normMatch(answer).split(' ')) {
    if (/^[0-9]+$/.test(w) && qwords.includes(w)) return true;
    if (L(w) >= 3) {
      const head = Array.from(w).slice(0, Math.max(3, L(w) - 3)).join('');
      if (qwords.some((q) => L(q) >= 3 && q.startsWith(head))) return true;
    }
  }
  return false;
}

export function place(opts, correct, stem) {
  const pos = h32(`ai|${stem}`) % 4;
  const rest = opts.filter((_, i) => i !== correct);
  rest.splice(pos, 0, opts[correct]);
  return [rest, pos];
}

export function passageOf(quote, passages) {
  const q = normMatch(quote);
  for (const p of passages) if (q && normMatch(p.text).includes(q)) return p.n;
  return 0;
}

export function check(raw, sourceNorm, passages, topics) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Rejected('shape');
  const stem = field(raw.stem, 'stem');
  let opts = options(raw.options);
  let correct = correctIndex(raw.correct);
  const quote = field(raw.quote, 'quote');
  if (!occurs(quote, sourceNorm)) throw new Rejected('quote');
  if (!grounded(opts[correct], quote)) throw new Rejected('grounded');
  const expl = clean(typeof raw.explanation === 'string' ? raw.explanation : '', LIMITS.explanation[1]);
  const n = passageOf(quote, passages);
  let topic = raw.topic;
  topic = typeof topic === 'string' && L(clean(topic, 41)) >= 2 ? clean(topic, 40) : topics[n] ?? '';
  const level = LEVELS[String(raw.difficulty ?? '').trim().toLowerCase()] ?? 2;
  [opts, correct] = place(opts, correct, stem);
  return { kind: 'ai', passage: n, sent: -1, uid: `ai:${h32(normMatch(stem))}`, key: `ai:${h32(normMatch(opts[correct]))}`, level,
    topic: topic || (topics[n] ?? ''), stem, options: opts, correct, explanation: expl, quote };
}

export function accept(raws, sourceNorm, passages, topics, need, have = []) {
  const out = [];
  const why = {};
  const stems = new Set(have.map((q) => normMatch(q.stem)));
  for (const raw of Array.isArray(raws) ? raws : []) {
    if (out.length >= need) break;
    let q;
    try {
      q = check(raw, sourceNorm, passages, topics);
    } catch (e) {
      if (!(e instanceof Rejected)) throw e;
      why[e.message] = (why[e.message] ?? 0) + 1;
      continue;
    }
    if (stems.has(normMatch(q.stem))) {
      why.duplicate = (why.duplicate ?? 0) + 1;
      continue;
    }
    stems.add(normMatch(q.stem));
    out.push(q);
  }
  return [out, why];
}

export function edited(data, current) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new InputError('question');
  try {
    const stem = field(data.stem ?? current.stem, 'stem');
    const opts = options(data.options ?? current.options);
    const correct = correctIndex(data.correct ?? current.correct);
    const e = data.explanation ?? current.explanation;
    const explanation = typeof e === 'string' ? clean(e, LIMITS.explanation[1]) : '';
    const topic = field(data.topic || current.topic || 'Mavzu', 'topic');
    return { ...current, stem, options: opts, correct, explanation, topic };
  } catch (err) {
    if (err instanceof Rejected) throw new InputError(`q_${err.message}`);
    throw err;
  }
}
