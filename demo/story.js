// The guided story. Each step does what a person would do, through Nodira ustoz's phone (the bot and the Mini App) and
// Jasur's (the bot and the Mini App). Steps run in order (with pauses), all at once ("Hammasini ko'rsatish"), or
// clicked out of order: a step first quietly does whatever it needs from earlier steps. Without the page (the headless
// tests) the same actions go straight to the bots and the backend.
import { atLocal } from '../shared/clock.js';
import { pct } from '../shared/i18n.js';
import { JASUR, NODIRA } from './seed.js';

export const STEPS = ['send', 'draft', 'edit', 'publish', 'solve', 'result', 'class', 'analysis', 'retest', 'progress'];
const STRONG_MISTAKE = 'Vodorod';
const JASUR_WRONG = { 3: "Og'izcha", 6: STRONG_MISTAKE, 9: '31%' }; // teacher's order (1-based) -> the option Jasur picks

function find(env, uid, rx) {
  for (const m of [...env.bots[uid].messages].reverse()) for (const row of m.kb) for (const b of row) if (b.data && rx.test(b.data)) return [m, b];
  return [null, null];
}

async function tap(env, uid, rx) {
  const [m, b] = find(env, uid, rx);
  if (!b) throw new Error(`demo: no button ${rx} for ${uid}`);
  if (env.ui) await env.ui.botTap(uid, b.data);
  else env.bots[uid].press(m.id, b.data);
}

const qs = (env) => env.backend.questionsOf(env.s.test);
const optionIndex = (q, text) => q.options.indexOf(text);

/** The traps that make the class's answers tell the story: most pick «Og'izcha» in question 3; in question 6 the
 * misleading «Vodorod» catches even the strong students. */
export function traps(env) {
  const list = qs(env);
  return { 2: { kind: 'pick', option: optionIndex(list[2], "Og'izcha"), share: 70 }, 5: { kind: 'key', option: optionIndex(list[5], STRONG_MISTAKE) } };
}

const ACTIONS = {
  // 1. 08:10. Nodira sends the "Fotosintez" text as a file, asks for 15 questions, "Aralash".
  async 1(env) {
    const { backend: b, bots, focus, pause } = env;
    focus(NODIRA, 'chat');
    b.at(8 * 60 + 10);
    const text = env.texts.find((t) => t.id === 'fotosintez').body;
    if (env.ui) await env.ui.sendFile(NODIRA, 'Fotosintez.txt', text);
    else bots[NODIRA].sendFile('Fotosintez.txt', text);
    await pause(1100);
    await tap(env, NODIRA, /^n:\d+:15$/);
    await pause(700);
    await tap(env, NODIRA, /^x:\d+:15:mixed$/);
    env.s.test = b.testsOf(NODIRA).find((t) => t.status === 'draft').id;
    await pause(1500);
  },
  // 2. The draft in the Mini App: every question with its quote from the text.
  async 2(env) {
    const { focus, pause, ui } = env;
    focus(NODIRA, 'app');
    await ui?.appOpen(NODIRA, { view: 'test', id: env.s.test });
    await ui?.scrollApp(NODIRA, '[data-testid=quote-3]');
    await pause(2200);
  },
  // 3. She deletes question 4 (half-true "kislorodni") and, in what becomes question 6, replaces «O'simlik» with «Vodorod».
  async 3(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(NODIRA, 'app');
    const q4 = qs(env)[3];
    if (ui) {
      await ui.appOpen(NODIRA, { view: 'test', id: env.s.test });
      await ui.appClick(NODIRA, '[data-testid=delete-4]');
      await ui.appClick(NODIRA, '[data-testid=confirm-yes]', 500);
    } else b.deleteQuestion(NODIRA, env.s.test, q4.id);
    await pause(900);
    const q6 = qs(env)[5];
    const k = q6.options.indexOf("O'simlik");
    if (ui) {
      await ui.appClick(NODIRA, '[data-testid=edit-6]');
      await ui.appFill(NODIRA, `[data-testid=edit-opt-${k}]`, STRONG_MISTAKE);
      await ui.appClick(NODIRA, '[data-testid=edit-save]', 500);
    } else b.editQuestion(NODIRA, env.s.test, q6.id, { options: q6.options.map((o, i) => (i === k ? STRONG_MISTAKE : o)) });
    await pause(1400);
  },
  // 4. 08:30. 7-B, 15 minutes, today 23:59 -> "Nashr qilish": 25 students get a message.
  async 4(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(NODIRA, 'app');
    b.at(8 * 60 + 30);
    const deadline = atLocal(b.today(), 23 * 60 + 59);
    if (ui) {
      await ui.appOpen(NODIRA, { view: 'test', id: env.s.test });
      await ui.scrollApp(NODIRA, '[data-testid=settings]');
      await ui.appClick(NODIRA, '[data-testid=set-class] [data-v="1"]');
      await ui.appClick(NODIRA, '[data-testid=set-minutes] [data-v="15"]');
      await ui.appClick(NODIRA, '[data-testid=set-deadline] [data-v="today"]');
      await ui.appClick(NODIRA, '[data-testid=publish]');
      await ui.appClick(NODIRA, '[data-testid=confirm-yes]', 600);
    } else {
      b.setSettings(NODIRA, env.s.test, { grp: 1, minutes: 15, deadline });
      b.notify(b.publish(NODIRA, env.s.test)[1]);
    }
    await pause(1600);
  },
  // 5. 09:05. Jasur opens the message and solves: his own order, the server's timer.
  async 5(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(JASUR, 'chat');
    b.at(9 * 60 + 5);
    await pause(900);
    const byStem = Object.fromEntries(qs(env).map((q, i) => [q.stem, [q, i + 1]]));
    if (ui) {
      await ui.botTapApp(JASUR, `?s=${env.s.test}`);
      focus(JASUR, 'app');
      await ui.appClick(JASUR, '[data-testid=start]', 600);
    }
    const [view] = ui ? [await ui.attempt(JASUR)] : b.start(JASUR, env.s.test);
    env.s.attempt = view.attempt;
    for (const item of view.questions) {
      const [q, n] = byStem[item.stem];
      const want = JASUR_WRONG[n] ?? q.options[q.correct];
      const choice = item.options.indexOf(want);
      b.offset += 38_000;
      if (ui) {
        await ui.appClick(JASUR, `[data-testid=opt-${choice}]`, 260);
        if (item.pos < view.questions.length - 1) await ui.appClick(JASUR, '[data-testid=next]', 240);
      } else b.answer(JASUR, view.attempt, item.pos, choice);
    }
    await pause(700);
  },
  // 6. He submits: 7/10, and every mistake with the correct answer and the quote.
  async 6(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(JASUR, 'app');
    if (ui) {
      await ui.appOpen(JASUR, { view: 'solve', id: env.s.test });
      await ui.appClick(JASUR, '[data-testid=submit]');
      await ui.appClick(JASUR, '[data-testid=confirm-yes]', 700);
      await ui.scrollApp(JASUR, '[data-testid=mistakes]');
    } else b.notify(b.submit(JASUR, env.s.attempt)[1]);
    await pause(2200);
  },
  // 7. The rest of 7-B finishes (simulated through the same rules); Nodira's table and grade chart fill live.
  async 7(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(NODIRA, 'app');
    await ui?.appOpen(NODIRA, { view: 'results', id: env.s.test });
    const rest = b.targets.filter((g) => g.test === env.s.test && g.user !== JASUR).map((g) => g.user);
    const tr = traps(env);
    for (let i = 0; i < rest.length; i += 6) {
      b.notify(b.simulateClass(env.s.test, tr, { only: rest.slice(i, i + 6), from: b.nowMs() }));
      b.offset += 6 * 60_000;
      b.changed();
      await pause(650);
    }
    b.at(9 * 60 + 50);
    await pause(1200);
  },
  // 8. The analysis: question 6 — even the strong students went wrong (check the question); question 3 — most picked «Og'izcha».
  async 8(env) {
    const { focus, pause, ui } = env;
    focus(NODIRA, 'app');
    await ui?.appOpen(NODIRA, { view: 'analysis', id: env.s.test });
    await ui?.scrollApp(NODIRA, '[data-testid=aq-3]');
    await pause(1700);
    await ui?.scrollApp(NODIRA, '[data-testid=aq-6]');
    await pause(1700);
  },
  // 9. "Xato savollar bo'yicha qayta test": a short test, only to those who missed the weak topics.
  async 9(env) {
    const { backend: b, focus, pause, ui } = env;
    focus(NODIRA, 'app');
    b.at(10 * 60);
    if (ui) {
      await ui.appOpen(NODIRA, { view: 'analysis', id: env.s.test });
      await ui.scrollApp(NODIRA, '[data-testid=retest-box]');
      await ui.appClick(NODIRA, '[data-testid=retest]');
      await ui.appClick(NODIRA, '[data-testid=confirm-yes]', 700);
    } else b.notify(b.retest(NODIRA, env.s.test)[1]);
    env.s.retest = b.tests.find((t) => t.parent === env.s.test).id;
    await pause(1200);
    focus(JASUR, 'chat');
    await pause(1400);
  },
  // 10. 15:00. The retest results: the class's score on those topics rises; the story ends on the progress.
  async 10(env) {
    const { backend: b, focus, pause, ui } = env;
    b.at(15 * 60);
    b.notify(b.simulateClass(env.s.retest, {}, { boost: 8, seed: 'retest', from: b.nowMs() - 3 * 3_600_000 }));
    focus(NODIRA, 'chat');
    await pause(1800);
    focus(NODIRA, 'app');
    await ui?.appOpen(NODIRA, { view: 'analysis', id: env.s.test });
    await ui?.scrollApp(NODIRA, '[data-testid=progress]');
    await pause(900);
  },
};

/** The numbers a caption mentions, from the same backend the phones show. */
export function captionParams(n, env) {
  const b = env.backend;
  const t = (l, k, p) => env.t(l, k, p);
  if (!env.s.test) return {};
  if (n === 2) return { n: b.questionsOf(env.s.test).length };
  if (n === 6 && env.s.attempt) return b.result(JASUR, env.s.test);
  if (n === 8) {
    const pick = b.analysis(NODIRA, env.s.test).questions[2].pick;
    return pick ? { pct: pick.pct, letter: pick.letter } : {};
  }
  if (n === 9 && env.s.retest) return { n: b.targets.filter((g) => g.test === env.s.retest).length };
  if (n === 10 && env.s.retest) {
    const pr = b.analysis(NODIRA, env.s.test).progress;
    return pr ? { before: pct(t, env.lang(), pr.before), after: pct(t, env.lang(), pr.after) } : {};
  }
  return {};
}

export async function runStep(n, env, quick = false, done = env.done ?? (env.done = new Set())) {
  env.s = env.s ?? {};
  for (let k = 1; k < n; k++) if (!done.has(k)) await runStep(k, env, true, done);
  if (done.has(n)) return;
  const wait = quick ? async () => {} : env.wait ?? (async () => {});
  const ctx = new Proxy(env, { get: (target, key) => {
    if (key === 'ui') return quick ? null : target.ui;
    if (key === 'focus') return quick ? () => {} : target.focus ?? (() => {});
    if (key === 'pause') return (ms = 650) => wait(ms);
    return target[key];
  } });
  await ACTIONS[n](ctx);
  done.add(n);
}
