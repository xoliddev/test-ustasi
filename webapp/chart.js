// Charts drawn as SVG in code: the grade distribution (5, 4, 3, 2) and a horizontal percentage bar.
import { s } from './util.js';

const GRADE_COLORS = { 5: '#1f9d6b', 4: '#3a86c8', 3: '#e2a23b', 2: '#d9534f' };

export function gradeChart(grades, label) {
  const W = 320;
  const H = 150;
  const top = Math.max(1, ...Object.values(grades));
  const svg = s('svg', { class: 'u-chart', viewBox: `0 0 ${W} ${H}`, role: 'img', 'data-testid': 'grade-chart', 'aria-label': label });
  [5, 4, 3, 2].forEach((g, i) => {
    const n = grades[g] ?? 0;
    const bw = 52;
    const x = 22 + i * 76;
    const bh = Math.round((n / top) * 92);
    const y = 112 - bh;
    svg.append(s('rect', { x, y: 20, width: bw, height: 92, rx: 8, class: 'u-chart-bg' }));
    if (n) svg.append(s('rect', { x, y, width: bw, height: bh, rx: 8, fill: GRADE_COLORS[g], 'data-testid': `bar-${g}` }));
    svg.append(s('text', { x: x + bw / 2, y: n ? Math.max(14, y - 6) : 106, 'text-anchor': 'middle', class: 'u-chart-n', 'data-testid': `grade-${g}` }, String(n)));
    svg.append(s('text', { x: x + bw / 2, y: 132, 'text-anchor': 'middle', class: 'u-chart-l' }, String(g)));
  });
  return svg;
}

export function pctBar(p, kind = '') {
  const svg = s('svg', { class: `u-bar ${kind}`, viewBox: '0 0 100 8', preserveAspectRatio: 'none', 'aria-hidden': 'true' });
  svg.append(s('rect', { x: 0, y: 0, width: 100, height: 8, rx: 4, class: 'u-bar-bg' }));
  if (p > 0) svg.append(s('rect', { x: 0, y: 0, width: Math.max(2, Math.min(100, p)), height: 8, rx: 4, class: 'u-bar-fg' }));
  return svg;
}
