// JS port of testustasi/core/table.py: the results table as an Excel-friendly CSV (UTF-8 BOM, ";", CRLF, quoted
// fields, no formula-looking cells).
export const BOM = '\ufeff';

export const mmss = (seconds) => (seconds === null || seconds === undefined ? '' : `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`);

export function cell(value) {
  let s = value === null || value === undefined ? '' : String(value);
  if (['=', '+', '-', '@', '\t', '\r'].includes(s.slice(0, 1))) s = `'${s}`;
  if (/[;"\n\r]/.test(s)) s = `"${s.replaceAll('"', '""')}"`;
  return s;
}

export function csvText(labels, rows, marks, total, stamp) {
  const head = [labels.no, labels.name, labels.score, labels.pct, labels.grade, labels.time, labels.status, labels.at];
  for (let i = 1; i <= total; i++) head.push(String(i));
  const lines = [head.map(cell).join(';')];
  rows.forEach((r, i) => {
    const done = r.status === 'done';
    const row = [i + 1, r.name, done ? r.score : '', done ? r.pct : '', done ? r.grade : '', done ? mmss(r.seconds) : '', labels[`st_${r.status}`],
      done && r.at ? stamp(r.at) : ''];
    if (done) for (const m of marks[r.user] ?? Array(total).fill(null)) row.push(m === null || m === undefined ? '' : m);
    else for (let k = 0; k < total; k++) row.push('');
    lines.push(row.map(cell).join(';'));
  });
  return `${BOM}${lines.join('\r\n')}\r\n`;
}
