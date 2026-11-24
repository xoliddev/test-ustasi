// The server's rules in the page, for the browser demo: people and their one role, classes, sources, drafts and the
// teacher's review, settings and publishing — the same shapes and error codes as testustasi/*.py (solving, results,
// the analysis, the retest and the notes are in backend-more.js). In memory and synchronous; demo/api.js wraps it in
// promises with the same method names as the HTTP API, so the Mini App's code is identical on the server and here.
import { localDay } from '../shared/clock.js';
import { analyse, candidates, COUNTS, MIXES, select } from '../shared/generate.js';
import { code as seedCode } from '../shared/seedgen.js';
import { checkedText, clean, h32, normalizeSource, short } from '../shared/text.js';
import { edited } from '../shared/validate.js';

export class Refused extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}
const no = (code) => { throw new Refused(code); };
const isId = (v) => Number.isInteger(v) && v !== 0 && Math.abs(v) < 1e12;
const L = (s) => Array.from(s).length;
export const QCOLS = ['kind', 'uid', 'key', 'passage', 'sent', 'level', 'topic', 'stem', 'options', 'correct', 'explanation', 'quote'];

export class Backend {
  constructor({ now = () => Date.now() } = {}) {
    Object.assign(this, { clock: now, offset: 0, users: new Map(), classes: [], members: [], sources: [], tests: [], questions: [], targets: [], attempts: [],
      answers: new Map(), sent: new Set(), listeners: [], ids: { cls: 10, src: 10, test: 10, q: 1000, att: 1 }, codes: 0 });
  }

  nowMs() { return this.clock() + this.offset; }
  today() { return localDay(this.nowMs()); }
  on(fn) { this.listeners.push(fn); }
  emit(ev) { for (const fn of this.listeners) fn(ev); }
  changed() { this.emit({ type: 'changed' }); }
  notify(notes) { for (const note of notes ?? []) this.emit({ type: 'note', note }); }

  // ── people and roles ──
  touch(uid, name, lang = 'uz', role = null) {
    if (!this.users.has(uid)) this.users.set(uid, { id: uid, name, lang, role, pend: null });
    return this.users.get(uid);
  }
  user(uid) { return this.users.get(uid) ?? no('auth'); }
  lang(uid) { return this.users.get(uid)?.lang ?? 'uz'; }
  setLang(uid, lang) {
    if (!['uz', 'ru'].includes(lang)) no('generic');
    this.user(uid).lang = lang;
    return lang;
  }
  setRole(uid, role) {
    const u = this.user(uid);
    if (u.role && u.role !== role) no(`role_${u.role}`);
    u.role = role;
    return role;
  }
  needTeacher(uid) {
    const u = this.users.get(uid);
    if (!u || u.role !== 'teacher') no('forbidden');
    return u;
  }
  me(uid) {
    const u = this.user(uid);
    return { id: uid, name: u.name, lang: u.lang, role: u.role, now: this.nowMs(), today: this.today() };
  }

  // ── scoped lookups ──
  teacherTest(uid, tid) {
    if (!isId(tid)) no('generic');
    this.needTeacher(uid);
    return this.tests.find((t) => t.id === tid && t.teacher === uid) ?? no('not_found');
  }
  studentTest(uid, tid) {
    if (!isId(tid)) no('generic');
    const t = this.tests.find((x) => x.id === tid && x.status === 'published');
    return t && this.targets.some((g) => g.test === tid && g.user === uid) ? t : no('not_found');
  }
  questionsOf(tid) { return this.questions.filter((q) => q.test === tid).sort((a, b) => a.pos - b.pos || a.id - b.id); }
  peopleOf(tid) {
    return this.targets.filter((g) => g.test === tid).map((g) => ({ id: g.user, name: this.users.get(g.user).name }))
      .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : a.id - b.id));
  }
  attemptsOf(tid) {
    return this.attempts.filter((a) => a.test === tid).map((a) => {
      const answers = { ...(this.answers.get(a.id) ?? {}) };
      return { ...a, answers, answered: Object.keys(answers).length };
    });
  }
  once(key) {
    if (this.sent.has(key)) return false;
    this.sent.add(key);
    return true;
  }

  // ── classes ──
  createClass(uid, name) {
    let title;
    try {
      title = checkedText(name, 1, 24, 'class_name');
    } catch (e) {
      no(e.code);
    }
    this.setRole(uid, 'teacher');
    if (this.classes.some((k) => k.teacher === uid && k.name === title)) no('class_exists');
    const k = { id: this.ids.cls++, teacher: uid, name: title };
    this.classes.push(k);
    this.changed();
    return { id: k.id, name: title, students: 0 };
  }
  classesOf(uid) {
    this.needTeacher(uid);
    return this.classes.filter((k) => k.teacher === uid).map((k) => ({ id: k.id, name: k.name, students: this.members.filter((m) => m.grp === k.id).length,
      tests: this.tests.filter((t) => t.grp === k.id && t.status === 'published').length })).sort((a, b) => (a.name < b.name ? -1 : 1));
  }
  ownClass(uid, gid) {
    if (!isId(gid)) no('generic');
    this.needTeacher(uid);
    return this.classes.find((k) => k.id === gid && k.teacher === uid) ?? no('not_found');
  }
  classDetail(uid, gid) {
    const k = this.ownClass(uid, gid);
    const students = this.members.filter((m) => m.grp === k.id).map((m) => ({ id: m.user, name: this.users.get(m.user).name, joined_at: m.joined_at }))
      .sort((a, b) => (a.name < b.name ? -1 : 1));
    return { id: k.id, name: k.name, students };
  }
  invite(uid, gid) {
    const k = this.ownClass(uid, gid);
    const exp = Math.floor(this.nowMs() / 3_600_000) + 14 * 24;
    return `g${k.id}_${exp}_${h32(`demo:${k.id}:${exp}`).toString(16).padStart(8, '0').repeat(2)}`;
  }

  // ── sources and drafts ──
  addSource(uid, body, title = '') {
    this.needTeacher(uid);
    if (typeof body !== 'string') no('generic');
    const text = normalizeSource(body);
    if (L(text) > 30_000) no('too_long');
    const a = analyse(text, typeof title === 'string' ? clean(title, 80) : '');
    if (L(text) < 150 || !a.passages.length) no('too_short');
    const name = (typeof title === 'string' && clean(title, 80)) || a.title || short(a.passages[0].sentences[0], 60);
    const s = { id: this.ids.src++, teacher: uid, title: name, body: a.body };
    this.sources.push(s);
    return this.sourceInfo(uid, s.id);
  }
  ownSource(uid, sid) {
    if (!isId(sid)) no('generic');
    return this.sources.find((s) => s.id === sid && s.teacher === uid) ?? no('not_found');
  }
  sourceInfo(uid, sid) {
    this.needTeacher(uid);
    const s = this.ownSource(uid, sid);
    const a = analyse(s.body, s.title);
    return { id: s.id, title: s.title, passages: a.passages.length, chars: L(s.body), possible: select(candidates(a), 20, 'mixed').length };
  }
  insert(tid, qs, start = 1) {
    qs.forEach((q, i) => this.questions.push({ id: this.ids.q++, test: tid, pos: start + i, ...Object.fromEntries(QCOLS.map((k) => [k, structuredClone(q[k])])), edited: 0 }));
  }
  makeDraft(uid, sid, n, mix) {
    if (!COUNTS.includes(n) || !MIXES.includes(mix)) no('generic');
    this.needTeacher(uid);
    const s = this.ownSource(uid, sid);
    const qs = select(candidates(analyse(s.body, s.title)), n, mix);
    if (!qs.length) no('no_questions');
    const t = { id: this.ids.test++, teacher: uid, source: s.id, grp: null, title: s.title.slice(0, 80), status: 'draft', code: null, minutes: 15, attempts: 1,
      shuffle: 1, reveal: 1, rank: 0, deadline: null, mix, asked: n, origin: 'rule', parent: null, note: null, created_at: this.nowMs(), published_at: null };
    this.tests.push(t);
    this.insert(t.id, qs);
    this.changed();
    return this.draftView(uid, t.id);
  }
  draftView(uid, tid) {
    const t = this.teacherTest(uid, tid);
    const src = this.ownSource(uid, t.source);
    const pick = ['id', 'title', 'status', 'code', 'minutes', 'attempts', 'deadline', 'mix', 'asked', 'origin', 'note', 'parent', 'grp', 'published_at'];
    return { ...Object.fromEntries(pick.map((k) => [k, t[k]])), shuffle: Boolean(t.shuffle), reveal: Boolean(t.reveal), rank: Boolean(t.rank), source: src.title,
      questions: this.questionsOf(t.id).map((q) => ({ id: q.id, pos: q.pos, kind: q.kind, level: q.level, topic: q.topic, stem: q.stem, options: [...q.options],
        correct: q.correct, explanation: q.explanation, quote: q.quote, passage: q.passage, edited: q.edited })), classes: this.classesOf(uid), now: this.nowMs() };
  }
  draftQuestion(uid, tid, qid) {
    const t = this.teacherTest(uid, tid);
    if (t.status !== 'draft') no('published');
    return [t, this.questions.find((q) => q.id === qid && q.test === t.id) ?? no('not_found')];
  }
  editQuestion(uid, tid, qid, data) {
    const [t, q] = this.draftQuestion(uid, tid, qid);
    let nq;
    try {
      nq = edited(data, q);
    } catch (e) {
      no(e.code ?? 'generic');
    }
    Object.assign(q, { stem: nq.stem, options: nq.options, correct: nq.correct, explanation: nq.explanation, topic: nq.topic, edited: 1 });
    this.changed();
    return this.draftView(uid, t.id);
  }
  deleteQuestion(uid, tid, qid) {
    const [t, q] = this.draftQuestion(uid, tid, qid);
    if (this.questionsOf(t.id).length <= 1) no('last_question');
    this.questions = this.questions.filter((x) => x.id !== q.id);
    for (const x of this.questions) if (x.test === t.id && x.pos > q.pos) x.pos -= 1;
    this.changed();
    return this.draftView(uid, t.id);
  }
  regenQuestion(uid, tid, qid) {
    const [t, q] = this.draftQuestion(uid, tid, qid);
    const src = this.ownSource(uid, t.source);
    const used = [...this.questionsOf(t.id).filter((x) => x.id !== q.id), q];
    const cands = candidates(analyse(src.body, src.title));
    const pick = select(cands.filter((x) => x.passage === q.passage), 1, t.mix, used);
    const got = pick.length ? pick : select(cands, 1, t.mix, used);
    if (!got.length) no('no_more');
    Object.assign(q, Object.fromEntries(QCOLS.map((k) => [k, structuredClone(got[0][k])])), { edited: 0 });
    this.changed();
    return this.draftView(uid, t.id);
  }
  moveQuestion(uid, tid, qid, step) {
    if (step !== -1 && step !== 1) no('generic');
    const [t, q] = this.draftQuestion(uid, tid, qid);
    const other = this.questions.find((x) => x.test === t.id && x.pos === q.pos + step);
    if (other) [other.pos, q.pos] = [q.pos, q.pos + step];
    this.changed();
    return this.draftView(uid, t.id);
  }
  newCode() {
    this.codes += 1;
    return seedCode(1000 + this.codes);
  }
}
