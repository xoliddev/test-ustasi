// JS port of testustasi/i18n.py: locale templates with HTML-escaped parameters, dates relative to today, percentages,
// counts, times and the analysis flags. The bot simulated in the demo and the Mini App use these.
import { civil, hhmm, localDay, localMinute } from './clock.js';

export class Raw {
  constructor(html) {
    this.html = String(html);
  }

  toString() {
    return this.html;
  }
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;' };
export const esc = (s) => String(s).replace(/[&<>]/g, (c) => ESC[c]);
export const normLang = (code) => (String(code ?? '').slice(0, 2).toLowerCase() === 'ru' ? 'ru' : 'uz');

export function makeT(catalogs) {
  return (lang, key, params = {}) => {
    const l = normLang(lang);
    const template = catalogs[l]?.[key] || catalogs.uz?.[key] || key;
    return template.replace(/\{(\w+)\}/g, (m, k) => (k in params ? (params[k] instanceof Raw ? params[k].html : esc(params[k])) : m));
  };
}

const ENT = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#x27;': "'", '&#39;': "'" };
export const plain = (html) => String(html).replace(/<[^>]+>/g, '').replace(/&(amp|lt|gt|quot|#x27|#39);/g, (m) => ENT[m]);

export function dateText(t, lang, day) {
  const [, m, d] = civil(day);
  return t(lang, 'fmt.day', { d, month: t(lang, `month.${m}`) });
}

export function when(t, lang, ms, now) {
  const day = localDay(ms);
  const time = hhmm(localMinute(ms));
  const today = localDay(now);
  if (day === today) return t(lang, 'fmt.today', { time });
  if (day === today + 1) return t(lang, 'fmt.tomorrow', { time });
  return t(lang, 'fmt.when', { date: dateText(t, lang, day), time });
}

export const num = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
export const pct = (t, lang, n) => t(lang, 'fmt.pct', { n });
export const questions = (t, lang, n) => t(lang, 'fmt.questions', { n });
export const minutes = (t, lang, n) => t(lang, 'fmt.minutes', { n });
export const students = (t, lang, n) => t(lang, 'fmt.students', { n });
export const mmss = (t, lang, seconds) => t(lang, 'fmt.time', { m: Math.floor(seconds / 60), s: String(seconds % 60).padStart(2, '0') });

export function flagText(t, lang, r) {
  if (r.flag === null || r.flag === undefined) return null;
  if ((r.flag === 'key' || r.flag === 'hard') && r.pick) return t(lang, `flag.${r.flag}_pick`, { pct: r.pick.pct, letter: r.pick.letter });
  return t(lang, `flag.${r.flag}`);
}
