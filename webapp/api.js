// The Mini App's API over HTTP: every call carries Telegram's signed initData (checked on the server). The browser
// demo passes an object with the same method names answered by its in-page backend (demo/api.js).
export function httpApi(initData, base = '/api') {
  async function call(method, path, body) {
    const res = await fetch(`${base}${path}`, {
      method,
      headers: { Authorization: `tma ${initData}`, ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || 'generic'), { code: data.error || 'generic' });
    return data;
  }
  const get = (p) => call('GET', p);
  const post = (p, b) => call('POST', p, b ?? {});
  return {
    me: () => get('/me'),
    setLang: (lang) => post('/lang', { lang }),
    tests: () => get('/tests'),
    draft: (data) => post('/drafts', data),
    test: (id) => get(`/tests/${id}`),
    settings: (id, data) => post(`/tests/${id}/settings`, data),
    publish: (id) => post(`/tests/${id}/publish`),
    edit: (id, qid, data) => post(`/tests/${id}/questions/${qid}`, data),
    remove: (id, qid) => post(`/tests/${id}/questions/${qid}/delete`),
    regen: (id, qid) => post(`/tests/${id}/questions/${qid}/regen`),
    move: (id, qid, step) => post(`/tests/${id}/questions/${qid}/move`, { step }),
    results: (id) => get(`/tests/${id}/results`),
    analysis: (id) => get(`/tests/${id}/analysis`),
    csv: (id) => get(`/tests/${id}/csv`),
    retest: (id) => post(`/tests/${id}/retest`),
    classes: () => get('/classes'),
    addClass: (name) => post('/classes', { name }),
    klass: (id) => get(`/classes/${id}`),
    invite: (id) => post(`/classes/${id}/invite`),
    start: (id) => post(`/tests/${id}/start`),
    attempt: (id) => get(`/attempts/${id}`),
    answer: (id, pos, choice) => post(`/attempts/${id}/answer`, { pos, choice }),
    submit: (id) => post(`/attempts/${id}/submit`),
    result: (id) => get(`/tests/${id}/result`),
  };
}
