// JS port of testustasi/core/passages.py: a source text -> headings, paragraphs and numbered passages of sentences.
import { normalizeSource, toLatin, uzCyrillic, wordRe } from './text.js';

export const MAX_PASSAGE = 900;
export const TARGET_PASSAGE = 650;
export const MIN_PASSAGE = 140;
const END = /[.!?…:;»"')]$/;
const ABBR = new Set(['h.k', 'mil', 'sm', 'km', 'mm', 'kg', 'm', 'y', 'asr', 'b', 't', 'va h.k', 'masalan', "ya'ni", 'prof', 'dots', 'akad']);
const SPLIT = /(?<=[.!?…])[»"')]?\s+(?=[«"(A-ZА-ЯЁЎҚҒҲ0-9])/g;
const ALPHA = /\p{L}/u;
const L = (s) => Array.from(s).length;

export const isLower = (ch) => ch !== ch.toUpperCase();
export const isUpper = (ch) => ch !== ch.toLowerCase() || (ch >= '0' && ch <= '9' && ch.length === 1) || (ch !== '' && '«"('.includes(ch));

export function isHeading(line) {
  if (!line || L(line) > 70 || '.!;:,'.includes(line.at(-1))) return false;
  const n = (line.match(wordRe()) ?? []).length;
  return n >= 1 && n <= 8 && (line.at(-1) === '?' || !END.test(line));
}

export function sentences(text) {
  const out = [];
  let buf = '';
  let pos = 0;
  for (const m of text.matchAll(SPLIT)) {
    const piece = text.slice(pos, m.index);
    pos = m.index + m[0].length;
    const candidate = buf ? `${buf} ${piece}`.trim() : piece.trim();
    const last = Array.from(candidate).slice(-8).join('').match(wordRe()) ?? [];
    const tail = last.length ? last[last.length - 1].toLowerCase() : '';
    if (ABBR.has(tail) || (L(tail) === 1 && ALPHA.test(tail))) {
      buf = candidate;
      continue;
    }
    out.push(candidate);
    buf = '';
  }
  const rest = text.slice(pos).trim();
  if (rest) out.push(buf ? `${buf} ${rest}`.trim() : rest);
  else if (buf) out.push(buf);
  return out.filter(Boolean);
}

function paragraphs(body) {
  const items = [];
  let heading = null;
  const blocks = body.split('\n\n');
  blocks.forEach((block, bi) => {
    const lines = block.split('\n').filter(Boolean);
    let para = '';
    lines.forEach((line, i) => {
      const nxt = i + 1 < lines.length ? lines[i + 1] : '';
      if (!para && isHeading(line) && (nxt || bi < blocks.length - 1)) {
        heading = line;
        return;
      }
      para = para.endsWith('-') && isLower(line.slice(0, 1)) ? para.slice(0, -1) + line : `${para} ${line}`.trim();
      if (END.test(line) && nxt && (isUpper(nxt.slice(0, 1)) || isHeading(nxt))) {
        items.push([heading, para]);
        para = '';
      }
    });
    if (para) items.push([heading, para]);
  });
  return items;
}

function chunks(text) {
  if (L(text) <= MAX_PASSAGE) return [text];
  const out = [];
  let cur = '';
  for (const s of sentences(text)) {
    if (cur && L(cur) + 1 + L(s) > TARGET_PASSAGE) {
      out.push(cur);
      cur = s;
    } else cur = `${cur} ${s}`.trim();
  }
  if (cur) out.push(cur);
  return out;
}

export function split(text) {
  let body = normalizeSource(text);
  if (uzCyrillic(body)) body = toLatin(body);
  const passages = [];
  for (const [heading, para] of paragraphs(body)) {
    for (const piece of chunks(para)) {
      const prev = passages.length ? passages[passages.length - 1] : null;
      if (prev && prev.heading === heading && (L(prev.text) < MIN_PASSAGE || L(piece) < MIN_PASSAGE) && L(prev.text) + L(piece) <= MAX_PASSAGE) {
        prev.text = `${prev.text} ${piece}`;
        continue;
      }
      passages.push({ n: passages.length + 1, heading, text: piece });
    }
  }
  for (const p of passages) p.sentences = sentences(p.text);
  return passages;
}

export function canonical(passages) {
  const out = [];
  let last = null;
  for (const p of passages) {
    if (p.heading && p.heading !== last) out.push(p.heading);
    last = p.heading;
    out.push(p.text);
  }
  return out.join('\n\n');
}

export function titleOf(passages, fallback = '') {
  const first = passages.find((p) => p.heading)?.heading;
  return (first || fallback).replace(/\?+$/, '').trim();
}
