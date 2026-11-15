const API_BASE = import.meta.env.VITE_API_BASE || ""
const apiFetch = (url, opts) => fetch(API_BASE + url, opts)

const TOKEN_KEY = 'mltestlab_token'
export const getToken = () => {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export const setToken = (t) => {
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch {}
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

const headers = (extra = {}) => {
  const t = getToken()
  return { ...(t ? { Authorization: `Bearer ${t}` } : {}), ...extra }
}

async function j(res) {
  if (!res.ok) {
    let msg = 'Request failed'
    try { msg = (await res.json()).detail || msg } catch {}
    if (res.status === 401 && getToken()) onUnauthorized()
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return res.json()
}

const get = (url) => apiFetch(url, { headers: headers() }).then(j)
const send = (method, url, body) =>
  apiFetch(url, { method, headers: headers({ 'Content-Type': 'application/json' }), body: body ? JSON.stringify(body) : undefined }).then(j)

export const api = {
  // auth
  signup: (b) => send('POST', '/api/auth/signup', b),
  login: (b) => send('POST', '/api/auth/login', b),
  me: () => get('/api/auth/me'),
  logout: () => send('POST', '/api/auth/logout'),
  // data
  stats: () => get('/api/stats'),
  models: () => get('/api/models'),
  catalog: () => get('/api/test-catalog'),
  datasets: () => get('/api/datasets'),
  preview: (id) => get(`/api/datasets/${encodeURIComponent(id)}/preview`),
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiFetch('/api/datasets', { method: 'POST', headers: headers(), body: fd }).then(j)
  },
  downloadDataset: async (id, name) => {
    const res = await apiFetch(`/api/datasets/${encodeURIComponent(id)}/download`, { headers: headers() })
    if (!res.ok) throw new Error('Could not download the dataset')
    const a = document.createElement('a')
    a.href = URL.createObjectURL(await res.blob())
    a.download = `${(name || 'dataset').toLowerCase().replace(/[^a-z0-9]+/g, '_')}.csv`
    a.click()
  },
  deleteDataset: (id) => send('DELETE', `/api/datasets/${id}`),
  runs: () => get('/api/runs'),
  run: (id) => get(`/api/runs/${id}`),
  createRun: (body) => send('POST', '/api/runs', body),
  deleteRun: (id) => send('DELETE', `/api/runs/${id}`),
  autofix: (id) => send('POST', `/api/runs/${id}/autofix`, {}),
  monitor: (id) => get(`/api/runs/${id}/monitor`),
  simulate: (id, body) => send('POST', `/api/runs/${id}/simulate`, body),
  clearMonitor: (id) => send('DELETE', `/api/runs/${id}/monitor`),
  batch: (body) => send('POST', '/api/batch', body),
  schema: (id) => get(`/api/runs/${id}/schema`),
  predict: (id, values) => send('POST', `/api/runs/${id}/predict`, { values }),
  exportModel: async (id) => {
    const res = await apiFetch(`/api/runs/${id}/export`, { headers: headers() })
    if (!res.ok) throw new Error('Could not export the model')
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `model-run${id}.pkl`
    a.click()
  },
}
