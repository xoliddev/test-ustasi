// JS port of testustasi/core/seedgen.py: the invented class (Nodira ustoz, 7-B, 25 students, three earlier tests) and
// `simulate`, which the demo also uses for "the other students finish".
import { atLocal } from './clock.js';
import { generate } from './generate.js';
import { h32 } from './text.js';

export const TEACHER = { id: -1, name: 'Nodira ustoz' };
export const GROUP = { id: 1, name: '7-B', teacher: -1 };
export const NAMES = ["Jasur Toshpo'latov", 'Madina Rahimova', 'Sardor Aliyev', 'Dilnoza Karimova', 'Bekzod Usmonov', "Zarina Yo'ldosheva", 'Otabek Nazarov',
  'Malika Saidova', 'Sanjar Qodirov', 'Gulnoza Ergasheva', 'Jahongir Murodov', 'Nilufar Hasanova', 'Shohruh Ismoilov', 'Kamola Tursunova',
  'Doniyor Sobirov', 'Sevara Mirzayeva', "Ulug'bek Xolmatov", 'Mohinur Rustamova', 'Bobur Abdullayev', "Feruza Jo'rayeva", 'Asadbek Nurmatov',
  'Shahzoda Qosimova', 'Islom Yusupov', 'Ruxshona Olimova', 'Temur Ahmedov'];
export const ABILITY = [70, 88, 65, 91, 54, 79, 47, 83, 60, 95, 69, 58, 76, 42, 86, 63, 52, 80, 72, 45, 67, 93, 56, 74, 61];
export const HISTORY = [['hujayra', 29, 8, 15], ['ildiz', 18, 8, 10], ['barg', 8, 10, 15]];
export const LESSON = 8 * 60 + 30;
const ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';

export const students = () => NAMES.map((name, i) => ({ id: -101 - i, name, ability: ABILITY[i] }));

function pickWrong(q, h) {
  const wrong = [0, 1, 2, 3].filter((i) => i !== q.correct);
  return wrong[[0, 0, 1, 2, 1, 0][h % 6]];
}

export function simulate(questions, people, seed, traps = {}, boost = 0) {
  return people.map((s) => {
    const a = s.ability + boost;
    const answers = {};
    questions.forEach((q, i) => {
      const r = h32(`${seed}:${s.id}:${q.id}`) % 100;
      const t = traps[i];
      if (t && t.kind === 'pick' && h32(`pick:${seed}:${s.id}:${q.id}`) % 100 < t.share) {
        answers[q.id] = t.option;
        return;
      }
      if (t && t.kind === 'key') {
        if (a >= 72) answers[q.id] = r < 75 ? t.option : q.correct;
        else answers[q.id] = r < 35 ? t.option : r < 75 ? q.correct : pickWrong(q, r);
        return;
      }
      const bias = (h32(`q:${seed}:${q.id}`) % 21) - 10;
      const p = Math.max(5, Math.min(97, a + (2 - q.level) * 10 + bias));
      answers[q.id] = r < p ? q.correct : pickWrong(q, h32(`w:${seed}:${s.id}:${q.id}`));
    });
    const seconds = questions.length * (40 + Math.floor(((100 - a) * 3) / 4)) + (h32(`t:${seed}:${s.id}`) % 90);
    return { user: s.id, answers, seconds };
  });
}

export function code(n) {
  const h = h32(`code:${n}`);
  return Array.from({ length: 6 }, (_, i) => ALPHABET[(h >>> (5 * i)) % ALPHABET.length]).join('');
}

export function world(texts, today) {
  const people = students();
  const byId = Object.fromEntries(texts.map((t) => [t.id, t]));
  const tests = HISTORY.map(([tid, ago, n, minutes], k) => {
    const text = byId[tid];
    const qs = generate(text.body, n, 'mixed', text.title);
    qs.forEach((q, pos) => { q.id = (k + 1) * 100 + pos + 1; });
    const day = today - ago;
    const sims = simulate(qs, people, `seed:${tid}`);
    const attempts = [];
    people.forEach((s, i) => {
      if (h32(`skip:${tid}:${s.id}`) % 25 === 0) return;
      const start = atLocal(day, 14 * 60 + (h32(`start:${tid}:${s.id}`) % 420));
      const used = Math.min(sims[i].seconds, minutes * 60 - 5);
      const right = qs.filter((q) => sims[i].answers[q.id] === q.correct).length;
      attempts.push({ user: s.id, no: 1, started_at: start, submitted_at: start + used * 1000, score: right, answers: sims[i].answers, auto: used === minutes * 60 - 5 });
    });
    return { id: k + 1, text: tid, title: text.title, questions: qs, published_at: atLocal(day, LESSON), deadline: atLocal(day + 2, 23 * 60 + 59), minutes, attempts,
      code: code(k + 1) };
  });
  return { teacher: TEACHER, group: GROUP, students: people, tests };
}
