// Mini App entry. Inside Telegram it passes the signed initData along (the server checks it on every call) and opens
// the screen the bot's button asked for (?t=, ?r=, ?a= for a teacher's test, ?s= for a student's). Outside Telegram it
// only asks to open it there.
import { normLang } from '../shared/i18n.js';
import { httpApi } from './api.js';
import { mountApp, routeFrom } from './ui.js';
import { h, loadShared } from './util.js';

const tg = window.Telegram?.WebApp;
const root = document.getElementById('app');
const shared = await loadShared();

if (!tg?.initData) {
  root.replaceChildren(h('p', { class: 'u-outside' }, shared.catalogs.uz['app.open_in_telegram']),
    h('p', { class: 'u-outside' }, shared.catalogs.ru['app.open_in_telegram']));
} else {
  tg.ready();
  tg.expand();
  const lang = normLang(tg.initDataUnsafe?.user?.language_code);
  const app = mountApp(root, { ...shared, api: httpApi(tg.initData), lang, poll: 5000, route: routeFrom(window.location.search),
    onLang: (l) => { document.documentElement.lang = l; }, telegram: tg });
  await app.ready;
}
document.body.dataset.ready = '1';
