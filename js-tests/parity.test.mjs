// The JS port of the core must give exactly what the Python core gives (shared/test_vectors.json).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import * as A from '../shared/analysis.js';
import * as clock from '../shared/clock.js';
import * as G from '../shared/generate.js';
import * as numq from '../shared/numq.js';
import * as P from '../shared/passages.js';
import * as seedgen from '../shared/seedgen.js';
import * as shuffle from '../shared/shuffle.js';
import * as table from '../shared/table.js';
import * as T from '../shared/text.js';
import * as U from '../shared/uzwords.js';
import * as V from '../shared/validate.js';

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const VEC = read('../shared/test_vectors.json');
const texts = read('../shared/data/texts.json');
const canon = (x) => (Array.isArray(x) ? x.map(canon) : x && typeof x === 'object'
  ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, canon(x[k])])) : x);
const same = (a, b, msg) => assert.deepEqual(canon(JSON.parse(JSON.stringify(a))), canon(b), msg);
const stamp = (ms) => {
  const [y, m, d] = clock.civil(clock.localDay(ms));
  return `${String(d).padStart(2, '0')}.${String(m).padStart(2, '0')}.${y} ${clock.hhmm(clock.localMinute(ms))}`;
};

test('words: stems, case endings, inflection, numbers, normalising, sentences', () => {
  for (const [w, st, cs] of VEC.stem) assert.deepEqual([U.stem(w), U.caseStrip(w)], [st, cs], w);
  for (const [b, s, out] of VEC.inflect) assert.equal(U.inflect(b, s), out, `${b}+${s}`);
  const nums = VEC.numq.map((x) => x[0]);
  for (const [s, f, q] of VEC.numq) {
    same(numq.find(s), f, s);
    same(numq.question(s, nums), q, s);
  }
  for (const [s, nm, lat, src] of VEC.norm) assert.deepEqual([T.normMatch(s), T.latin(s), T.normalizeSource(s)], [nm, lat, src], s);
  for (const [s, out] of VEC.sentences) assert.deepEqual(P.sentences(s), out, s);
  for (const [s, h] of VEC.h32) assert.equal(T.h32(s), h, s);
});

test('the generator: passages, definitions, key terms, topics, every candidate and every selection', () => {
  for (const v of VEC.texts) {
    const a = G.analyse(v.body, v.title);
    same(a, v.analysis, `${v.id} analysis`);
    const cands = G.candidates(a);
    same(cands, v.candidates, `${v.id} candidates`);
    for (const n of G.COUNTS) for (const m of G.MIXES) assert.deepEqual(G.select(cands, n, m).map((q) => q.uid), v.select[`${n}:${m}`], `${v.id} ${n} ${m}`);
    const some = cands.slice(0, Math.max(1, Math.floor(cands.length / 2)));
    assert.deepEqual(G.select(cands, 6, 'mixed', some).map((q) => q.uid), v.select.more, `${v.id} more`);
    assert.deepEqual(G.select(cands, 6, 'mixed', some, true).map((q) => q.uid), v.select.same, `${v.id} same`);
  }
});

test('AI drafts: every check, the accepted questions and the reasons; a teacher edit', () => {
  const a = G.analyse(VEC.ai.source);
  const src = T.normMatch(a.body);
  const [out, why] = V.accept(VEC.ai.raws, src, a.passages, a.topics, 10);
  same(out, VEC.ai.out);
  same(why, VEC.ai.why);
  VEC.ai.raws.forEach((raw, i) => {
    let got;
    try {
      got = V.check(raw, src, a.passages, a.topics);
    } catch (e) {
      if (!(e instanceof V.Rejected)) throw e;
      got = e.message;
    }
    same(got, VEC.ai.checks[i][1], `check ${i}`);
  });
  for (const [d, exp] of VEC.edited) {
    let got;
    try {
      got = V.edited(d, VEC.ai.out[0]);
    } catch (e) {
      got = e.code;
    }
    same(got, exp, JSON.stringify(d));
  }
  for (const [x, q, exp] of VEC.grounded) assert.equal(V.grounded(x, q), exp, x);
});

test('the seeded shuffle and the seeded class on four days (today, New Year, a year end, a leap day)', () => {
  for (const [n, s, out] of VEC.perm) assert.deepEqual(shuffle.perm(n, s), out, `${n} ${s}`);
  let i = 0;
  for (const s of [shuffle.attemptSeed(7, 5, 1), shuffle.attemptSeed(7, -101, 2)]) {
    for (const sh of [true, false]) {
      assert.deepEqual([s, shuffle.layout([11, 12, 13, 14, 15], s, sh)], VEC.layout[i]);
      i += 1;
    }
  }
  for (const v of VEC.worlds) {
    const w = seedgen.world(texts, v.day);
    same(w, v.world, `world ${v.day}`);
    const traps = { 2: { kind: 'pick', option: 1, share: 60 }, 5: { kind: 'key', option: 0 } };
    same(seedgen.simulate(w.tests[0].questions, w.students, `demo:${v.day}`, traps, 0), v.sim, `sim ${v.day}`);
  }
});

test('the results table, the question analysis, topics, the retest plan and the CSV', () => {
  for (const v of VEC.worlds) {
    const w = seedgen.world(texts, v.day);
    const people = w.students.map((s) => ({ id: s.id, name: s.name }));
    w.tests.forEach((t, k) => {
      const qa = t.attempts.map((a, i) => ({ ...a, id: i + 1 }));
      const rep = v.reports[k];
      const tab = A.table(people, qa, t.questions.length);
      same(tab, rep.table, `table ${v.day} ${k}`);
      same(A.questionsReport(t.questions, qa), rep.questions);
      same(A.topicsReport(t.questions, qa), rep.topics);
      same(A.retestPlan(t.questions, qa), rep.plan);
      const marks = Object.fromEntries(qa.map((a) => [a.user, t.questions.map((q) => (a.answers[q.id] === q.correct ? 1 : 0))]));
      const labels = { no: '№', name: 'Ism', score: 'Ball', pct: 'Foiz', grade: 'Baho', time: 'Vaqt', status: 'Holat', at: 'Topshirgan', st_done: 'topshirdi',
        st_working: 'yechyapti', st_waiting: 'boshlamagan' };
      assert.equal(table.csvText(labels, tab.rows, marks, t.questions.length, stamp), rep.csv);
    });
  }
  for (const [p, pc, rd] of VEC.small) assert.deepEqual([A.pct(...p), p[1] ? A.rdiv(...p) : null], [pc, rd], String(p));
  for (const [x, m] of VEC.median) assert.equal(A.median(x), m);
  for (const [x, out] of VEC.cells) assert.equal(table.cell(x), out, String(x));
});
