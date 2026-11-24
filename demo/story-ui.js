// What the story "does with its fingers": taps on the bot's buttons (and on a button that opens the Mini App), a file
// sent from the chat, and taps and typing inside the real Mini App.
export function makeUi({ phones, apps, bots, backend, wait }) {
  async function until(root, sel, ms = 8000) {
    for (let i = 0; i < ms / 50; i++) {
      const all = root.querySelectorAll(sel);
      const el = all[all.length - 1];
      if (el && !el.disabled) return el;
      await wait(50);
    }
    throw new Error(`demo: ${sel} did not appear`);
  }
  /** Scroll only the given box (never the page) so `el` is in view. */
  function reveal(box, el, gap = 12) {
    const r = el.getBoundingClientRect();
    const b = box.getBoundingClientRect();
    if (r.top < b.top + gap || r.bottom > b.bottom - gap) box.scrollTo({ top: box.scrollTop + r.top - b.top - gap * 4, behavior: 'smooth' });
  }
  const appBody = (uid) => phones[uid].appRoot.querySelector('.u-body') ?? phones[uid].appRoot;

  /** Show the press, then click whatever element matches now (a live refresh may have redrawn the screen meanwhile). */
  async function press(box, root, sel) {
    const el = await until(root, sel);
    reveal(box, el);
    await wait(260);
    el.classList.add('pressing');
    await wait(300);
    const now = await until(root, sel);
    now.classList.remove('pressing');
    now.click();
  }

  return {
    async botTap(uid, data) {
      const chat = phones[uid].chat;
      await press(chat, chat, `.kb-btn[data-cb="${CSS.escape(data)}"]`);
      await wait(300);
    },
    async botTapApp(uid, where) {
      const chat = phones[uid].chat;
      await press(chat, chat, `.kb-btn.app[data-app="${CSS.escape(where)}"]`);
      await wait(500);
    },
    async sendFile(uid, name, text) {
      const { input } = phones[uid];
      const before = input.placeholder;
      input.placeholder = `📎 ${name}`;
      await wait(700);
      input.placeholder = before;
      bots[uid].sendFile(name, text);
      await wait(400);
    },
    async appOpen(uid, route) {
      await apps[uid].ready;
      const cur = apps[uid].route;
      if (cur.view !== route.view || cur.id !== route.id) await apps[uid].open(route);
      else await apps[uid].refresh();
      await wait(350);
    },
    async appClick(uid, sel, after = 350) {
      await press(appBody(uid), phones[uid].appRoot, sel);
      await wait(after);
    },
    async appFill(uid, sel, value) {
      const el = await until(phones[uid].appRoot, sel);
      reveal(appBody(uid), el);
      el.focus();
      el.value = '';
      for (const ch of value) {
        el.value += ch;
        await wait(70);
      }
      el.dispatchEvent(new Event('input', { bubbles: true }));
      await wait(250);
    },
    async scrollApp(uid, sel) {
      const target = async () => {
        const el = await until(phones[uid].appRoot, sel).catch(() => null);
        const body = appBody(uid);
        return el ? [body, Math.max(0, el.getBoundingClientRect().top - body.getBoundingClientRect().top + body.scrollTop - 50)] : [body, null];
      };
      const [body, top] = await target();
      if (top !== null) body.scrollTo({ top, behavior: 'smooth' });
      await wait(500);
      const [again, end] = await target(); // a live refresh may have redrawn the page meanwhile: land exactly
      if (end !== null && Math.abs(again.scrollTop - end) > 4) again.scrollTop = end;
    },
    async attempt(uid) {
      for (let i = 0; i < 160; i++) {
        const a = backend.attempts.find((x) => x.user === uid && x.submitted_at === null);
        if (a && phones[uid].appRoot.querySelector('[data-testid=solving]')) return backend.attemptView(uid, a.id);
        await wait(50);
      }
      throw new Error('demo: the attempt did not start');
    },
  };
}
