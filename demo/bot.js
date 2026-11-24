// The bot, simulated in the page: the same callback data, screens and messages as testustasi/bot (roles, a text or a file
// becomes a source and then a draft, test cards with results, the retest, classes, students' tests and codes) and every
// message the real bot sends on its own. Messages are {id, from: 'bot' | 'me', html, kb, at, file?: {name, size}}.
import * as I from '../shared/i18n.js';
import { Refused } from './backend.js';

const N = '(\\d{1,12})';
const PATTERNS = [['menu', 'm'], ['lang', 'lang'], ['help', 'h'], ['teacher', 'role:t'], ['student', 'role:s'], ['new', 'nt'], ['count', `n:${N}`],
  ['mix', `n:${N}:(5|10|15|20)`], ['make', `x:${N}:(5|10|15|20):(easy|mixed|hard)`], ['tests', 'tl'], ['test', `t:${N}`], ['retestAsk', `rq:${N}`], ['retest', `rx:${N}`],
  ['csv', `csv:${N}`], ['classes', 'cl'], ['class', `c:${N}`], ['newClass', 'cn'], ['mine', 'st'], ['code', 'code']].map(([n, rx]) => [n, new RegExp(`^${rx}$`)]);

export class BotSim {
  constructor(backend, uid, t, views, { onChange = () => {}, onAlert = () => {}, app = true, onFile = () => {} } = {}) {
    Object.assign(this, { b: backend, uid, t, v: views, onChange, onAlert, app, onFile });
    this.messages = [];
    this.ids = 1;
    this.pend = null;
  }

  get lang() { return this.b.lang(this.uid); }

  push(screen, from = 'bot', extra = {}) {
    const msg = { id: this.ids++, from, html: screen.html, kb: screen.kb ?? [], at: this.b.nowMs(), ...extra };
    this.messages.push(msg);
    this.onChange();
    return msg;
  }

  show(id, screen) {
    const msg = id && this.messages.find((m) => m.id === id);
    if (!msg) return this.push(screen);
    Object.assign(msg, { html: screen.html, kb: screen.kb ?? [] });
    this.onChange();
    return msg;
  }

  guard(fn) {
    try {
      return fn();
    } catch (e) {
      if (!(e instanceof Refused)) throw e;
      const key = this.t(this.lang, `err.${e.code}`) === `err.${e.code}` ? 'err.generic' : `err.${e.code}`;
      return { error: this.t(this.lang, key) };
    }
  }

  menuScreen() {
    const u = this.b.user(this.uid);
    if (u.role === 'teacher') return this.v.menuTeacher(this.lang, u.name, this.b.classesOf(this.uid).length, this.b.testsOf(this.uid).length);
    if (u.role === 'student') return this.v.menuStudent(this.lang, u.name, this.b.myTests(this.uid).filter((x) => x.status === 'new').length);
    return this.v.hello(this.lang);
  }

  start() {
    this.push({ html: '/start' }, 'me');
    return this.push(this.menuScreen());
  }

  /** A typed message: a class name or a test code when one is awaited, a teacher's long text becomes a source. */
  type(text) {
    this.push({ html: I.esc(text) }, 'me');
    const screen = this.guard(() => {
      const role = this.b.user(this.uid).role;
      if (this.pend === 'class') {
        this.pend = null;
        const k = this.b.createClass(this.uid, text.slice(0, 40));
        const s = this.v.classesList(this.lang, this.b.classesOf(this.uid));
        return { ...s, html: `${this.t(this.lang, 'bot.class_made', { name: k.name })}\n\n${s.html}` };
      }
      if (role === 'teacher') {
        if (Array.from(text.trim()).length < 150) return { ...this.menuScreen(), html: `${this.t(this.lang, 'bot.short_text')}\n\n${this.menuScreen().html}` };
        return this.v.gotSource(this.lang, this.b.addSource(this.uid, text));
      }
      return this.menuScreen();
    });
    return this.push(screen.error ? { html: screen.error } : screen);
  }

  /** A file sent to the bot (the demo's file holds a text). */
  sendFile(name, text) {
    this.push({ html: '' }, 'me', { file: { name, size: Array.from(text).length } });
    const screen = this.guard(() => {
      if (this.b.user(this.uid).role !== 'teacher') return { html: this.t(this.lang, 'bot.file_student'), kb: [] };
      return this.v.gotSource(this.lang, this.b.addSource(this.uid, text, name.replace(/\.(pdf|docx|txt)$/i, '').replaceAll('_', ' ')));
    });
    return this.push(screen.error ? { html: screen.error } : screen);
  }

  route(data) { // eslint-disable-line complexity
    const found = PATTERNS.map(([n, rx]) => [n, rx.exec(data)]).find(([, m]) => m);
    if (!found) return { error: this.t(this.lang, 'bot.stale') };
    const [kind, m] = found;
    const g = m.slice(1).map((x) => (/^\d+$/.test(x) ? Number(x) : x));
    const { b, v, uid, t } = this;
    const L = this.lang;
    switch (kind) {
      case 'menu': this.pend = null; return this.menuScreen();
      case 'lang': b.setLang(uid, L === 'uz' ? 'ru' : 'uz'); this.onLangChange?.(this.lang); return this.menuScreen();
      case 'help': return v.help(L, b.user(uid).role);
      case 'teacher': b.setRole(uid, 'teacher'); return this.menuScreen();
      case 'student': b.setRole(uid, 'student'); return v.joinedStudent(L);
      case 'code': this.pend = 'code'; return v.askCode(L);
      case 'mine': return v.myTests(L, b.myTests(uid));
      default: break;
    }
    b.needTeacher(uid);
    switch (kind) {
      case 'new': return v.newTest(L);
      case 'count': return v.gotSource(L, b.sourceInfo(uid, g[0]));
      case 'mix': return v.askMix(L, b.sourceInfo(uid, g[0]), g[1]);
      case 'make': return v.draftReady(L, b.makeDraft(uid, g[0], g[1], g[2]), this.app);
      case 'tests': return v.testsList(L, b.testsOf(uid));
      case 'test': {
        const d = b.draftView(uid, g[0]);
        const res = d.status === 'published' ? b.results(uid, g[0]) : null;
        return v.testCard(L, d, res, res ? b.analysis(uid, g[0]) : null, b.nowMs());
      }
      case 'retestAsk': return v.retestAsk(L, g[0], b.analysis(uid, g[0]).plan);
      case 'retest': {
        const [info, notes] = b.retest(uid, g[0]);
        b.notify(notes);
        return v.retestSent(L, g[0], info);
      }
      case 'csv': this.onFile(g[0]); return null;
      case 'classes': return v.classesList(L, b.classesOf(uid));
      case 'class': return v.classScreen(L, b.classDetail(uid, g[0]), `https://t.me/testustasi_bot?start=${b.invite(uid, g[0])}`, 14);
      default: this.pend = 'class'; return v.askClass(L);
    }
  }

  press(id, data) {
    const s = String(data).slice(0, 64);
    const keep = s.startsWith('+'); // a button under a message that stays in the chat: answer with a new message
    const screen = this.guard(() => this.route(keep ? s.slice(1) : s));
    if (screen?.error) this.onAlert(I.plain(screen.error));
    else if (screen) {
      if (keep) this.push(screen);
      else this.show(id, screen);
    }
  }

  /** A message the bot sends on its own (a note from the backend). */
  deliver(note) {
    return this.push(this.v.note(this.lang, note, this.b.nowMs()));
  }
}
