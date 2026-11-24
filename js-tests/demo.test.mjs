// The demo's story headless: the in-page backend runs the server's rules, the steps work in order and out of order, on
// any day (30 days in a row, across New Year), and the simulated bots get the same messages the real bot sends.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { atLocal, daysFromCivil } from '../shared/clock.js';
import { makeT } from '../shared/i18n.js';
import { apiFor } from '../demo/api.js';
import { BotSim } from '../demo/bot.js';
import { makeViews } from '../demo/bot-views.js';
import { createDemo, JASUR, NODIRA } from '../demo/seed.js';
import { captionParams, runStep, STEPS } from '../demo/story.js';

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const catalogs = { uz: read('../shared/locales/uz.json'), ru: read('../shared/locales/ru.json') };
const data = { catalogs, texts: read('../shared/data/texts.json') };
const t = makeT(catalogs);

function world(day = daysFromCivil(2026, 11, 25)) {
  const real = atLocal(day, 7 * 60 + 30);
  const started = Date.now();
  const backend = createDemo({ data, now: () => real + (Date.now() - started) });
  const views = makeViews(t);
  const bots = Object.fromEntries([NODIRA, JASUR].map((uid) => [uid, new BotSim(backend, uid, t, views)]));
  backend.on((ev) => { if (ev.type === 'note') bots[ev.note.to]?.deliver(ev.note); });
  bots[NODIRA].start();
  bots[JASUR].start();
  return { backend, bots, env: { backend, bots, done: new Set(), texts: data.texts, t, lang: () => 'uz', s: {} } };
}
const texts = (bot) => bot.messages.map((m) => m.html).join('\n');
const last = (bot) => bot.messages[bot.messages.length - 1].html;

test('the whole story in order: a file, the draft with quotes, the teacher edits, publishes, Jasur solves 7/10, the class, the analysis, the retest, progress', async () => {
  const { backend: b, bots, env } = world();
  assert.match(texts(bots[NODIRA]), /👩‍🏫 <b>Nodira ustoz<\/b>\nSinflar: 1 · testlar: 3/);
  assert.match(texts(bots[JASUR]), /🎓 <b>Jasur Toshpo'latov<\/b>/);
  await runStep(1, env);
  assert.match(last(bots[NODIRA]), /^✅ <b>Qoralama tayyor: Fotosintez<\/b>\n11 ta savol \(so'ralgani 15 ta edi/);
  await runStep(2, env);
  assert.equal(captionParams(2, env).n, 11);
  await runStep(3, env);
  const qs = b.questionsOf(env.s.test);
  assert.equal(qs.length, 10);
  assert.deepEqual(qs[5].options, ['Vodorod', 'Havo', 'Karbonat angidrid', 'Kislorod']);
  assert.ok(qs[5].edited && qs[2].stem === 'Xlorofill saqlovchi mayda tanachalar nima deb ataladi?');
  await runStep(4, env);
  assert.match(last(bots[JASUR]), /^📝 <b>Yangi test: Fotosintez<\/b>\n10 ta savol · 15 daqiqa\nMuddat: bugun, 23:59$/);
  await runStep(5, env);
  await runStep(6, env);
  const r = b.result(JASUR, env.s.test);
  assert.equal(`${r.score}/${r.total}`, '7/10');
  assert.deepEqual(r.mistakes.map((m) => m.correct).sort(), ['21%', 'Kislorod', 'Xloroplast']);
  assert.ok(r.mistakes.every((m) => m.quote));
  await runStep(7, env);
  assert.match(last(bots[NODIRA]), /^📊 <b>Fotosintez<\/b> — hamma topshirdi\nTopshirdi: 25\/25/);
  const res = b.results(NODIRA, env.s.test);
  assert.equal(res.stats.done, 25);
  await runStep(8, env);
  const an = b.analysis(NODIRA, env.s.test);
  assert.equal(an.questions[5].flag, 'key');
  assert.equal(an.questions[2].flag, 'hard');
  assert.equal(an.questions[2].pick.letter, 'A');
  assert.ok(an.questions[2].pick.pct >= 45, String(an.questions[2].pick.pct));
  await runStep(9, env);
  assert.match(last(bots[JASUR]), /^🔁 <b>Qayta test: Fotosintez<\/b>/);
  const targets = b.targets.filter((g) => g.test === env.s.retest).map((g) => g.user);
  assert.ok(targets.includes(JASUR) && targets.length < 25 && targets.length >= 8, String(targets.length));
  await runStep(10, env);
  const pr = b.analysis(NODIRA, env.s.test).progress;
  assert.ok(pr.after - pr.before >= 25 && pr.after >= 75, JSON.stringify(pr));
  assert.match(last(bots[NODIRA]), /📈 Shu mavzular bo'yicha guruh natijasi: \d+% → \d+%/);
  assert.match(captionParams(10, env).before, /^\d+%$/);
});

test('steps clicked out of order quietly do what they need first, and a step clicked twice does nothing twice', async () => {
  for (const n of [10, 3, 6, 7, 9]) {
    const { backend: b, env } = world();
    await runStep(n, env);
    assert.deepEqual([...env.done].sort((x, y) => x - y), Array.from({ length: n }, (_, i) => i + 1));
    const tests = b.tests.length;
    await runStep(n, env);
    assert.equal(b.tests.length, tests);
    if (n >= 6) assert.equal(b.attempts.filter((a) => a.user === JASUR && a.test === env.s.test).length, 1);
  }
});

test('the story on 30 days in a row and across New Year', async () => {
  const days = [...Array.from({ length: 30 }, (_, k) => daysFromCivil(2026, 12, 10) + k), daysFromCivil(2027, 1, 1)];
  for (const day of days) {
    const { backend: b, env } = world(day);
    for (let n = 1; n <= STEPS.length; n++) await runStep(n, env);
    assert.equal(b.today(), day);
    const an = b.analysis(NODIRA, env.s.test);
    assert.equal(an.questions[5].flag, 'key', String(day));
    assert.ok(an.progress.after > an.progress.before, String(day));
    assert.equal(b.result(JASUR, env.s.test).score, 7);
  }
});

test('the API stand-ins answer like the server: roles, errors, no answers for a student before submitting', async () => {
  const { backend: b, env } = world();
  await runStep(4, env);
  const jasur = apiFor(b, JASUR, t);
  const nodira = apiFor(b, NODIRA, t);
  await assert.rejects(jasur.results(env.s.test), { code: 'forbidden' });
  await assert.rejects(jasur.classes(), { code: 'forbidden' });
  await assert.rejects(nodira.result(env.s.test), { code: 'forbidden' });
  await assert.rejects(nodira.settings(env.s.test, { minutes: 5 }), { code: 'published' });
  const view = await jasur.start(env.s.test);
  const blob = JSON.stringify(view);
  for (const w of ['correct', 'explanation', 'quote', 'qid']) assert.ok(!blob.includes(`"${w}"`), w);
  await assert.rejects(jasur.result(env.s.test), { code: 'not_submitted' });
  await assert.rejects(jasur.answer(view.attempt, 0, 9), { code: 'generic' });
  const csv = await nodira.csv(1);
  assert.ok(csv.csv.startsWith('﻿№;Ism;Ball;Foiz;Baho;Vaqt (daq:son);Holat;Topshirgan vaqti'));
});
