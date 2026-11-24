// Small DOM helpers shared by the Mini App and the demo. No framework, no build step. Text from people or
// from data only ever goes through textContent (never innerHTML).
const SVG_NS = 'http://www.w3.org/2000/svg';

/** The locales (the very same JSON files the bot reads) and, for the demo, the project's texts. */
export async function loadShared(base = new URL('../shared/', import.meta.url), withTexts = false) {
  const get = (p) => fetch(new URL(p, base)).then((r) => {
    if (!r.ok) throw new Error(`load ${p}`);
    return r.json();
  });
  const [uz, ru, texts] = await Promise.all([get('locales/uz.json'), get('locales/ru.json'), withTexts ? get('data/texts.json') : null]);
  return { catalogs: { uz, ru }, texts };
}

function attach(el, attrs, children) {
  for (const [k, v] of Object.entries(attrs ?? {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') el.setAttribute('class', v);
    else if (k === 'html') el.innerHTML = v; // only fixed icons and locale templates whose params are escaped, never user text
    else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

/** h('div', {class: 'x', onclick: fn}, child, 'text') — children may be nodes, strings or arrays. */
export const h = (tag, attrs = {}, ...children) => attach(document.createElement(tag), attrs, children);
/** The same for SVG elements. */
export const s = (tag, attrs = {}, ...children) => attach(document.createElementNS(SVG_NS, tag), attrs, children);

/** Plain text of a locale template (for aria-labels, buttons and push banners). */
export const plain = (html) => {
  const d = document.createElement('div');
  d.innerHTML = html;
  return d.textContent;
};

export const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
};

/** Like t() but without HTML escaping: the result only ever goes into textContent, so nothing is parsed. */
export function makeText(catalogs) {
  return (lang, key, params = {}) => {
    const l = lang === 'ru' ? 'ru' : 'uz';
    const template = catalogs[l]?.[key] || catalogs.uz?.[key] || key;
    return template.replace(/<[^>]+>/g, '').replace(/\{(\w+)\}/g, (m, k) => (k in params ? String(params[k]) : m));
  };
}

/** A short message at the bottom of `root`. */
export function toast(root, text, kind = '') {
  let box = root.querySelector(':scope > .g-toasts');
  if (!box) {
    box = h('div', { class: 'g-toasts', role: 'status', 'aria-live': 'polite' });
    root.append(box);
  }
  const el = h('div', { class: `g-toast ${kind}` }, text);
  box.append(el);
  setTimeout(() => el.classList.add('out'), 2600);
  setTimeout(() => el.remove(), 3100);
}

export function errText(T, lang, e) {
  const key = `err.${e?.code ?? 'generic'}`;
  const txt = T(lang, key);
  return txt === key ? T(lang, 'err.generic') : txt;
}

export const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

/** replaceChildren() that skips null, false and empty strings (replaceChildren would print "null"). */
export function fill(el, ...kids) {
  el.replaceChildren(...kids.flat(Infinity).filter((k) => k !== null && k !== undefined && k !== false && k !== ''));
  return el;
}

/** A row of choice buttons; ``options`` = [[value, label]]. */
export function chips(options, value, onPick, testid = '') {
  const box = h('div', { class: 'u-chips', role: 'radiogroup', 'data-testid': testid || null });
  const paint = (v) => box.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.v === String(v)));
  for (const [v, label] of options) {
    box.append(h('button', { type: 'button', class: 'u-chipbtn', 'data-v': String(v), role: 'radio', onclick: () => { onPick(v); paint(v); } }, label));
  }
  paint(value);
  return box;
}

/** A small confirmation sheet over ``root``; resolves to true or false. */
export function confirmBox(root, text, yes, no) {
  return new Promise((done) => {
    const close = (v) => { sheet.remove(); done(v); };
    const sheet = h('div', { class: 'u-sheet', role: 'dialog', 'data-testid': 'confirm' }, h('div', { class: 'u-sheet-box' }, h('p', {}, text),
      h('div', { class: 'u-row' }, h('button', { type: 'button', class: 'u-btn ghost', 'data-testid': 'confirm-no', onclick: () => close(false) }, no),
        h('button', { type: 'button', class: 'u-btn', 'data-testid': 'confirm-yes', onclick: () => close(true) }, yes))));
    root.append(sheet);
  });
}
