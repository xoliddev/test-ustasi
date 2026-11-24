// The demo's world: the same invented class as the server's seed (shared/seedgen.js), relative to the demo's "today",
// with the clock at 08:05 Tashkent time. The story's two people get positive ids like real Telegram users: Nodira
// ustoz teaches 7-B, Jasur studies there. The other 24 students are seeded (negative ids) and act in the story's
// simulated steps through the same rules.
import { atLocal, localDay } from '../shared/clock.js';
import { simulate, world } from '../shared/seedgen.js';
import './backend-more.js';
import { Backend } from './backend.js';

export const NODIRA = 1;
export const JASUR = 2;
export const START = 8 * 60 + 5;
const IDS = { [-1]: NODIRA, [-101]: JASUR };
const id = (x) => IDS[x] ?? x;

Backend.prototype.load = function load(w, texts) {
  const now = this.nowMs();
  this.touch(id(w.teacher.id), w.teacher.name, 'uz', 'teacher');
  this.classes.push({ id: w.group.id, teacher: id(w.teacher.id), name: w.group.name });
  for (const s of w.students) {
    this.touch(id(s.id), s.name, 'uz', 'student');
    this.members.push({ grp: w.group.id, user: id(s.id), joined_at: now });
  }
  this.abilities = Object.fromEntries(w.students.map((s) => [id(s.id), s.ability]));
  const byText = Object.fromEntries(texts.map((t) => [t.id, t]));
  for (const t of w.tests) {
    const src = { id: this.ids.src++, teacher: id(w.teacher.id), title: byText[t.text].title, body: byText[t.text].body };
    this.sources.push(src);
    this.tests.push({ id: t.id, teacher: id(w.teacher.id), source: src.id, grp: w.group.id, title: t.title, status: 'published', code: t.code, minutes: t.minutes, attempts: 1,
      shuffle: 1, reveal: 1, rank: 0, deadline: t.deadline, mix: 'mixed', asked: t.questions.length, origin: 'rule', parent: null, note: null, created_at: t.published_at,
      published_at: t.published_at });
    t.questions.forEach((q, i) => this.questions.push({ ...q, test: t.id, pos: i + 1, edited: 0 }));
    for (const s of w.students) this.targets.push({ test: t.id, user: id(s.id) });
    for (const a of t.attempts) {
      if (a.submitted_at >= now) continue;
      const att = { id: this.ids.att++, test: t.id, user: id(a.user), no: 1, seed: 0, started_at: a.started_at, deadline_at: a.started_at + t.minutes * 60_000,
        submitted_at: a.submitted_at, score: a.score, auto: Number(a.auto) };
      this.attempts.push(att);
      this.answers.set(att.id, Object.fromEntries(Object.entries(a.answers).map(([k, v]) => [Number(k), v])));
    }
    this.sent.add(`sum:${t.id}`);
  }
};

/** The other students solve test ``tid`` (the story's "the class finishes"): answers from the shared simulation, one
 * attempt each, started from ``from`` and spread over the next minutes; returns the notes (the summary at the end). */
Backend.prototype.simulateClass = function simulateClass(tid, traps, { skip = [], only = null, boost = 0, from = this.nowMs(), seed = 'demo' } = {}) {
  const qs = this.questionsOf(tid);
  const people = this.targets.filter((g) => g.test === tid && !skip.includes(g.user) && (!only || only.includes(g.user))
    && !this.attempts.some((a) => a.test === tid && a.user === g.user && a.submitted_at !== null)).map((g) => ({ id: g.user, ability: this.abilities[g.user] ?? 60 }));
  const notes = [];
  simulate(qs, people, `${seed}:${tid}`, traps, boost).forEach((sim, i) => {
    const begin = from + i * 23_000;
    const [view] = this.start(sim.user, tid, begin);
    const a = this.attempts.find((x) => x.id === view.attempt);
    this.answers.set(a.id, Object.fromEntries(qs.map((q) => [q.id, sim.answers[q.id]])));
    notes.push(...this.finalize(a, false, Math.min(a.deadline_at, begin + sim.seconds * 1000)));
  });
  return notes;
};

export function createDemo({ data, now = () => Date.now(), lang = 'uz' }) {
  const b = new Backend({ now });
  const today = localDay(b.nowMs());
  b.offset = atLocal(today, START) - b.clock();
  b.load(world(data.texts, today), data.texts);
  for (const uid of [NODIRA, JASUR]) b.setLang(uid, lang);
  b.at = (minute, day = 0) => {
    const target = atLocal(today + day, minute);
    if (target > b.nowMs()) b.offset += target - b.nowMs();
    b.changed();
  };
  return b;
}
