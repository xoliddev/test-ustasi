// JS port of testustasi/core/shuffle.py: mulberry32 seeded with FNV-1a, Fisher-Yates; the same permutation as the server.
import { h32 } from './text.js';

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a) >>> 0;
    t = (((t + Math.imul(t ^ (t >>> 7), 61 | t)) >>> 0) ^ t) >>> 0;
    return (t ^ (t >>> 14)) >>> 0;
  };
}

export function perm(n, seed) {
  const out = Array.from({ length: n }, (_, i) => i);
  const next = rng(seed);
  for (let i = n - 1; i > 0; i--) {
    const j = next() % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export const attemptSeed = (test, user, no) => h32(`${test}:${user}:${no}`);

export function layout(qids, seed, shuffle = true) {
  const order = shuffle ? perm(qids.length, seed) : qids.map((_, i) => i);
  return order.map((i) => ({ qid: qids[i], opts: shuffle ? perm(4, h32(`${seed}:${qids[i]}`)) : [0, 1, 2, 3] }));
}
