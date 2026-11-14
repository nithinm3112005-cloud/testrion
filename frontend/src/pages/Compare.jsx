import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, GitCompare } from 'lucide-react'
import { api } from '../api.js'
import { Empty, Loading, MODEL_LABELS, Page, ScoreRing, StatusBadge } from '../components/ui.jsx'

export default function Compare() {
  const [params, setParams] = useSearchParams()
  const nav = useNavigate()
  const [runs, setRuns] = useState(null)
  const [A, setA] = useState(null)
  const [B, setB] = useState(null)
  const a = params.get('a') || ''
  const b = params.get('b') || ''

  useEffect(() => { api.runs().then(setRuns) }, [])
  useEffect(() => { setA(null); if (a) api.run(a).then(setA).catch(() => {}) }, [a])
  useEffect(() => { setB(null); if (b) api.run(b).then(setB).catch(() => {}) }, [b])

  if (!runs) return <Loading />
  const set = (k, v) => setParams({ a, b, [k]: v })
  const Pick = ({ k, val }) => (
    <select className="select" value={val} onChange={(e) => set(k, e.target.value)}>
      <option value="">Select a run…</option>
      {runs.map((r) => <option key={r.id} value={r.id}>#{r.id} · {r.dataset_name} · {MODEL_LABELS[r.model] || r.model} · {r.score}</option>)}
    </select>
  )

  const both = A && B
  const bById = both ? Object.fromEntries(B.result.tests.map((t) => [t.id, t])) : {}
  const gain = both ? B.score - A.score : 0
  const bothReg = both && A.result.metrics.task === 'regression' && B.result.metrics.task === 'regression'
  const bothClf = both && A.result.metrics.task !== 'regression' && B.result.metrics.task !== 'regression'

  return (
    <Page title="Compare runs" sub="Put two test runs side by side to see exactly what changed">
      <div className="grid g2">
        <div><div className="muted" style={{ marginBottom: 6, fontWeight: 600 }}>Run A (baseline)</div><Pick k="a" val={a} /></div>
        <div><div className="muted" style={{ marginBottom: 6, fontWeight: 600 }}>Run B (comparison)</div><Pick k="b" val={b} /></div>
      </div>

      {runs.length < 2 && (
        <div className="card mt-lg"><Empty icon={GitCompare} title="You need at least two runs" text="Run a test and an auto-fix (or two different models) to compare them." /></div>
      )}

      {both && (
        <>
          <div className="card card-pad mt-lg">
            <div className="grid" style={{ gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: 30 }}>
              {[A, B].map((r, i) => (
                <div key={r.id} className="row" style={{ gap: 20, justifyContent: i ? 'flex-start' : 'flex-end', cursor: 'pointer' }} onClick={() => nav(`/app/runs/${r.id}`)}>
                  {i === 0 && <div style={{ textAlign: 'right' }}><b>#{r.id} · {r.dataset_name}</b><div className="muted">{MODEL_LABELS[r.model]}</div></div>}
                  <ScoreRing score={r.score} grade={r.result.summary.grade} size={120} stroke={11} />
                  {i === 1 && <div><b>#{r.id} · {r.dataset_name}</b><div className="muted">{MODEL_LABELS[r.model]}</div></div>}
                </div>
              ))}
            </div>
            <div style={{ textAlign: 'center', marginTop: 14 }}>
              <span className={`badge ${gain > 0 ? 'pass' : gain < 0 ? 'fail' : 'gray'}`} style={{ fontSize: 13, padding: '5px 14px' }}>
                {gain > 0 ? '▲' : gain < 0 ? '▼' : '='} {Math.abs(gain).toFixed(1)} points {gain > 0 ? 'better' : gain < 0 ? 'worse' : 'difference'}
              </span>
            </div>
          </div>

          <div className="grid g2 mt">
            <div className="card card-pad">
              <div className="card-title" style={{ marginBottom: 14 }}>Key metrics</div>
              <table className="table"><thead><tr><th>Metric</th><th>A</th><th>B</th><th>Δ</th></tr></thead><tbody>
                {(bothReg
                  ? [['R² (accuracy)', 'r2', 'pct'], ['Cross-val R²', 'cv_mean', 'pct'], ['Train R²', 'train_r2', 'pct'], ['RMSE', 'rmse', 'num', true], ['MAE', 'mae', 'num', true], ['Mean abs. % error', 'mape', 'pct', true]]
                  : bothClf
                    ? [['Macro F1', 'f1', 'pct'], ['Accuracy', 'accuracy', 'pct'], ['Cross-val F1', 'cv_mean', 'pct'], ['Train F1', 'train_f1', 'pct']]
                    : [['Accuracy / R²', 'accuracy', 'pct'], ['Cross-validation score', 'cv_mean', 'pct']]
                ).map(([l, k, kind, lower]) => {
                  const va = A.result.metrics[k], vb = B.result.metrics[k]
                  const d = vb - va
                  const good = lower ? d <= 0 : d >= 0
                  const f = (v) => (kind === 'pct' ? `${(v * 100).toFixed(1)}%` : Number(v).toFixed(2))
                  return (<tr key={k}><td>{l}</td><td>{f(va)}</td><td>{f(vb)}</td>
                    <td style={{ color: good ? 'var(--pass)' : 'var(--fail)', fontWeight: 700 }}>{d >= 0 ? '+' : ''}{kind === 'pct' ? (d * 100).toFixed(1) : d.toFixed(2)}</td></tr>)
                })}
              </tbody></table>
            </div>
            <div className="card card-pad">
              <div className="card-title" style={{ marginBottom: 14 }}>Category scores</div>
              {A.result.summary.categories.map((c) => {
                const o = B.result.summary.categories.find((x) => x.name === c.name)
                const d = o ? o.score - c.score : 0
                return (<div key={c.name} className="row" style={{ padding: '9px 0', borderBottom: '1px dashed var(--border)' }}>
                  <b style={{ flex: 1 }}>{c.name}</b><span className="muted">{Math.round(c.score)}</span><ArrowRight size={14} color="#8b8988" />
                  <b>{o ? Math.round(o.score) : '—'}</b>
                  <span style={{ width: 54, textAlign: 'right', fontWeight: 700, color: d >= 0 ? 'var(--pass)' : 'var(--fail)' }}>{d >= 0 ? '+' : ''}{Math.round(d)}</span>
                </div>)
              })}
            </div>
          </div>

          <div className="card mt table-wrap">
            <table className="table">
              <thead><tr><th>Test</th><th>Category</th><th>Run A</th><th>Run B</th></tr></thead>
              <tbody>
                {A.result.tests.map((t) => {
                  const o = bById[t.id]
                  const changed = o && o.status !== t.status
                  return (<tr key={t.id} style={changed ? { background: 'rgba(147,18,255,0.06)' } : {}}>
                    <td><b>{t.name}</b></td><td className="muted">{t.category}</td>
                    <td><StatusBadge status={t.status} /> <span className="muted" style={{ marginLeft: 6 }}>{t.value}</span></td>
                    <td>{o ? <><StatusBadge status={o.status} /> <span className="muted" style={{ marginLeft: 6 }}>{o.value}</span></> : '—'}</td>
                  </tr>)
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Page>
  )
}
