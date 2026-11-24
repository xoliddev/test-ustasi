// The rest of the server's rules in the page (see backend.js): settings and publishing, solving with the deadline kept
// here and the seeded order, results, the analysis, the CSV, the retest and the notes; plus loading the seeded class.
import * as A from '../shared/analysis.js';
import { atLocal } from '../shared/clock.js';
import { analyse, candidates, select } from '../shared/generate.js';
import { attemptSeed, layout } from '../shared/shuffle.js';
import { csvText } from '../shared/table.js';
import { checkedText } from '../shared/text.js';
import { Backend, QCOLS, Refused } from './backend.js';

const GRACE = 5000;
const DAY = 86_400_000;
const no = (code) => { throw new Refused(code); };
const plan = (t, a, qs) => layout(qs.map((q) => q.id), a.seed, Boolean(t.shuffle));
const P = Backend.prototype;

P.setSettings = function setSettings(uid, tid, data) {
  if (!data || typeof data !== 'object' || !Object.keys(data).length || Object.keys(data).length > 8) no('generic');
  const t = this.teacherTest(uid, tid);
  const ch = {};
  for (const [k, v] of Object.entries(data)) {
    if (['shuffle', 'reveal', 'rank'].includes(k)) {
      if (typeof v !== 'boolean') no('generic');
      ch[k] = Number(v);
      continue;
    }
    if (t.status !== 'draft') no('published');
    const int = Number.isInteger(v);
    if (k === 'minutes') ch[k] = int && v >= 1 && v <= 180 ? v : no('minutes');
    else if (k === 'attempts') ch[k] = int && v >= 1 && v <= 5 ? v : no('attempts');
    else if (k === 'deadline') ch[k] = v === null || (int && v >= this.nowMs() + 5 * 60_000 && v <= this.nowMs() + 60 * DAY) ? v : no('deadline');
    else if (k === 'grp') {
      if (v !== null) this.ownClass(uid, v);
      ch[k] = v;
    } else if (k === 'title') {
      try { ch[k] = checkedText(v, 2, 80, 'title'); } catch { no('title'); }
    } else no('generic');
  }
  Object.assign(t, ch);
  this.changed();
  return this.draftView(uid, t.id);
};

P.publish = function publish(uid, tid) {
  const t = this.teacherTest(uid, tid);
  if (t.status !== 'draft') no('published');
  if (t.grp === null) no('no_class');
  const k = this.ownClass(uid, t.grp);
  if (t.deadline !== null && t.deadline <= this.nowMs()) no('deadline');
  const n = this.questionsOf(t.id).length;
  Object.assign(t, { status: 'published', code: this.newCode(), published_at: this.nowMs() });
  for (const m of this.members.filter((x) => x.grp === k.id)) if (!this.targets.some((g) => g.test === t.id && g.user === m.user)) this.targets.push({ test: t.id, user: m.user });
  const people = this.targets.filter((g) => g.test === t.id).map((g) => g.user).sort((a, b) => a - b);
  this.changed();
  return [this.draftView(uid, t.id), people.map((u) => ({ to: u, kind: 'new_test', test: t.id, title: t.title, count: n, minutes: t.minutes, deadline: t.deadline, class: k.name }))];
};

P.testsOf = function testsOf(uid) {
  this.needTeacher(uid);
  return this.tests.filter((t) => t.teacher === uid).sort((a, b) => (b.published_at ?? b.created_at) - (a.published_at ?? a.created_at) || b.id - a.id).map((t) => ({
    id: t.id, title: t.title, status: t.status, code: t.code, minutes: t.minutes, deadline: t.deadline, parent: t.parent, created_at: t.created_at,
    published_at: t.published_at, class: this.classes.find((k) => k.id === t.grp)?.name ?? null, questions: this.questionsOf(t.id).length,
    people: this.targets.filter((g) => g.test === t.id).length, done: new Set(this.attempts.filter((a) => a.test === t.id && a.submitted_at !== null).map((a) => a.user)).size }));
};

P.myTests = function myTests(uid) {
  const now = this.nowMs();
  return this.tests.filter((t) => t.status === 'published' && this.targets.some((g) => g.test === t.id && g.user === uid))
    .sort((a, b) => b.published_at - a.published_at || b.id - a.id).map((t) => {
      const mine = this.attempts.filter((a) => a.test === t.id && a.user === uid);
      const last = mine.filter((a) => a.submitted_at !== null).sort((a, b) => b.id - a.id)[0];
      const count = this.questionsOf(t.id).length;
      const status = mine.some((a) => a.submitted_at === null) ? 'working' : last ? 'done' : t.deadline !== null && t.deadline <= now ? 'closed' : 'new';
      const item = { id: t.id, title: t.title, minutes: t.minutes, deadline: t.deadline, attempts: t.attempts, parent: t.parent, published_at: t.published_at,
        class: this.classes.find((k) => k.id === t.grp)?.name ?? null, count, status, retest: t.parent !== null };
      if (last) Object.assign(item, { score: last.score, pct: A.pct(last.score, count) });
      return item;
    });
};

P.testCard = function testCard(uid, tid) {
  const t = this.studentTest(uid, tid);
  const att = this.attempts.filter((a) => a.test === t.id && a.user === uid).sort((a, b) => a.no - b.no);
  const used = att.filter((a) => a.submitted_at !== null).length;
  return { id: t.id, title: t.title, count: this.questionsOf(t.id).length, minutes: t.minutes, deadline: t.deadline, attempts: t.attempts, used,
    left: Math.max(0, t.attempts - used), open: att.find((a) => a.submitted_at === null)?.id ?? null, closed: t.deadline !== null && t.deadline <= this.nowMs(),
    done: used > 0, now: this.nowMs(), retest: t.parent !== null };
};

P.ownAttempt = function ownAttempt(uid, aid) {
  if (!Number.isInteger(aid)) no('generic');
  const a = this.attempts.find((x) => x.id === aid && x.user === uid) ?? no('not_found');
  return [a, this.studentTest(uid, a.test)];
};

P.start = function start(uid, tid, at = null) {
  const t = this.studentTest(uid, tid);
  let notes = [];
  let a = this.attempts.find((x) => x.test === t.id && x.user === uid && x.submitted_at === null);
  if (a && this.nowMs() > a.deadline_at + GRACE) {
    notes = this.finalize(a, true);
    a = null;
  }
  if (!a) {
    if (t.deadline !== null && t.deadline <= this.nowMs()) no('closed');
    const mine = this.attempts.filter((x) => x.test === t.id && x.user === uid);
    if (mine.length >= t.attempts) no('no_attempts');
    const no_ = Math.max(0, ...mine.map((x) => x.no)) + 1;
    const begin = at ?? this.nowMs();
    const limit = begin + t.minutes * 60_000;
    a = { id: this.ids.att++, test: t.id, user: uid, no: no_, seed: attemptSeed(t.id, uid, no_), started_at: begin, deadline_at: t.deadline !== null ? Math.min(limit, t.deadline) : limit,
      submitted_at: null, score: null, auto: 0 };
    this.attempts.push(a);
    this.changed();
  }
  return [this.attemptView(uid, a.id), notes];
};

P.attemptView = function attemptView(uid, aid) {
  const [a, t] = this.ownAttempt(uid, aid);
  const qs = this.questionsOf(t.id);
  const by = Object.fromEntries(qs.map((q) => [q.id, q]));
  const ans = this.answers.get(a.id) ?? {};
  const chosen = {};
  const items = plan(t, a, qs).map((it, pos) => {
    if (it.qid in ans) chosen[String(pos)] = it.opts.indexOf(ans[it.qid]);
    return { pos, stem: by[it.qid].stem, options: it.opts.map((k) => by[it.qid].options[k]) };
  });
  return { attempt: a.id, test: t.id, title: t.title, no: a.no, deadline_at: a.deadline_at, now: this.nowMs(), submitted: a.submitted_at !== null, questions: items, answers: chosen };
};

P.answer = function answer(uid, aid, pos, choice) {
  if (!Number.isInteger(pos) || !Number.isInteger(choice) || choice < 0 || choice > 3 || pos < 0) no('generic');
  const [a, t] = this.ownAttempt(uid, aid);
  if (a.submitted_at !== null) no('submitted');
  if (this.nowMs() > a.deadline_at + GRACE) return [{ time_up: true, test: t.id }, this.finalize(a, true)];
  const p = plan(t, a, this.questionsOf(t.id));
  if (pos >= p.length) no('generic');
  const ans = this.answers.get(a.id) ?? {};
  ans[p[pos].qid] = p[pos].opts[choice];
  this.answers.set(a.id, ans);
  this.changed();
  return [{ pos, choice, answered: Object.keys(ans).length, total: p.length, time_up: false }, []];
};

P.finalize = function finalize(a, auto, at = null) {
  if (a.submitted_at !== null) return [];
  const qs = this.questionsOf(a.test);
  a.submitted_at = at ?? (auto ? Math.min(this.nowMs(), a.deadline_at) : this.nowMs());
  a.score = A.score(qs, this.answers.get(a.id) ?? {});
  a.auto = Number(auto);
  this.changed();
  return this.summaryIfComplete(a.test);
};

P.submit = function submit(uid, aid) {
  const [a, t] = this.ownAttempt(uid, aid);
  const notes = this.finalize(a, this.nowMs() > a.deadline_at + GRACE);
  return [this.result(uid, t.id), notes];
};

P.result = function result(uid, tid) {
  const t = this.studentTest(uid, tid);
  const qs = this.questionsOf(t.id);
  const mine = this.attemptsOf(t.id).filter((a) => a.user === uid);
  const done = mine.filter((a) => a.submitted_at !== null);
  if (!done.length) no('not_submitted');
  const a = done[done.length - 1];
  const left = Math.max(0, t.attempts - mine.length);
  const closed = t.deadline !== null && t.deadline <= this.nowMs();
  const pc = A.pct(a.score, qs.length);
  const out = { test: t.id, title: t.title, score: a.score, total: qs.length, pct: pc, grade: A.grade(pc), auto: Boolean(a.auto),
    seconds: Math.max(0, Math.floor((a.submitted_at - a.started_at) / 1000)), left, closed, reveal: false, rank: null, mistakes: null, retest: t.parent !== null };
  if (t.rank) {
    const fin = [...A.finals(this.attemptsOf(t.id)).values()];
    out.rank = { place: 1 + fin.filter((f) => f.score > a.score).length, of: fin.length };
  }
  if (t.reveal && (left === 0 || closed)) {
    const by = Object.fromEntries(qs.map((q) => [q.id, q]));
    out.reveal = true;
    out.mistakes = plan(t, a, qs).map((p, i) => [p, i]).filter(([p]) => a.answers[p.qid] !== by[p.qid].correct).map(([p, i]) => ({ n: i + 1, stem: by[p.qid].stem,
      chosen: p.qid in a.answers ? by[p.qid].options[a.answers[p.qid]] : null, correct: by[p.qid].options[by[p.qid].correct], explanation: by[p.qid].explanation, quote: by[p.qid].quote }));
  }
  return out;
};

P.published = function published(uid, tid) {
  const t = this.teacherTest(uid, tid);
  if (t.status !== 'published') no('not_published');
  return [t, this.questionsOf(t.id), this.peopleOf(t.id), this.attemptsOf(t.id)];
};

P.results = function results(uid, tid) {
  const [t, qs, people, atts] = this.published(uid, tid);
  return { id: t.id, title: t.title, code: t.code, deadline: t.deadline, minutes: t.minutes, parent: t.parent, total: qs.length, now: this.nowMs(), ...A.table(people, atts, qs.length) };
};

P.progressOf = function progressOf(parent, child) {
  const qs = this.questionsOf(parent.id);
  const atts = this.attemptsOf(parent.id);
  const pl = A.retestPlan(qs, atts);
  return { ...A.progress(qs, atts, pl.topics, this.questionsOf(child), this.attemptsOf(child)), topics: pl.topics };
};

P.analysis = function analysis(uid, tid) {
  const [t, qs, people, atts] = this.published(uid, tid);
  const rep = A.questionsReport(qs, atts);
  const names = Object.fromEntries(people.map((p) => [p.id, p.name]));
  const tops = A.topicsReport(qs, atts).map((tp) => ({ ...tp, people: Object.entries(tp.people).map(([u, v]) => ({ user: Number(u), name: names[u] ?? '?', pct: v }))
    .sort((x, y) => x.pct - y.pct || (x.name < y.name ? -1 : 1)) }));
  rep.questions.forEach((r, i) => Object.assign(r, { stem: qs[i].stem, options: qs[i].options, correct: qs[i].correct, kind: qs[i].kind, quote: qs[i].quote }));
  const pl = A.retestPlan(qs, atts);
  const child = this.tests.find((x) => x.parent === t.id && x.teacher === uid);
  const out = { id: t.id, title: t.title, parent: t.parent, code: t.code, deadline: t.deadline, n: rep.n, k: rep.k, questions: rep.questions, topics: tops,
    plan: { ...pl, count: pl.students.length, names: pl.students.map((u) => names[u] ?? '?') }, retest: child?.id ?? null, progress: null };
  if (child) out.progress = this.progressOf(t, child.id);
  if (t.parent) out.progress = this.progressOf(this.tests.find((x) => x.id === t.parent), t.id);
  return out;
};

P.csv = function csv(uid, tid, labels, stamp) {
  const [t, qs, people, atts] = this.published(uid, tid);
  const tab = A.table(people, atts, qs.length);
  const marks = Object.fromEntries([...A.finals(atts)].map(([u, a]) => [u, qs.map((q) => (q.id in a.answers ? Number(a.answers[q.id] === q.correct) : null))]));
  return { name: `${t.title}.csv`, csv: csvText(labels, tab.rows, marks, qs.length, stamp) };
};

P.retest = function retest(uid, tid) {
  const [t, qs, , atts] = this.published(uid, tid);
  if (t.parent !== null) no('no_retest');
  const old = this.tests.find((x) => x.parent === t.id);
  if (old) return [{ id: old.id, again: true }, []];
  const pl = A.retestPlan(qs, atts);
  if (!pl.topics.length || !pl.students.length) no('no_retest');
  const keep = qs.filter((q) => pl.questions.includes(q.id));
  const src = this.ownSource(uid, t.source);
  const passages = new Set(qs.filter((q) => pl.topics.includes(q.topic)).map((q) => q.passage));
  const cands = candidates(analyse(src.body, src.title)).filter((x) => passages.has(x.passage));
  const fresh = select(cands, Math.max(2, Math.min(5, 8 - keep.length)), 'mixed', qs, true);
  const all = [...keep, ...fresh].sort((a, b) => a.passage - b.passage || a.sent - b.sent || (a.uid < b.uid ? -1 : a.uid > b.uid ? 1 : 0)).slice(0, 8);
  const minutes = Math.max(5, Math.ceil((t.minutes * all.length) / Math.max(1, qs.length)));
  const deadline = atLocal(this.today() + 1, 23 * 60 + 59);
  const r = { id: this.ids.test++, teacher: uid, source: t.source, grp: t.grp, title: `${t.title} — qayta test`.slice(0, 80), status: 'published', code: null, minutes, attempts: 1,
    shuffle: 1, reveal: 1, rank: 0, deadline, mix: 'mixed', asked: all.length, origin: 'rule', parent: t.id, note: null, created_at: this.nowMs(), published_at: this.nowMs() };
  this.tests.push(r);
  this.insert(r.id, all.map((q) => Object.fromEntries(QCOLS.map((k) => [k, q[k]]))));
  for (const u of pl.students) this.targets.push({ test: r.id, user: u });
  this.changed();
  return [{ id: r.id, again: false, count: all.length, students: pl.students.length, topics: pl.topics, kept: keep.length, fresh: fresh.length, skipped: pl.skipped },
    pl.students.map((u) => ({ to: u, kind: 'retest', test: r.id, title: t.title, topics: pl.topics, count: all.length, minutes, deadline }))];
};

P.summaryIfComplete = function summaryIfComplete(tid, reason = 'all') {
  const t = this.tests.find((x) => x.id === tid);
  const people = this.peopleOf(tid);
  const atts = this.attemptsOf(tid);
  const done = A.finals(atts).size;
  if (reason === 'all' && (!people.length || done < people.length)) return [];
  if (!this.once(`sum:${tid}`)) return [];
  const qs = this.questionsOf(tid);
  const st = A.table(people, atts, qs.length).stats;
  const rep = A.questionsReport(qs, atts);
  const flags = { key: rep.questions.filter((r) => r.flag === 'key').length, hard: rep.questions.filter((r) => r.flag === 'hard').length };
  const note = { to: t.teacher, kind: 'summary', test: tid, title: t.title, reason, done, people: people.length, avg: st.avg, median: st.median, flags, retest: t.parent !== null, progress: null };
  if (t.parent) {
    const parent = this.tests.find((x) => x.id === t.parent);
    const pq = this.questionsOf(parent.id);
    const pa = this.attemptsOf(parent.id);
    note.progress = A.progress(pq, pa, A.retestPlan(pq, pa).topics, qs, atts);
  }
  return [note];
};

P.dueNotes = function dueNotes() {
  const notes = [];
  for (const a of this.attempts.filter((x) => x.submitted_at === null && x.deadline_at + GRACE < this.nowMs())) notes.push(...this.finalize(a, true));
  for (const t of this.tests.filter((x) => x.status === 'published' && x.deadline !== null && x.deadline <= this.nowMs())) notes.push(...this.summaryIfComplete(t.id, 'deadline'));
  return notes;
};
