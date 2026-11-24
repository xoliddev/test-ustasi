// JS port of testustasi/bot/views.py: the bot's screens as {html, kb}, so the simulated bot in the demo reads and behaves
// exactly like the real one (the same texts, buttons and callback data).
import { MIN_FLAGS } from '../shared/analysis.js';
import * as I from '../shared/i18n.js';
import { short } from '../shared/text.js';

const { Raw } = I;

export function makeViews(t) {
  const btn = (text, data) => ({ text, data });
  const app = (text, where = '') => ({ text, app: where });
  const back = (lang, data = 'm') => [btn(t(lang, 'btn.back'), data)];
  const Q = (lang, n) => I.questions(t, lang, n);
  const MIN = (lang, n) => I.minutes(t, lang, n);
  const PCT = (lang, n) => I.pct(t, lang, n);
  const WHEN = (lang, ms, now) => I.when(t, lang, ms, now);
  const v = {
    btn, back,
    hello: (lang) => ({ html: t(lang, 'bot.hello'), kb: [[btn(t(lang, 'btn.teacher'), 'role:t')], [btn(t(lang, 'btn.student'), 'role:s')], [btn(t(lang, 'btn.lang'), 'lang')]] }),
    menuTeacher: (lang, name, classes, tests) => ({ html: t(lang, 'bot.menu_teacher', { name, classes, tests }), kb: [[btn(t(lang, 'btn.new_test'), 'nt')],
      [btn(t(lang, 'btn.tests'), 'tl'), btn(t(lang, 'btn.classes'), 'cl')], [app(t(lang, 'btn.app'))], [btn(t(lang, 'btn.help'), 'h'), btn(t(lang, 'btn.lang'), 'lang')]] }),
    menuStudent: (lang, name, fresh) => ({ html: t(lang, 'bot.menu_student', { name, line: fresh ? t(lang, 'bot.student_new', { n: fresh }) : t(lang, 'bot.student_none') }),
      kb: [[btn(t(lang, 'btn.tests'), 'st')], [btn(t(lang, 'btn.code'), 'code')], [btn(t(lang, 'btn.help'), 'h'), btn(t(lang, 'btn.lang'), 'lang')]] }),
    joinedStudent: (lang) => ({ html: t(lang, 'bot.student_join'), kb: [[btn(t(lang, 'btn.code'), 'code')], [btn(t(lang, 'btn.menu'), 'm')]] }),
    help: (lang, role) => ({ html: t(lang, role === 'student' ? 'bot.help_student' : 'bot.help_teacher'), kb: [back(lang)] }),
    newTest: (lang) => ({ html: t(lang, 'bot.new_test'), kb: [back(lang)] }),
    gotSource: (lang, src) => ({ html: t(lang, 'bot.got_source', { title: src.title, passages: src.passages, chars: I.num(src.chars) }),
      kb: [[5, 10, 15, 20].map((n) => btn(t(lang, 'btn.n', { n }), `n:${src.id}:${n}`)), back(lang)] }),
    askMix: (lang, src, n) => ({ html: t(lang, 'bot.ask_mix', { title: src.title, n }),
      kb: [['easy', 'mixed', 'hard'].map((m) => btn(t(lang, `btn.mix_${m}`), `x:${src.id}:${n}:${m}`)), back(lang, `n:${src.id}`)] }),
    draftReady(lang, d, hasApp) {
      const n = d.questions.length;
      const fewer = n < d.asked ? t(lang, 'bot.fewer', { asked: d.asked }) : '';
      const kb = hasApp ? [[app(t(lang, 'btn.review'), `?t=${d.id}`)]] : [];
      kb.push([btn(t(lang, 'btn.tests'), '+tl'), btn(t(lang, 'btn.menu'), '+m')]);
      const html = t(lang, 'bot.draft_ready', { title: d.title, count: Q(lang, n), fewer });
      return { html: hasApp ? html : `${html}\n\n${t(lang, 'bot.no_app')}`, kb };
    },
    testsList(lang, items) {
      if (!items.length) return { html: t(lang, 'bot.tests_none'), kb: [back(lang)] };
      const rows = items.slice(0, 10).map((it) => {
        const key = it.status === 'draft' ? 'bot.test_draft_row' : it.parent ? 'bot.test_retest_row' : 'bot.test_row';
        return [btn(t(lang, key, { title: short(it.title, 34), done: it.done, people: it.people }), `t:${it.id}`)];
      });
      return { html: t(lang, 'bot.tests'), kb: [...rows, back(lang)] };
    },
    testCard(lang, d, res, an, now) {
      if (d.status === 'draft') return { html: t(lang, 'bot.card_draft', { title: d.title, count: Q(lang, d.questions.length) }), kb: [[app(t(lang, 'btn.review'), `?t=${d.id}`)], back(lang, 'tl')] };
      const st = res.stats;
      let flags = '';
      if (an && an.n >= MIN_FLAGS) {
        const keys = an.questions.filter((r) => r.flag === 'key').length;
        const hard = an.questions.filter((r) => r.flag === 'hard').length;
        flags = (keys ? t(lang, 'bot.flags', { n: keys }) : '') + (hard ? t(lang, 'bot.flags_hard', { n: hard }) : '');
      }
      const code = d.parent ? t(lang, 'bot.card_retest') : t(lang, 'bot.card_code', { code: d.code });
      const deadline = d.deadline ? t(lang, 'bot.card_deadline', { when: WHEN(lang, d.deadline, now) }) : '';
      const cls = d.classes.find((k) => k.id === d.grp)?.name ?? '';
      const html = t(lang, 'bot.card', { title: d.title, cls, count: Q(lang, d.questions.length), minutes: MIN(lang, d.minutes), deadline, code: new Raw(code),
        done_lbl: t(lang, 'lbl.done'), done: st.done, people: st.people, avg_lbl: t(lang, 'lbl.avg'), avg: st.done ? PCT(lang, st.avg) : '—', flags: new Raw(flags) });
      const kb = [[app(t(lang, 'btn.results'), `?r=${d.id}`), app(t(lang, 'btn.analysis'), `?a=${d.id}`)]];
      if (an && !d.parent && an.retest === null && an.plan.topics.length && an.plan.count) kb.push([btn(t(lang, 'btn.retest'), `rq:${d.id}`)]);
      if (st.done) kb.push([btn(t(lang, 'btn.csv'), `csv:${d.id}`)]);
      return { html, kb: [...kb, back(lang, 'tl')] };
    },
    retestAsk(lang, tid, plan) {
      const names = plan.names.slice(0, 12).map((n) => n.split(' ')[0]).join(', ') + (plan.names.length > 12 ? '…' : '');
      return { html: t(lang, 'bot.retest_ask', { topics: plan.topics.join(', '), count: plan.count, names }), kb: [[btn(t(lang, 'btn.retest_send'), `rx:${tid}`)], back(lang, `t:${tid}`)] };
    },
    retestSent: (lang, tid, info) => ({ html: info.again ? t(lang, 'bot.retest_again') : t(lang, 'bot.retest_sent', { students: info.students, count: Q(lang, info.count) }),
      kb: [[app(t(lang, 'btn.results'), `?r=${info.id}`)], back(lang, `t:${tid}`)] }),
    classesList: (lang, items) => ({ html: t(lang, 'bot.classes'), kb: [...items.slice(0, 20).map((k) => [btn(t(lang, 'bot.class_row', { name: k.name, n: I.students(t, lang, k.students) }),
      `c:${k.id}`)]), [btn(t(lang, 'btn.new_class'), 'cn')], back(lang)] }),
    classScreen: (lang, k, link, days) => ({ html: t(lang, 'bot.class', { name: k.name, count: I.students(t, lang, k.students.length),
      names: k.students.slice(0, 40).map((s) => s.name.split(' ')[0]).join(', '), days, link }), kb: [back(lang, 'cl')] }),
    askClass: (lang) => ({ html: t(lang, 'bot.ask_class'), kb: [back(lang, 'cl')] }),
    askCode: (lang) => ({ html: t(lang, 'bot.ask_code'), kb: [back(lang)] }),
    myTests(lang, items) {
      if (!items.length) return { html: t(lang, 'bot.my_none'), kb: [back(lang)] };
      const key = { new: 'bot.my_new', working: 'bot.my_working', done: 'bot.my_done', closed: 'bot.my_closed' };
      return { html: t(lang, 'bot.my_tests'), kb: [...items.slice(0, 10).map((it) => [app(t(lang, key[it.status], { title: short(it.title, 32),
        count: it.status === 'new' ? Q(lang, it.count) : it.count, score: it.score ?? 0 }), `?s=${it.id}`)]), back(lang)] };
    },
    codeJoined: (lang, j) => ({ html: t(lang, 'bot.joined_code', { cls: j.class, title: j.title }), kb: [[app(t(lang, 'btn.start_test'), `?s=${j.test}`)], [btn(t(lang, 'btn.menu'), '+m')]] }),
    note(lang, n, now) {
      const deadline = n.deadline ? t(lang, 'note.deadline', { when: WHEN(lang, n.deadline, now) }) : '';
      const go = [[app(t(lang, 'btn.start_test'), `?s=${n.test}`)]];
      if (n.kind === 'new_test') return { html: t(lang, 'note.new_test', { title: n.title, count: Q(lang, n.count), minutes: MIN(lang, n.minutes), deadline: new Raw(deadline) }), kb: go };
      if (n.kind === 'retest') {
        return { html: t(lang, 'note.retest', { title: n.title, topics: n.topics.join(', '), count: Q(lang, n.count), minutes: MIN(lang, n.minutes), deadline: new Raw(deadline) }), kb: go };
      }
      if (n.kind === 'reminder') return { html: t(lang, 'note.reminder', { title: n.title, when: WHEN(lang, n.deadline, now) }), kb: go };
      const head = t(lang, n.reason === 'all' ? 'note.summary_all' : 'note.summary_deadline', { title: n.title });
      const flags = (n.flags.key ? t(lang, 'bot.flags', { n: n.flags.key }) : '') + (n.flags.hard ? t(lang, 'bot.flags_hard', { n: n.flags.hard }) : '');
      const pr = n.progress;
      const progress = pr && pr.retook ? t(lang, 'note.progress', { before: PCT(lang, pr.before), after: PCT(lang, pr.after) }) : '';
      return { html: t(lang, 'note.summary', { head: new Raw(head), done_lbl: t(lang, 'lbl.done'), done: n.done, people: n.people, avg_lbl: t(lang, 'lbl.avg'), avg: PCT(lang, n.avg),
        median_lbl: t(lang, 'lbl.median'), median: PCT(lang, n.median), flags: new Raw(flags), progress: new Raw(progress) }),
      kb: [[app(t(lang, 'btn.results'), `?r=${n.test}`), app(t(lang, 'btn.analysis'), `?a=${n.test}`)]] };
    },
  };
  return v;
}
