// The 800x500 portfolio thumbnail, drawn on a canvas in the page from two phone screenshots: Jasur's result with his
// mistakes and Nodira ustoz's analysis of wrong answers. Every frame stays fully inside with a margin. Used by
// scripts/shots.mjs.
export async function thumb(page, jasur, nodira) {
  return page.evaluate(async ([a, b]) => {
    const load = async (s) => { const i = new Image(); i.src = `data:image/png;base64,${s}`; await i.decode(); return i; };
    const [ph1, ph2] = await Promise.all([a, b].map(load));
    const cv = document.createElement('canvas');
    cv.width = 1600;
    cv.height = 1000;
    const g = cv.getContext('2d');
    const bg = g.createLinearGradient(0, 0, 1600, 1000);
    bg.addColorStop(0, '#22437a');
    bg.addColorStop(0.55, '#14284d');
    bg.addColorStop(1, '#0b1630');
    g.fillStyle = bg;
    g.fillRect(0, 0, 1600, 1000);
    const glow = g.createRadialGradient(1180, 520, 40, 1180, 520, 620);
    glow.addColorStop(0, 'rgba(242,177,52,0.22)');
    glow.addColorStop(1, 'rgba(242,177,52,0)');
    g.fillStyle = glow;
    g.fillRect(0, 0, 1600, 1000);
    // a row of answer cells under the title: right, right, wrong, right ...
    [1, 1, 0, 1, 1, 0, 1, 1, 1, 0].forEach((ok, i) => {
      g.fillStyle = ok ? 'rgba(31,157,107,0.9)' : 'rgba(217,83,79,0.9)';
      g.beginPath();
      g.roundRect(86 + i * 46, 846, 36, 36, 9);
      g.fill();
    });
    const F = '-apple-system, Segoe UI, Roboto, sans-serif';
    g.fillStyle = '#f2b134';
    g.font = `700 22px ${F}`;
    g.fillText('T E L E G R A M   B O T   +   M I N I   A P P', 82, 150);
    g.fillStyle = '#ffffff';
    g.font = `800 104px ${F}`;
    g.fillText('Test', 74, 268);
    g.fillText('Ustasi', 74, 376);
    ['Matndan test — iqtibos bilan', 'Telefonda yechish, vaqt nazorati', 'Xatolar tahlili va qayta test'].forEach((t, i) => {
      g.fillStyle = ['#f2b134', '#7fd6b2', '#ff9c7a'][i];
      g.beginPath();
      g.arc(92, 458 + i * 60, 8, 0, 7);
      g.fill();
      g.fillStyle = '#eef2fb';
      g.font = `500 30px ${F}`;
      g.fillText(t, 118, 470 + i * 60);
    });
    g.fillStyle = 'rgba(242,177,52,0.9)';
    g.font = `600 25px ${F}`;
    g.fillText('xoliddev', 82, 690);
    const place = (img, x, y, h) => {
      const w = (img.width * h) / img.height;
      g.save();
      g.shadowColor = 'rgba(0,0,0,0.6)';
      g.shadowBlur = 50;
      g.shadowOffsetY = 24;
      g.drawImage(img, x, y, w, h);
      g.restore();
      return w;
    };
    const H = 840;
    const w2 = (ph2.width * H) / ph2.height;
    const w1 = (ph1.width * (H - 60)) / ph1.height;
    place(ph1, 1600 - 60 - w2 - w1 + 30, 110, H - 60);
    place(ph2, 1600 - 60 - w2, 80, H);
    const o = document.createElement('canvas');
    o.width = 800;
    o.height = 500;
    const og = o.getContext('2d');
    og.imageSmoothingQuality = 'high';
    og.drawImage(cv, 0, 0, 800, 500);
    return o.toDataURL('image/jpeg', 0.9).split(',')[1];
  }, [jasur.toString("base64"), nodira.toString("base64")]);
}
