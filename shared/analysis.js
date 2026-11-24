// JS port of testustasi/core/analysis.py: scores, the results table's numbers and the analysis of wrong answers, in
// integer math only. ``answers`` objects map a question id to the chosen original option index.
import { sortBy } from './text.js';

export const LETTERS = 'ABCD';
export const MIN_FLAGS = 5;
const fl = Math.floor;

export const rdiv = (a, b) => (a < 0 ? -fl((-2 * a + b) / (2 * b)) : fl((2 * a + b) / (2 * b)));
export const pct = (part, whole) => (whole > 0 ? rdiv(100 * part, whole) : 0);
export const grade = (p) => (p >= 86 ? 5 : p >= 71 ? 4 : p >= 56 ? 3 : 2);
const ans = (a, id) => (a.answers[id] === undefined ? null : a.answers[id]);

export function median(values) {
  const v = [...values].sort((x, y) => x - y);
  if (!v.length) return 0;
  const mid = fl(v.length / 2);
  return v.length % 2 ? v[mid] : rdiv(v[mid - 1] + v[mid], 2);
}

export const score = (questions, answers) => questions.filter((q) => answers[q.id] === q.correct).length;

export function finals(attempts) {
  const out = new Map();
  for (const a of sortBy(attempts.filter((x) => x.submitted_at !== null && x.submitted_at !== undefined), (x) => [x.submitted_at, x.id])) out.set(a.user, a);
  return out;
}

export function table(people, attempts, total) {
  const last = finals(attempts);
  const open = new Map(attempts.filter((a) => a.submitted_at === null || a.submitted_at === undefined).map((a) => [a.user, a]));
  const rows = people.map((p) => {
    const a = last.get(p.id);
    if (a) {
      const pc = pct(a.score, total);
      return { user: p.id, name: p.name, status: 'done', score: a.score, total, pct: pc, grade: grade(pc),
        seconds: Math.max(0, fl((a.submitted_at - a.started_at) / 1000)), at: a.submitted_at, auto: Boolean(a.auto) };
    }
    if (open.has(p.id)) {
      const o = open.get(p.id);
      return { user: p.id, name: p.name, status: 'working', score: null, total, pct: null, grade: null, seconds: null, at: o.started_at, answered: o.answered ?? 0 };
    }
    return { user: p.id, name: p.name, status: 'waiting', score: null, total, pct: null, grade: null, seconds: null, at: null };
  });
  const done = rows.filter((r) => r.status === 'done');
  const pcs = done.map((r) => r.pct);
  const grades = { 5: 0, 4: 0, 3: 0, 2: 0 };
  for (const r of done) grades[r.grade] += 1;
  const stats = { people: rows.length, done: done.length, working: rows.filter((r) => r.status === 'working').length,
    waiting: rows.filter((r) => r.status === 'waiting').length, avg: pcs.length ? rdiv(pcs.reduce((x, y) => x + y, 0), pcs.length) : 0,
    median: median(pcs), avg_score_x10: done.length ? rdiv(10 * done.reduce((x, r) => x + r.score, 0), done.length) : 0, grades };
  const rank = { done: 0, working: 1, waiting: 2 };
  sortBy(rows, (r) => [rank[r.status], -(r.pct ?? 0), r.seconds ?? 0, r.name, r.user]);
  return { rows, stats };
}

const ranked = (last) => sortBy([...last.values()], (a) => [-a.score, a.submitted_at - a.started_at, a.user]);

export function questionsReport(questions, attempts) {
  const order = ranked(finals(attempts));
  const n = order.length;
  const k = n >= MIN_FLAGS ? Math.max(1, rdiv(27 * n, 100)) : 0;
  const top = order.slice(0, k);
  const bottom = k ? order.slice(n - k) : [];
  const out = questions.map((q, pos) => {
    const picks = [0, 0, 0, 0];
    let blank = 0;
    for (const a of order) {
      const c = ans(a, q.id);
      if (c === null) blank += 1;
      else picks[c] += 1;
    }
    const right = picks[q.correct];
    const p = pct(right, n);
    const tp = k ? pct(top.filter((a) => ans(a, q.id) === q.correct).length, k) : null;
    const bp = k ? pct(bottom.filter((a) => ans(a, q.id) === q.correct).length, k) : null;
    const disc = k ? tp - bp : null;
    let lead = -1;
    for (let i = 0; i < 4; i++) if (i !== q.correct && (lead < 0 || picks[i] > picks[lead])) lead = i;
    let flag = null;
    let pick = null;
    if (n >= MIN_FLAGS) {
      if (tp < 50 && disc <= 10) flag = 'key';
      else if (p < 50) flag = 'hard';
      else if (p >= 90) flag = 'easy';
      if ((flag === 'key' || flag === 'hard') && pct(picks[lead], n) >= 30) pick = { option: lead, letter: LETTERS[lead], pct: pct(picks[lead], n) };
    }
    return { id: q.id, pos: pos + 1, topic: q.topic, right, n, pct: p, top: tp, bottom: bp, disc, picks: picks.map((x) => pct(x, n)), counts: picks, blank, flag, pick };
  });
  return { n, k, questions: out };
}

export function topicsReport(questions, attempts) {
  const last = finals(attempts);
  const order = [];
  for (const q of questions) if (!order.includes(q.topic)) order.push(q.topic);
  const users = [...last.keys()].sort((x, y) => x - y);
  return order.map((topic) => {
    const qs = questions.filter((q) => q.topic === topic);
    let right = 0;
    for (const a of last.values()) right += qs.filter((q) => ans(a, q.id) === q.correct).length;
    const people = {};
    for (const u of users) people[u] = pct(qs.filter((q) => ans(last.get(u), q.id) === q.correct).length, qs.length);
    return { topic, questions: qs.map((q) => questions.indexOf(q) + 1), pct: pct(right, qs.length * last.size), people };
  });
}

export function retestPlan(questions, attempts, limit = 2) {
  const rep = questionsReport(questions, attempts);
  const byId = new Map(rep.questions.map((r) => [r.id, r]));
  const weak = sortBy(topicsReport(questions, attempts).filter((t) => t.pct < 60), (t) => [t.pct, t.questions[0]]).slice(0, limit);
  const names = weak.map((t) => t.topic);
  const keep = questions.filter((q) => names.includes(q.topic) && byId.get(q.id).pct < 70 && byId.get(q.id).flag !== 'key');
  const skipped = questions.filter((q) => names.includes(q.topic) && byId.get(q.id).flag === 'key').map((q) => byId.get(q.id).pos);
  const last = finals(attempts);
  const missed = [...last.entries()].filter(([, a]) => keep.some((q) => ans(a, q.id) !== q.correct)).map(([u]) => u).sort((x, y) => x - y);
  const inT = questions.filter((q) => names.includes(q.topic));
  let right = 0;
  for (const a of last.values()) right += inT.filter((q) => ans(a, q.id) === q.correct).length;
  return { topics: names, questions: keep.map((q) => q.id), skipped, students: missed, before: pct(right, inT.length * last.size) };
}

export function progress(questions, attempts, topics, reQuestions, reAttempts) {
  const first = finals(attempts);
  const again = finals(reAttempts);
  const qa = questions.filter((q) => topics.includes(q.topic));
  const qb = reQuestions.filter((q) => topics.includes(q.topic));
  let rightA = 0;
  let rightB = 0;
  let wholeB = 0;
  for (const [u, a] of first) {
    const own = qa.filter((q) => ans(a, q.id) === q.correct).length;
    rightA += own;
    if (again.has(u) && qb.length) {
      rightB += qb.filter((q) => ans(again.get(u), q.id) === q.correct).length;
      wholeB += qb.length;
    } else {
      rightB += own;
      wholeB += qa.length;
    }
  }
  return { before: pct(rightA, qa.length * first.size), after: pct(rightB, wholeB), retook: [...first.keys()].filter((u) => again.has(u)).length };
}
