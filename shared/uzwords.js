// JS port of testustasi/core/uzwords.py: function words, the suffix stripper, inflecting an option, number words and
// counter words.
import { low } from './text.js';

const set = (s) => new Set(s.split(/\s+/).filter(Boolean));
export const STOP = set(`
va ham bilan uchun esa lekin ammo biroq chunki agar yoki hamda bu shu u ular uning ularning unda undan unga buni bunda
shunday shuning ushbu o'sha bir bitta har hamma barcha deyarli qariyb taxminan asosan faqat juda eng ko'p kam katta
kichik mayda yangi eski boshqa kabi deb emas bor yo'q edi ekan bo'ladi bo'lgan bo'lib bo'lsa bo'lishi mumkin qiladi
qilgan qiladigan hosil orqali tufayli sifatida tomonidan ataladi deyiladi aytiladi hisoblanadi iborat kerak nima kim
qanday qayer qachon nechta necha masalan ya'ni keyin oldin avval hozir doim ba'zi ko'pincha birinchi ikkinchi uchinchi
yil kun oy soat vaqt jarayon modda qism tur narsa holda ichida ustida ostida bo'yicha bo'ylab qarab qaraganda natijada
tarzda yerda ham-da bular shular o'z o'zi biri biridir sabab sababli bo'lmasa bo'lmagan yaxshi yuqori past ko'proq
kamroq oson qiyin asosiy umumiy turli muhim ayniqsa hatto yana endi so'ng undan-keyin ostidagi ustidagi`);
export const CASES = ['dagi', 'ning', 'gacha', 'dan', 'dir', 'ni', 'ga', 'ka', 'qa', 'da'];
export const POSSESSIVE = ['lari', 'si', 'i'];
const ADJ_I = ['li', 'iy', 'gi', 'ki', 'qi'];
const DA_ROOTS = new Set(['modda', 'parda', 'soda', 'banda', 'poda', 'sada', 'dunyoda', 'aslida', 'ayniqsa']);
export const VERBISH = ['adi', 'ydi', 'ladi', 'gan', 'gach', 'moqda', 'yapti', 'maydi', 'masdan', 'ishdi', 'edi', 'ibdi', 'ganda', 'gani',
  'ilgan', 'ilib', 'ib', 'moq', 'sin', 'ydilar', 'dilar'];
export const CAPS = ['ning', 'ni', 'ga', 'ka', 'qa', 'da', 'dan', 'dagi', 'lar', 'larda', 'lardan', 'larga', 'larni', 'larning', 'dir', ''];
export const UNITS = { bir: 1, ikki: 2, uch: 3, "to'rt": 4, besh: 5, olti: 6, yetti: 7, sakkiz: 8, "to'qqiz": 9 };
export const TENS = { "o'n": 10, yigirma: 20, "o'ttiz": 30, qirq: 40, ellik: 50, oltmish: 60, yetmish: 70, sakson: 80, "to'qson": 90 };
export const TA = { ikkita: 2, uchta: 3, "to'rtta": 4, beshta: 5, oltita: 6, yettita: 7, sakkizta: 8, "to'qqizta": 9, "o'nta": 10 };
export const COUNTERS = set(`
ta xil bosqich marta kun soat yil oy hafta daqiqa minut sekund metr kilometr km kg gramm litr gradus foiz qism
tur juft qavat bo'lim asr nafar dona qator sahifa gers santimetr sm millimetr mm tonna kishi shtat viloyat
qit'a okean sayyora`);
const COUNTER_LIST = [...COUNTERS].sort((a, b) => b.length - a.length || (a < b ? -1 : a > b ? 1 : 0));
const AFTER_COUNTER = new Set([...CAPS, 'i', 'si', 'ni', 'dan', 'ga', 'gacha', 'igacha', 'sigacha', 'lik', 'ligi', 'ini', 'ida', 'idan', 'iga', 'ining']);
const own = (o, k) => Object.hasOwn(o, k);
const VOW = new Set(['a', 'e', 'i', 'o', 'u']);
const L = (s) => Array.from(s).length;

function caseOk(w, suf) {
  const rest = w.slice(0, w.length - suf.length);
  return w.endsWith(suf) && L(rest) >= 3 && (suf !== 'da' || !DA_ROOTS.has(w)) && (suf !== 'ka' || rest.endsWith('k')) && (suf !== 'qa' || rest.endsWith('q'));
}

export function stem(word) {
  let w = low(word);
  for (const suf of CASES) {
    if (caseOk(w, suf)) {
      w = w.slice(0, w.length - suf.length);
      break;
    }
  }
  for (const suf of POSSESSIVE) {
    const rest = w.slice(0, w.length - suf.length);
    const vowel = VOW.has(rest.slice(-1));
    if (w.endsWith(suf) && L(rest) >= 3 && (suf !== 'si' || vowel) && (suf !== 'i' || (!vowel && rest.slice(-1) !== "'" && !ADJ_I.some((e) => w.endsWith(e))))) {
      w = rest;
      break;
    }
  }
  if (w.endsWith('lar') && L(w) >= 5) w = w.slice(0, -3);
  return w;
}

export function caseStrip(word) {
  const w = low(word);
  for (const suf of CASES) {
    if (caseOk(w, suf)) return word.length === w.length ? word.slice(0, word.length - suf.length) : word;
  }
  return word;
}

export function suffixOf(word, base) {
  const w = low(word);
  const b = low(base);
  return w.startsWith(b) ? w.slice(b.length) : null;
}

export function inflect(base, suffix) {
  if (!suffix) return base;
  const last = low(base).slice(-1);
  let suf = suffix;
  if (['ga', 'ka', 'qa'].includes(suf)) suf = last === 'k' ? 'ka' : last === 'q' ? 'qa' : 'ga';
  else if (suf === 'i' || suf === 'si') suf = last !== '' && 'aeiou'.includes(last) ? 'si' : 'i';
  else if (suf.startsWith('i') && last !== '' && 'aeiou'.includes(last)) suf = `s${suf}`;
  return base + suf;
}

export function isContent(word) {
  const w = low(word);
  if (L(w) < 4 || STOP.has(w) || STOP.has(stem(w)) || /[0-9]/.test(w)) return false;
  return !VERBISH.some((e) => w.endsWith(e));
}

export function numberWord(tokens, i) {
  const w = low(tokens[i]);
  if (/^[0-9]+$/.test(w) && w.length <= 7) {
    let n = Number(w);
    let used = 1;
    while (i + used < tokens.length && tokens[i + used].length === 3 && /^[0-9]+$/.test(tokens[i + used]) && n < 1000) {
      n = n * 1000 + Number(tokens[i + used]);
      used += 1;
    }
    return [n, used];
  }
  if (own(TA, w)) return [TA[w], 1];
  if (own(TENS, w)) {
    if (i + 1 < tokens.length && own(TA, low(tokens[i + 1]))) return [TENS[w] + TA[low(tokens[i + 1])], 2];
    if (i + 1 < tokens.length && own(UNITS, low(tokens[i + 1]))) return [TENS[w] + UNITS[low(tokens[i + 1])], 2];
    return [TENS[w], 1];
  }
  if (own(UNITS, w)) return [UNITS[w], 1];
  return null;
}

export function counterOf(word) {
  const w = low(word);
  for (const c of COUNTER_LIST) {
    if (w.startsWith(c) && (w.length === c.length || AFTER_COUNTER.has(w.slice(c.length)))) return [c, w.slice(c.length)];
  }
  return null;
}
