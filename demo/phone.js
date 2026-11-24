// One demo phone: a realistic frame with the demo's Tashkent clock, a Telegram-like bot chat (a sent file shown as a
// document bubble) and the Mini App. The Mini App is laid out for 375 px; a narrower frame zooms it.
import { hhmm as fmt, localMinute } from '../shared/clock.js';
import { h, plain } from '../webapp/util.js';

const SIGNAL = '<svg viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>';
const WIFI = '<svg viewBox="0 0 16 12"><path d="M8 2.2c2.4 0 4.6.9 6.2 2.5l1.3-1.3A10.5 10.5 0 0 0 8 .3 10.5 10.5 0 0 0 .5 3.4l1.3 1.3A8.7 8.7 0 0 1 8 2.2zm0 3.7c1.4 0 2.7.5 3.6 1.4l1.3-1.3A6.9 6.9 0 0 0 8 4a6.9 6.9 0 0 0-4.9 2l1.3 1.3c1-.9 2.2-1.4 3.6-1.4zm0 3.6c-.5 0-1 .2-1.3.6L8 11.4l1.3-1.3c-.3-.4-.8-.6-1.3-.6z"/></svg>';
export const MARK = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="7" y="5" width="18" height="23" rx="3.5" fill="currentColor"/>'
  + '<path d="M11 12l2 2 4-4M11 20l2 2 4-4" fill="none" stroke="#1d3b6e" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  + '<path d="M19.5 13h2.5M19.5 21h2.5" stroke="#1d3b6e" stroke-width="2.2" stroke-linecap="round"/></svg>';
const DOC = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" fill="#fff" opacity=".95"/>'
  + '<path d="M14 2v5h5" fill="none" stroke="#2f5fa8" stroke-width="1.6"/><path d="M8 12h8M8 15.5h8M8 19h5" stroke="#2f5fa8" stroke-width="1.6" stroke-linecap="round"/></svg>';

export function createPhone({ who, bot, texts, now, onOpenApp, onShowApp }) {
  const clock = () => fmt(localMinute(now())).replace(/^0/, '');
  const time = h('span', { class: 'phone-clock' }, clock());
  const status = h('div', { class: 'phone-status', 'aria-hidden': 'true' }, time,
    h('span', { class: 'phone-icons', html: `${SIGNAL}${WIFI}<span class="phone-batt"><i></i></span>` }));
  const badge = h('span', { class: 'badge', hidden: true });
  const tabChat = h('button', { class: 'ptab on', type: 'button', 'data-testid': `${who}-tab-chat` }, '', badge);
  const tabApp = h('button', { class: 'ptab', type: 'button', 'data-testid': `${who}-tab-app` });
  const scroll = h('div', { class: 'tg-scroll', 'data-testid': `${who}-chat` });
  const input = h('input', { 'aria-label': 'message', autocomplete: 'off', maxlength: 300, 'data-testid': `${who}-input` });
  const chat = h('div', { class: 'pane chat on' },
    h('div', { class: 'tg-head' }, h('span', { class: 'tg-ava', html: MARK }), h('div', {}, h('b', {}, 'Test Ustasi'), h('small', { class: 'tg-status' }))),
    scroll,
    h('form', { class: 'tg-input', onsubmit: (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      if (text.startsWith('/start')) bot.start();
      else bot.type(text);
    } }, input, h('button', { type: 'submit', 'aria-label': 'send' }, '➤')));
  const appRoot = h('div', { class: 'pane app', 'data-testid': `${who}-app` });
  const push = h('div', { class: 'push', role: 'status', onclick: () => show('chat') });
  const screen = h('div', { class: 'phone-screen' }, push, h('div', { class: 'ptabs' }, tabChat, tabApp), chat, appRoot);
  const phone = h('div', { class: 'phone', 'data-testid': `${who}-phone` }, h('span', { class: 'phone-island', 'aria-hidden': 'true' }), status, screen,
    h('span', { class: 'phone-homebar', 'aria-hidden': 'true' }));
  const labelEl = h('div', { class: 'side-label' });
  const side = h('section', { class: 'side', 'data-who': who }, labelEl, phone);
  const seen = new Set();
  let unread = 0;
  let pane = 'chat';

  function show(which) {
    pane = which;
    chat.classList.toggle('on', pane === 'chat');
    appRoot.classList.toggle('on', pane === 'app');
    tabChat.classList.toggle('on', pane === 'chat');
    tabApp.classList.toggle('on', pane === 'app');
    if (pane === 'chat') {
      unread = 0;
      badge.hidden = true;
      scroll.scrollTop = scroll.scrollHeight;
    }
  }
  tabChat.addEventListener('click', () => show('chat'));
  tabApp.addEventListener('click', () => { show('app'); onShowApp?.(); });

  function renderLabels(name, role) {
    labelEl.replaceChildren(h('b', {}, name), h('span', {}, role));
    tabChat.firstChild.textContent = texts.P('demo.chat');
    tabApp.textContent = texts.P('demo.app');
    chat.querySelector('.tg-status').textContent = texts.P('demo.bot_status');
    input.placeholder = texts.P('demo.input');
  }

  function renderChat() {
    scroll.replaceChildren(...bot.messages.map((m) => {
      const kb = m.kb.length ? h('div', { class: 'kb' }, m.kb.map((row) => h('div', { class: 'kb-row' }, row.map((b) => h('button', {
        class: `kb-btn${'app' in b ? ' app' : ''}`, type: 'button', title: b.text, 'data-cb': b.data ?? '', 'data-app': 'app' in b ? b.app : null,
        onclick: () => { if ('app' in b) onOpenApp?.(b.app); else bot.press(m.id, b.data); } }, b.text))))) : null;
      const fresh = !seen.has(m.id);
      seen.add(m.id);
      const stamp = h('time', {}, fmt(localMinute(m.at)));
      const bubble = m.file ? h('div', { class: 'bubble file-b' }, h('span', { class: 'file-ico', html: DOC }),
        h('div', {}, h('b', {}, m.file.name), h('small', {}, texts.P('app.chars', { n: m.file.size }))), stamp)
        : h('div', { class: 'bubble', html: m.html }, stamp);
      return h('div', { class: `msg ${m.from === 'me' ? 'me' : 'bot'}${fresh ? ' new' : ''}`, 'data-mid': String(m.id) }, bubble, m.from === 'me' ? null : kb);
    }));
    scroll.scrollTop = scroll.scrollHeight;
  }

  /** A message arrived from the bot on its own: light the phone up. */
  function ping(html) {
    if (pane !== 'chat') {
      unread += 1;
      badge.textContent = String(unread);
      badge.hidden = false;
    }
    push.replaceChildren(h('span', { class: 'tg-ava', html: MARK }), h('div', {}, h('b', {}, 'Test Ustasi'), h('span', {}, plain(html))));
    push.classList.add('show');
    phone.classList.add('ring');
    clearTimeout(push.timer);
    push.timer = setTimeout(() => { push.classList.remove('show'); phone.classList.remove('ring'); }, 2600);
  }

  function alert(text) {
    const el = h('div', { class: 'tg-alert', role: 'alert' }, text);
    screen.append(el);
    setTimeout(() => el.remove(), 2200);
  }

  const fit = () => {
    const pad = Number.parseFloat(getComputedStyle(phone).paddingLeft) * 2;
    const w = phone.getBoundingClientRect().width - pad;
    appRoot.style.zoom = pad > 0 && w > 0 && w < 375 ? String(w / 375) : '';
  };
  new ResizeObserver(fit).observe(phone);
  const tick = () => { time.textContent = clock(); };
  return { side, appRoot, chat: scroll, input, show, ping, alert, renderChat, renderLabels, tick, get pane() { return pane; } };
}
