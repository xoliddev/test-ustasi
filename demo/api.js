// The Mini App's API answered by the in-page backend instead of HTTP (the same method names as webapp/api.js, the same
// shapes and error codes as the server), so the Mini App's code is identical on the server and in the demo. Notes the
// backend returns become bot messages in the phones.
import { civil, hhmm, localDay, localMinute } from '../shared/clock.js';

export function run(fn) {
  return Promise.resolve().then(() => {
    try {
      return structuredClone(fn());
    } catch (e) {
      if (!e.code) throw e;
      throw Object.assign(new Error(e.code), { code: e.code });
    }
  });
}

const stamp = (ms) => {
  const [y, m, d] = civil(localDay(ms));
  return `${String(d).padStart(2, '0')}.${String(m).padStart(2, '0')}.${y} ${hhmm(localMinute(ms))}`;
};
const LABELS = ['no', 'name', 'score', 'pct', 'grade', 'time', 'status', 'at', 'st_done', 'st_working', 'st_waiting'];

export function apiFor(b, uid, t) {
  const role = () => b.user(uid).role;
  const withNotes = (fn) => run(() => {
    const [res, notes] = fn();
    b.notify(notes);
    return res;
  });
  return {
    me: () => run(() => b.me(uid)),
    setLang: (lang) => run(() => ({ lang: b.setLang(uid, lang) })),
    tests: () => run(() => ({ items: role() === 'teacher' ? b.testsOf(uid) : b.myTests(uid) })),
    draft: (d) => run(() => b.makeDraft(uid, b.addSource(uid, d.text, d.title ?? '').id, d.n, d.mix)),
    test: (id) => run(() => (role() === 'teacher' ? b.draftView(uid, id) : b.testCard(uid, id))),
    settings: (id, d) => run(() => b.setSettings(uid, id, d)),
    publish: (id) => withNotes(() => b.publish(uid, id)),
    edit: (id, qid, d) => run(() => b.editQuestion(uid, id, qid, d)),
    remove: (id, qid) => run(() => b.deleteQuestion(uid, id, qid)),
    regen: (id, qid) => run(() => b.regenQuestion(uid, id, qid)),
    move: (id, qid, step) => run(() => b.moveQuestion(uid, id, qid, step)),
    results: (id) => run(() => b.results(uid, id)),
    analysis: (id) => run(() => b.analysis(uid, id)),
    csv: (id) => run(() => b.csv(uid, id, Object.fromEntries(LABELS.map((k) => [k, t(b.lang(uid), `csv.${k}`)])), stamp)),
    retest: (id) => withNotes(() => b.retest(uid, id)),
    classes: () => run(() => ({ items: b.classesOf(uid) })),
    addClass: (name) => run(() => b.createClass(uid, name)),
    klass: (id) => run(() => b.classDetail(uid, id)),
    invite: (id) => run(() => ({ link: `https://t.me/testustasi_bot?start=${b.invite(uid, id)}`, days: 14 })),
    start: (id) => withNotes(() => b.start(uid, id)),
    attempt: (id) => run(() => b.attemptView(uid, id)),
    answer: (id, pos, choice) => withNotes(() => b.answer(uid, id, pos, choice)),
    submit: (id) => withNotes(() => b.submit(uid, id)),
    result: (id) => run(() => {
      if (role() !== 'student') throw Object.assign(new Error('forbidden'), { code: 'forbidden' });
      return b.result(uid, id);
    }),
  };
}
