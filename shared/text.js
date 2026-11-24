// JS port of testustasi/core/text.py: text helpers shared by the generator, the quote check and the bot. Explicit
// character classes only, so the browser splits, normalises and hashes exactly like the server.
const cc = (n) => String.fromCharCode(n);
const CONTROL = new RegExp(`[\\x00-\\x08\\x0b-\\x1f\\x7f${cc(0x200b)}-${cc(0x200f)}${cc(0x202a)}-${cc(0x202e)}${cc(0x2066)}-${cc(0x2069)}\\ufeff]`, 'g');
const SPACE = /[ \t\n\r\f\v\u00a0\u2028\u2029\u3000]+/;
const HSPACE = /[ \t\f\v\u00a0\u3000]+/g;
const APOS = /[\u02bb\u02bc\u2019\u2018`\u00b4\u2032]/g;
export const LETTER = 'A-Za-z\\u00c0-\\u024f\\u0400-\\u04ff';
const WORD_SRC = `[${LETTER}0-9](?:[${LETTER}0-9']|-(?=[${LETTER}0-9]))*`;
export const wordRe = () => new RegExp(WORD_SRC, 'g');
const WORD_FULL = new RegExp(`^${WORD_SRC}$`);
const NOT_WORD = new RegExp(`[^${LETTER}0-9]+`);
const ALPHA = /\p{L}/u;
const enc = new TextEncoder();

export const CYR = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'yo', ж: 'j', з: 'z', и: 'i', й: 'y', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p',
  р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'x', ц: 's', ч: 'ch', ш: 'sh', щ: 'sh', ъ: "'", ы: 'i', ь: '', э: 'e', ю: 'yu', я: 'ya',
  ў: "o'", қ: 'q', ғ: "g'", ҳ: 'h',
};
const VOWELS = new Set('аеёиоуэюяўы');

export class InputError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

/** Length in code points (like Python's len). */
export const len = (s) => Array.from(s).length;

export const clean = (text, limit) => Array.from(String(text ?? '').replace(CONTROL, ' ').split(SPACE).filter(Boolean).join(' '))
  .slice(0, limit).join('');

export function normalizeSource(text) {
  let s = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n').normalize('NFC');
  s = s.replace(CONTROL, ' ').replace(APOS, "'");
  s = s.replaceAll('\u2013', '—').replaceAll('\u2012', '—').replaceAll(' - ', ' — ');
  const out = [];
  for (const raw of s.split('\n')) {
    const line = raw.replace(HSPACE, ' ').trim();
    if (line || (out.length && out[out.length - 1])) out.push(line);
  }
  return out.join('\n').trim();
}

export function latin(text) {
  let out = '';
  let prev = ' ';
  for (const ch of String(text).toLowerCase()) {
    if (ch === 'е' && (!ALPHA.test(prev) || VOWELS.has(prev) || prev === 'ъ' || prev === 'ь')) out += 'ye';
    else out += CYR[ch] ?? ch;
    prev = ch;
  }
  return out.replace(APOS, "'");
}

export function uzCyrillic(text) {
  let cyr = 0;
  let lat = 0;
  for (const ch of text) {
    if (ch >= 'Ѐ' && ch <= 'ӿ') cyr += 1;
    else if (ch.toLowerCase() >= 'a' && ch.toLowerCase() <= 'z' && ch.length === 1) lat += 1;
  }
  const lo = text.toLowerCase();
  return cyr > lat && ['ў', 'қ', 'ғ', 'ҳ'].some((c) => lo.includes(c));
}

export function toLatin(text) {
  let out = '';
  let prev = ' ';
  for (const ch of text) {
    const lo = ch.toLowerCase();
    const t = lo === 'е' && (!ALPHA.test(prev) || VOWELS.has(prev.toLowerCase()) || 'ъь'.includes(prev.toLowerCase())) ? 'ye' : CYR[lo] ?? ch;
    out += ch !== lo && lo in CYR ? t.slice(0, 1).toUpperCase() + t.slice(1) : t;
    prev = ch;
  }
  return out;
}

export const normMatch = (text) => latin(String(text).normalize('NFC')).replaceAll("'", '').split(NOT_WORD).filter(Boolean).join(' ');
export const words = (text) => String(text).match(wordRe()) ?? [];
export const isWord = (w) => WORD_FULL.test(w);
export const low = (w) => latin(w);
export const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);

export function h32(text) {
  let h = 0x811c9dc5;
  for (const b of enc.encode(text)) {
    h ^= b;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

export const rnd = (key) => h32(key) / 4_294_967_296;

export function short(text, limit) {
  const a = Array.from(text);
  if (a.length <= limit) return text;
  const cut = a.slice(0, limit - 1).join('');
  const sp = cut.lastIndexOf(' ');
  return `${(sp > limit / 2 ? cut.slice(0, sp) : cut).replace(/[ ,;:—]+$/, '')}…`;
}

export function checkedText(value, lo, hi, code) {
  if (typeof value !== 'string') throw new InputError(code);
  const s = clean(value, hi + 1);
  if (len(s) > hi || Array.from(s).filter((ch) => /[\p{L}\p{N}]/u.test(ch)).length < lo) throw new InputError(code);
  return s;
}

export function whole(value, lo, hi, code) {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < lo || value > hi) throw new InputError(code);
  return value;
}

/** Python-like comparison of key arrays (numbers and strings), for deterministic sorting. */
export function cmp(a, b) {
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if (a[i] === b[i]) continue;
    if (a[i] === undefined) return -1;
    if (b[i] === undefined) return 1;
    return a[i] < b[i] ? -1 : 1;
  }
  return 0;
}
export const sortBy = (arr, key) => arr.sort((x, y) => cmp(key(x), key(y)));
