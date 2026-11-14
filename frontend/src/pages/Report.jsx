import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  Activity, ArrowRight, ChevronDown, Download, Lightbulb, Loader2, PackageOpen, Printer, ShieldAlert, ShieldCheck, Sparkles, Trash2, Wand2,
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api.js'
import {
  Empty, Loading, MODEL_LABELS, Page, ScoreRing, STATUS, StatusBadge, fmtDate, scoreColor,
} from '../components/ui.jsx'

const CATS = ['Data Quality', 'Model Performance', 'Robustness', 'Reliability', 'Fairness & Slices']

export default function Report() {
  const { id } = useParams()
  const nav = useNavigate()
  const [run, setRun] = useState(null)
  const [tab, setTab] = useState(() => new URLSearchParams(window.location.search).get('tab') || 'tests')
  const [fixing, setFixing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setRun(null)
    api.run(id).then(setRun).catch((e) => setError(e.message))
  }, [id])

  if (error) return <Page title="Run not found"><div className="error-box">{error}</div></Page>
  if (!run) return <Loading text="Loading report…" />

  const res = run.result
  const sum = res.summary
  const fix = res.fix
  const issues = sum.warned + sum.failed

  const autofix = async () => {
    setFixing(true)
    try {
      const r = await api.autofix(run.id)
      nav(`/app/runs/${r.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setFixing(false)
    }
  }
  const remove = async () => {
    if (!confirm('Delete this run?')) return
    await api.deleteRun(run.id)
    nav('/app/history')
  }
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(run, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `testrion-run-${run.id}.json`
    a.click()
  }

  return (
    <Page
      crumbs={<div className="crumbs no-print"><Link to="/app/history">Test history</Link> / Run #{run.id}</div>}
      title={`${run.dataset_name}`}
      sub={
        <span className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <span className="badge gray">Run #{run.id}</span>
          <span className="badge gray">{MODEL_LABELS[run.model] || run.model}</span>
          <span className="badge gray">target: {run.target}</span>
          {run.kind === 'autofix' && <span className="badge brand"><Wand2 size={12} /> Auto-fixed</span>}
          <span>{fmtDate(run.created_at)} · {res.duration_sec}s</span>
        </span>
      }
      actions={
        <>
          {run.kind === 'test' && issues > 0 && (
            <button className="btn btn-magic btn-lg" onClick={autofix} disabled={fixing}>
              {fixing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Wand2 size={16} />}
              {fixing ? 'Fixing problems…' : `Auto-fix ${issues} issue${issues > 1 ? 's' : ''}`}
            </button>
          )}
          <button className="btn" onClick={() => api.exportModel(run.id).catch((e) => setError(e.message))} title="Download the trained model (.joblib)"><PackageOpen size={15} /> Model</button>
          <button className="btn" onClick={exportJson}><Download size={15} /> JSON</button>
          <button className="btn" onClick={() => window.print()}><Printer size={15} /> Print</button>
          <button className="btn btn-danger" onClick={remove}><Trash2 size={15} /></button>
        </>
      }
    >
      {fixing && (
        <div className="overlay">
          <div className="modal" style={{ textAlign: 'center' }}>
            <div className="spinner" />
            <h3>Diagnosing & fixing…</h3>
            <div className="muted">Repairing data, tuning hyper-parameters, searching better models and re-running all tests.</div>
          </div>
        </div>
      )}

      <GateBanner gate={sum.gate} />
      {fix && <div className="mt"><FixPanel fix={fix} run={run} sum={sum} /></div>}

      <div className="grid mt" style={{ gridTemplateColumns: '300px 1fr 1fr' }}>
        <div className="card card-pad" style={{ display: 'grid', placeItems: 'center', textAlign: 'center', gap: 12 }}>
          <ScoreRing score={sum.score} grade={sum.grade} size={170} stroke={14} />
          <div>
            <div style={{ fontWeight: 700 }}>{sum.verdict}</div>
            <div className="muted" style={{ fontSize: 12.5 }}>Overall quality score</div>
          </div>
        </div>

        <div className="card card-pad">
          <div className="card-title" style={{ marginBottom: 16 }}>Test outcomes</div>
          <div className="grid g2" style={{ gap: 12 }}>
            {[['pass', sum.passed], ['warn', sum.warned], ['fail', sum.failed], ['skip', sum.skipped]].map(([k, n]) => (
              <div key={k} className="row" style={{ padding: 12, borderRadius: 12, background: `var(--${k}-bg)` }}>
                {(() => { const I = STATUS[k].Icon; return <I size={22} color={STATUS[k].color} /> })()}
                <div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: STATUS[k].color, lineHeight: 1 }}>{n}</div>
                  <div style={{ fontSize: 12, color: STATUS[k].color, fontWeight: 600 }}>{STATUS[k].label}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="muted" style={{ marginTop: 14, fontSize: 12.5 }}>{sum.total} tests executed on {res.profile.usable_rows.toLocaleString()} usable rows in {res.duration_sec}s ({Math.round(res.profile.usable_rows / Math.max(res.duration_sec, 0.01)).toLocaleString()} rows/s).</div>
        </div>

        <div className="card card-pad">
          <div className="card-title" style={{ marginBottom: 16 }}>Score by category</div>
          <div className="grid" style={{ gap: 15 }}>
            {sum.categories.map((c) => (
              <div key={c.name}>
                <div className="row" style={{ marginBottom: 6 }}>
                  <b style={{ fontSize: 13 }}>{c.name}</b>
                  <div className="spacer" />
                  <span className="muted" style={{ fontSize: 12 }}>{c.passed}/{c.total} passed</span>
                  <b style={{ color: scoreColor(c.score), width: 38, textAlign: 'right' }}>{Math.round(c.score)}</b>
                </div>
                <div className="bar"><i style={{ width: `${c.score}%`, background: scoreColor(c.score) }} /></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-lg no-print">
        <div className="tabs">
          {[['tests', 'Test results'], ['perf', 'Model performance'], ['data', 'Data profile'], ['play', 'Try the model'], ['monitor', 'Live monitoring'], ['config', 'Configuration']].map(([k, l]) => (
            <button key={k} className={`tab ${tab === k ? 'active' : ''}`} onClick={() => setTab(k)}>{l}</button>
          ))}
        </div>
      </div>

      <div className="mt">
        {tab === 'tests' && <Tests tests={res.tests} />}
        {tab === 'perf' && <Performance m={res.metrics} />}
        {tab === 'data' && <DataProfile p={res.profile} />}
        {tab === 'play' && <Playground run={run} />}
        {tab === 'monitor' && <Monitoring run={run} />}
        {tab === 'config' && <Config res={res} run={run} />}
      </div>
    </Page>
  )
}

/* ------------------------------ fix panel ------------------------------ */
function FixPanel({ fix, run, sum }) {
  const gain = sum.score - fix.original_score
  const changed = fix.comparison.filter((c) => c.before !== c.after)
  return (
    <div className="card card-pad" style={{ borderColor: 'rgba(147,18,255,0.45)', background: 'linear-gradient(180deg, rgba(147,18,255,0.14), rgba(147,18,255,0.02) 60%)' }}>
      <div className="row" style={{ marginBottom: 18 }}>
        <Sparkles size={20} color="#b24bff" />
        <div>
          <div className="card-title">Auto-fix report</div>
          <div className="card-sub">
            Problems were diagnosed, repaired and every test was re-run ·{' '}
            <Link to={`/app/runs/${fix.parent_run_id}`} style={{ color: 'var(--brand)', fontWeight: 600 }}>view original run #{fix.parent_run_id}</Link>
          </div>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'auto 1.3fr 1fr', gap: 34, alignItems: 'start' }}>
        <div className="delta" style={{ position: 'sticky', top: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <ScoreRing score={fix.original_score} size={104} stroke={9} grade={fix.original_grade} />
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>Before</div>
          </div>
          <ArrowRight className="delta-arrow" />
          <div style={{ textAlign: 'center' }}>
            <ScoreRing score={sum.score} size={104} stroke={9} grade={sum.grade} />
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--pass)', fontWeight: 700 }}>After {gain >= 0 ? '+' : ''}{gain.toFixed(1)}</div>
          </div>
        </div>

        <div>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>What was fixed</div>
          <div className="timeline">
            {fix.steps.length === 0 && <div className="muted">No changes were necessary or beneficial.</div>}
            {fix.steps.map((s, i) => (
              <div key={i} className="tl-item">
                <div className="tl-dot">{i + 1}</div>
                <div>
                  <div className="tl-title">{s.title}</div>
                  <div className="tl-why">{s.why}</div>
                  <span className="tl-change">{s.change}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Tests that changed ({changed.length})</div>
          <div style={{ maxHeight: 290, overflow: 'auto', border: '1px solid var(--border)', borderRadius: 12, background: 'transparent' }}>
            <table className="table" style={{ fontSize: 13 }}>
              <tbody>
                {changed.map((c) => (
                  <tr key={c.id}>
                    <td style={{ padding: '9px 12px' }}>{c.name}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <span className="shift"><StatusBadge status={c.before} /> <ArrowRight size={13} color="#8b8988" /> <StatusBadge status={c.after} /></span>
                    </td>
                  </tr>
                ))}
                {changed.length === 0 && <tr><td className="muted" style={{ padding: 16 }}>No test status changed.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {run.model !== fix.original_model && (
        <div className="callout fix" style={{ marginTop: 16 }}>
          The model was switched from <b>{MODEL_LABELS[fix.original_model]}</b> to <b>{MODEL_LABELS[run.model]}</b> after a cross-validated model search.
        </div>
      )}
    </div>
  )
}

/* ------------------------------ test list ------------------------------ */
function Tests({ tests }) {
  const [filter, setFilter] = useState('all')
  const [open, setOpen] = useState({})
  const counts = useMemo(() => {
    const c = { all: tests.length, fail: 0, warn: 0, pass: 0, skip: 0 }
    tests.forEach((t) => c[t.status]++)
    return c
  }, [tests])
  const shown = tests.filter((t) => filter === 'all' || t.status === filter)
  return (
    <>
      <div className="chips" style={{ marginBottom: 16 }}>
        {[['all', 'All'], ['fail', 'Failed'], ['warn', 'Warnings'], ['pass', 'Passed'], ['skip', 'Skipped']].filter(([k]) => counts[k] > 0 || k === 'all').map(([k, l]) => (
          <button key={k} className={`chip ${filter === k ? 'active' : ''}`} onClick={() => setFilter(k)}>{l} · {counts[k]}</button>
        ))}
      </div>
      <div className="grid" style={{ gap: 18 }}>
        {CATS.map((cat) => {
          const list = shown.filter((t) => t.category === cat)
          if (!list.length) return null
          return (
            <div key={cat} className="card">
              <div className="cat-head">
                <div className="cat-name">{cat}</div>
                <span className="badge gray">{list.length} tests</span>
              </div>
              {list.map((t) => {
                const S = STATUS[t.status]
                const isOpen = open[t.id]
                return (
                  <div key={t.id} className="test">
                    <div className="test-main" onClick={() => setOpen({ ...open, [t.id]: !isOpen })}>
                      <div className={`test-icon ${t.status}`}><S.Icon size={18} /></div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="test-name">{t.name}</div>
                        <div className="test-desc">{t.description}</div>
                      </div>
                      <div className="test-val"><b style={{ color: S.color }}>{t.value}</b><span>target: {t.threshold}</span></div>
                      <StatusBadge status={t.status} />
                      <ChevronDown size={18} className={`chev ${isOpen ? 'open' : ''}`} />
                    </div>
                    {isOpen && (
                      <div className="test-body">
                        <div className="callout info"><b>Finding · </b>{t.details}</div>
                        {t.fix && <div className="callout fix"><Lightbulb size={14} style={{ verticalAlign: -2 }} /> <b>Recommended fix · </b>{t.fix}</div>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </>
  )
}

/* ------------------------------ performance ------------------------------ */
function Performance({ m }) {
  return m.task === 'regression' ? <RegPerformance m={m} /> : <ClfPerformance m={m} />
}

function ClfPerformance({ m }) {
  const pc = m.per_class.map((c) => ({ name: c.class, Precision: +c.precision.toFixed(3), Recall: +c.recall.toFixed(3), F1: +c.f1.toFixed(3) }))
  const maxCm = Math.max(...m.confusion_matrix.flat(), 1)
  const n = m.classes.length
  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="grid g4">
        {[['Accuracy', m.accuracy], ['Macro precision', m.precision], ['Macro recall', m.recall], ['Macro F1', m.f1]].map(([l, v]) => (
          <div key={l} className="card metric">
            <div className="metric-label">{l}</div>
            <div className="metric-value" style={{ color: scoreColor(v * 100) }}>{(v * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
      <DetailedMetrics m={m} />
      <div className="grid g2">
        <div className="card card-pad">
          <div className="card-title">Per-class performance</div>
          <div style={{ height: 290, marginTop: 14 }}>
            <ResponsiveContainer>
              <BarChart data={pc} margin={{ left: -10 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Legend iconType="circle" />
                <Bar isAnimationActive={false} dataKey="Precision" fill="#d2a8ff" radius={[5, 5, 0, 0]} />
                <Bar isAnimationActive={false} dataKey="Recall" fill="#a855f7" radius={[5, 5, 0, 0]} />
                <Bar isAnimationActive={false} dataKey="F1" fill="#5b21b6" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card card-pad">
          <div className="card-title">Confusion matrix</div>
          <div className="card-sub" style={{ marginBottom: 14 }}>Rows = actual class · columns = predicted class</div>
          <div className="cm" style={{ gridTemplateColumns: `70px repeat(${n}, 1fr)` }}>
            <div />
            {m.classes.map((c) => <div key={c} className="cm-label" title={c}>{c}</div>)}
            {m.confusion_matrix.map((row, i) => (
              <Fragment key={`r${i}`}>
                <div className="cm-label" title={m.classes[i]}>{m.classes[i]}</div>
                {row.map((v, j) => (
                  <div key={`${i}-${j}`} className="cm-cell"
                    style={{
                      background: i === j ? `rgba(22,163,74,${0.12 + 0.75 * v / maxCm})` : v ? `rgba(220,38,38,${0.1 + 0.6 * v / maxCm})` : 'rgba(255,255,255,0.04)',
                      color: v / maxCm > 0.55 ? '#fff' : '#f7f7f8',
                    }}>{v}</div>
                ))}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
      <div className="grid g2">
        <div className="card card-pad">
          <div className="card-title">Feature importance</div>
          <div className="card-sub">Permutation importance — drop in F1 when a feature is shuffled</div>
          <div style={{ height: 300, marginTop: 10 }}>
            {m.feature_importance.length ? (
              <ResponsiveContainer>
                <BarChart data={m.feature_importance} layout="vertical" margin={{ left: 30, right: 20 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="feature" width={130} tick={{ fontSize: 11.5 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => v.toFixed(4)} />
                  <Bar isAnimationActive={false} dataKey="importance" radius={[0, 6, 6, 0]}>
                    {m.feature_importance.map((_, i) => <Cell key={i} fill={i === 0 ? '#9312ff' : '#d2a8ff'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="muted">Not available.</div>}
          </div>
        </div>
        <div className="card card-pad">
          <div className="card-title">Generalisation</div>
          <div className="card-sub" style={{ marginBottom: 16 }}>Train vs test vs cross-validated macro F1</div>
          {[['Training F1', m.train_f1], ['Test F1', m.f1], ['Cross-validation F1', m.cv_mean]].map(([l, v]) => (
            <div key={l} style={{ marginBottom: 16 }}>
              <div className="row" style={{ marginBottom: 6 }}>
                <b style={{ fontSize: 13 }}>{l}</b><div className="spacer" />
                <b>{(v * 100).toFixed(1)}%{l.startsWith('Cross') && <span className="muted" style={{ fontWeight: 500 }}> ± {(m.cv_std * 100).toFixed(1)}</span>}</b>
              </div>
              <div className="bar"><i style={{ width: `${v * 100}%`, background: '#a855f7' }} /></div>
            </div>
          ))}
          <div className="callout info" style={{ marginTop: 20 }}>Model trained in {m.fit_time.toFixed(2)}s.</div>
        </div>
      </div>
      <SlicesCard rows={m.slices} task="classification" />
    </div>
  )
}

/* ------------------------------ data profile ------------------------------ */
function DataProfile({ p }) {
  if (p.target_stats) return <RegProfile p={p} />
  const colors = ['#9312ff', '#06b6d4', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#ec4899']
  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="grid g4">
        {[['Rows', p.rows.toLocaleString()], ['Usable rows', p.usable_rows.toLocaleString()], ['Features', `${p.features} (${p.numeric_features} num · ${p.categorical_features} cat)`], ['Missing cells', `${(p.missing_pct * 100).toFixed(1)}%`]].map(([l, v]) => (
          <div key={l} className="card metric"><div className="metric-label">{l}</div><div className="metric-value" style={{ fontSize: 22 }}>{v}</div></div>
        ))}
      </div>
      <div className="card card-pad">
        <div className="card-title">Class distribution</div>
        <div style={{ height: 260, marginTop: 14 }}>
          <ResponsiveContainer>
            <BarChart data={p.class_distribution} margin={{ left: -10 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
              <XAxis dataKey="class" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar isAnimationActive={false} dataKey="count" radius={[6, 6, 0, 0]}>
                {p.class_distribution.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      {p.notes.length > 0 && <div className="callout info">{p.notes.join(' · ')}</div>}
    </div>
  )
}

/* ------------------------------ configuration ------------------------------ */
function Config({ res, run }) {
  const c = res.config
  const rows = [
    ['Model', MODEL_LABELS[c.model] || c.model],
    ['Target column', c.target],
    ['Imputation', c.impute ? 'Median / most-frequent' : 'Off (rows with gaps dropped)'],
    ['Scaling', { none: 'None', standard: 'Standardisation', robust: 'Robust (median / IQR)' }[c.scale]],
    ['Class balancing', c.balance ? { class_weight: 'Class weights', oversample: 'Random oversampling' }[c.balance] : 'None'],
    ['Remove duplicates', c.dedupe ? 'Yes' : 'No'],
    ['Drop constant columns', c.drop_constant ? 'Yes' : 'No'],
    ['Dropped columns', c.drop_columns.length ? c.drop_columns.join(', ') : '—'],
    ...(c.log_target ? [['Target transform', 'log(1 + y), predictions mapped back']] : []),
    ['Protected attributes (audited)', (c.protected && c.protected.length) ? c.protected.join(', ') : 'Auto-detected'],
    ['Hyper-parameters', Object.keys(c.params).length ? Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ') : 'Defaults'],
    ['Data split', '75% train / 25% hold-out test (seed 42). Validation = cross-validation inside the 75%; the test set is never used to fit, tune or select a model'],
  ]
  return (
    <div className="grid g2">
      <div className="card card-pad"><div className="card-title" style={{ marginBottom: 16 }}>Pipeline configuration</div>
        <dl className="kv">{rows.map(([k, v]) => <Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>)}</dl>
      </div>
      <div className="card card-pad"><div className="card-title" style={{ marginBottom: 16 }}>Raw config (JSON)</div>
        <pre className="json">{JSON.stringify(c, null, 2)}</pre>
      </div>
    </div>
  )
}

/* ------------------------------ playground ------------------------------ */
function Playground({ run }) {
  const [schema, setSchema] = useState(null)
  const [vals, setVals] = useState({})
  const [out, setOut] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setSchema(null)
    api.schema(run.id).then((s) => {
      setSchema(s)
      setVals(Object.fromEntries(s.features.map((f) => [f.name, f.type === 'numeric' ? String(+f.median.toFixed(3)) : f.default])))
    }).catch((e) => setErr(e.message))
  }, [run.id])

  const predict = async () => {
    setBusy(true); setErr('')
    try { setOut(await api.predict(run.id, vals)) } catch (e) { setErr(e.message); setOut(null) } finally { setBusy(false) }
  }

  if (err && !schema) return <div className="error-box">{err}</div>
  if (!schema) return <Loading text="Training the model on all data…" />
  return (
    <div className="grid" style={{ gridTemplateColumns: '1.5fr 1fr', gap: 18, alignItems: 'start' }}>
      <div className="card card-pad">
        <div className="card-title">Enter feature values</div>
        <div className="card-sub" style={{ marginBottom: 18 }}>Pre-filled with typical values — change them and press Predict.</div>
        <div className="grid g2" style={{ gap: 14 }}>
          {schema.features.map((f) => (
            <label key={f.name} className="field" style={{ margin: 0 }}>
              {f.name} <span className="muted" style={{ fontWeight: 400 }}>{f.type === 'numeric' ? `(${+f.min.toFixed(2)} – ${+f.max.toFixed(2)})` : ''}</span>
              {f.type === 'numeric' ? (
                <input className="input" type="number" step="any" value={vals[f.name] ?? ''} onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })} />
              ) : (
                <select className="select" value={vals[f.name] ?? ''} onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })}>
                  {f.options.map((o) => <option key={o}>{o}</option>)}
                </select>
              )}
            </label>
          ))}
        </div>
        <button className="btn btn-primary btn-lg mt-lg" onClick={predict} disabled={busy}>
          {busy ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Sparkles size={16} />} Predict
        </button>
      </div>
      <div className="card card-pad" style={{ position: 'sticky', top: 20 }}>
        <div className="card-title">Prediction for “{schema.target}”</div>
        {err && <div className="error-box" style={{ marginTop: 14 }}>{err}</div>}
        {!out && !err && <div className="muted" style={{ marginTop: 14 }}>The result will appear here.</div>}
        {out && (
          <>
            <div style={{ fontSize: 30, fontWeight: 800, margin: '14px 0 4px', color: 'var(--brand)' }}>{out.task === 'regression' ? Number(out.label).toLocaleString(undefined, { maximumFractionDigits: 2 }) : out.label}</div>
            {out.task === 'regression' ? <div className="muted">Estimated numeric value for “{schema.target}”.</div> : out.probabilities ? out.probabilities.slice().sort((x, y) => y.p - x.p).map((p) => (
              <div key={p.class} style={{ marginTop: 12 }}>
                <div className="row"><b style={{ fontSize: 13 }}>{p.class}</b><div className="spacer" /><b>{(p.p * 100).toFixed(1)}%</b></div>
                <div className="bar"><i style={{ width: `${p.p * 100}%`, background: p.class === out.label ? '#9312ff' : 'rgba(147,18,255,0.45)' }} /></div>
              </div>
            )) : <div className="muted">This model does not output probabilities.</div>}
          </>
        )}
      </div>
    </div>
  )
}

/* ------------------------------ deployment gate ------------------------------ */
function GateBanner({ gate }) {
  if (!gate) return null
  const ok = gate.status === 'APPROVED'
  const color = ok ? 'var(--pass)' : 'var(--fail)'
  return (
    <div className="card gate" style={{ borderColor: color, background: ok ? 'var(--pass-bg)' : 'var(--fail-bg)' }}>
      <div className="row" style={{ gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        {ok ? <ShieldCheck size={38} color={color} /> : <ShieldAlert size={38} color={color} />}
        <div style={{ minWidth: 220 }}>
          <div style={{ fontSize: 20, fontWeight: 800, color, letterSpacing: '-0.01em' }}>Deployment {ok ? 'approved' : 'blocked'}</div>
          <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Release gate: accuracy ≥ 85% (R² ≥ 0.85 for regression) and demographic parity difference &lt; 10%</div>
        </div>
        <div className="spacer" />
        <div className="gate-checks">
          {gate.checks.map((c) => (
            <span key={c.name} className={`gate-check ${c.passed === true ? 'ok' : c.passed === false ? 'bad' : 'na'}`}>
              <b>{c.passed === true ? '✓' : c.passed === false ? '✗' : '–'}</b> {c.name}: <b>{c.value}</b>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------ slices ------------------------------ */
function SlicesCard({ rows, task }) {
  if (!rows || !rows.length) return null
  const cols = [...new Set(rows.map((r) => r.column))]
  const reg = task === 'regression'
  return (
    <div className="card card-pad">
      <div className="card-title">Data-slice testing</div>
      <div className="card-sub" style={{ marginBottom: 14 }}>{reg ? 'Mean absolute % error per slice (lower is better)' : 'Accuracy per slice (higher is better)'} · protected attributes are marked</div>
      <div className="grid g2" style={{ gap: 18 }}>
        {cols.map((c) => {
          const rs = rows.filter((r) => r.column === c)
          const max = Math.max(...rs.map((r) => r.metric), 0.0001)
          return (
            <div key={c}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>{c} {rs[0].protected && <span className="badge brand" style={{ marginLeft: 6 }}>protected</span>}</div>
              {rs.map((r) => (
                <div key={r.group} className="row" style={{ gap: 10, marginBottom: 7 }}>
                  <span style={{ width: 120, fontSize: 12.5 }} title={r.group}>{r.group}</span>
                  <div className="bar" style={{ flex: 1 }}><i style={{ width: `${(reg ? r.metric / max : r.metric) * 100}%`, background: reg ? '#f59e0b' : '#a855f7' }} /></div>
                  <b style={{ width: 58, textAlign: 'right', fontSize: 12.5 }}>{(r.metric * 100).toFixed(1)}%</b>
                  <span className="muted" style={{ width: 44, fontSize: 11.5 }}>n={r.n}</span>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ------------------------------ regression performance ------------------------------ */
function RegPerformance({ m }) {
  const fmt = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })
  const lo = Math.min(...m.scatter.map((d) => Math.min(d.actual, d.predicted)))
  const hi = Math.max(...m.scatter.map((d) => Math.max(d.actual, d.predicted)))
  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="grid g4">
        {[['R² (accuracy)', (m.r2 * 100).toFixed(1) + '%', scoreColor(m.r2 * 100)], ['RMSE', fmt(m.rmse)], ['MAE', fmt(m.mae)], ['Mean abs. % error', (m.mape * 100).toFixed(1) + '%', scoreColor(100 - m.mape * 300)]].map(([l, v, c]) => (
          <div key={l} className="card metric"><div className="metric-label">{l}</div><div className="metric-value" style={{ color: c }}>{v}</div></div>
        ))}
      </div>
      <div className="grid g2">
        <div className="card card-pad">
          <div className="card-title">Actual vs predicted</div>
          <div className="card-sub">Points on the diagonal are perfect predictions</div>
          <div style={{ height: 300, marginTop: 10 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ left: 0, right: 16, top: 10 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                <XAxis type="number" dataKey="actual" name="Actual" domain={[lo, hi]} tick={{ fontSize: 11 }} tickFormatter={(v) => Math.round(v)} />
                <YAxis type="number" dataKey="predicted" name="Predicted" domain={[lo, hi]} tick={{ fontSize: 11 }} tickFormatter={(v) => Math.round(v)} />
                <Tooltip formatter={(v) => fmt(v)} />
                <ReferenceLine segment={[{ x: lo, y: lo }, { x: hi, y: hi }]} stroke="#8b8988" strokeDasharray="5 5" />
                <Scatter isAnimationActive={false} data={m.scatter} fill="#9312ff" fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card card-pad">
          <div className="card-title">Residual distribution</div>
          <div className="card-sub">Errors should be centred on zero</div>
          <div style={{ height: 300, marginTop: 10 }}>
            <ResponsiveContainer>
              <BarChart data={m.residual_hist} margin={{ left: -10 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="bin" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar isAnimationActive={false} dataKey="count" fill="#a855f7" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="card">
        <div className="card-head" style={{ paddingBottom: 12 }}>
          <div><div className="card-title">Actual vs predicted comparison table</div><div className="card-sub">First 20 rows of the unseen test set</div></div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 360, overflow: 'auto' }}>
          <table className="table">
            <thead><tr><th>#</th><th>Actual</th><th>Predicted</th><th>Error</th><th>Error %</th></tr></thead>
            <tbody>
              {m.comparison_table.map((r, i) => (
                <tr key={i}>
                  <td className="muted">{i + 1}</td><td><b>{fmt(r.actual)}</b></td><td>{fmt(r.predicted)}</td>
                  <td style={{ color: r.error >= 0 ? 'var(--warn)' : 'var(--brand)' }}>{r.error >= 0 ? '+' : ''}{fmt(r.error)}</td>
                  <td><span className={`badge ${r.error_pct <= 0.1 ? 'pass' : r.error_pct <= 0.2 ? 'warn' : 'fail'}`}>{(r.error_pct * 100).toFixed(1)}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="grid g2">
        <div className="card card-pad">
          <div className="card-title">Feature importance</div>
          <div className="card-sub">Permutation importance — drop in R² when a feature is shuffled</div>
          <div style={{ height: 290, marginTop: 10 }}>
            {m.feature_importance.length ? (
              <ResponsiveContainer>
                <BarChart data={m.feature_importance} layout="vertical" margin={{ left: 30, right: 20 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="feature" width={130} tick={{ fontSize: 11.5 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => v.toFixed(4)} />
                  <Bar isAnimationActive={false} dataKey="importance" radius={[0, 6, 6, 0]}>{m.feature_importance.map((_, i) => <Cell key={i} fill={i === 0 ? '#9312ff' : '#d2a8ff'} />)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="muted">Not available.</div>}
          </div>
        </div>
        <div className="card card-pad">
          <div className="card-title">Generalisation</div>
          <div className="card-sub" style={{ marginBottom: 16 }}>Train vs test vs cross-validated R²</div>
          {[['Training R²', m.train_r2], ['Test R²', m.r2], ['Cross-validation R²', m.cv_mean]].map(([l, v]) => (
            <div key={l} style={{ marginBottom: 16 }}>
              <div className="row" style={{ marginBottom: 6 }}><b style={{ fontSize: 13 }}>{l}</b><div className="spacer" /><b>{(v * 100).toFixed(1)}%</b></div>
              <div className="bar"><i style={{ width: `${Math.max(0, v) * 100}%`, background: '#a855f7' }} /></div>
            </div>
          ))}
          <div className="callout info" style={{ marginTop: 20 }}>Model trained in {m.fit_time.toFixed(2)}s.</div>
        </div>
      </div>
      <SlicesCard rows={m.slices} task="regression" />
    </div>
  )
}

function RegProfile({ p }) {
  const t = p.target_stats
  const f = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 })
  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="grid g4">
        {[['Rows', p.rows.toLocaleString()], ['Usable rows', p.usable_rows.toLocaleString()], ['Features', `${p.features} (${p.numeric_features} num · ${p.categorical_features} cat)`], ['Missing cells', `${(p.missing_pct * 100).toFixed(1)}%`]].map(([l, v]) => (
          <div key={l} className="card metric"><div className="metric-label">{l}</div><div className="metric-value" style={{ fontSize: 22 }}>{v}</div></div>
        ))}
      </div>
      <div className="card card-pad">
        <div className="card-title">Target distribution</div>
        <div className="card-sub">mean {f(t.mean)} · median {f(t.median)} · range {f(t.min)} – {f(t.max)} · skew {t.skew.toFixed(2)}</div>
        <div style={{ height: 260, marginTop: 14 }}>
          <ResponsiveContainer>
            <BarChart data={p.target_histogram} margin={{ left: -10 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
              <XAxis dataKey="bin" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar isAnimationActive={false} dataKey="count" fill="#06b6d4" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      {p.notes.length > 0 && <div className="callout info">{p.notes.join(' · ')}</div>}
    </div>
  )
}

/* ------------------------------ live monitoring ------------------------------ */
function Monitoring({ run }) {
  const [m, setM] = useState(null)
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const load = () => api.monitor(run.id).then(setM).catch((e) => setErr(e.message))
  useEffect(() => { load() }, [run.id])
  const act = async (name, fn) => { setBusy(name); setErr(''); try { await fn(); await load() } catch (e) { setErr(e.message) } finally { setBusy('') } }
  if (err && !m) return <div className="error-box">{err}</div>
  if (!m) return <Loading text="Training the model for monitoring…" />
  const tone = m.drift_status === 'DRIFT DETECTED' ? 'fail' : m.drift_status === 'warning' ? 'warn' : m.drift_status === 'stable' ? 'pass' : 'skip'
  const col = { pass: '#45b558', warn: '#f2a93b', fail: '#f03b2a', null: '#8b8988' }
  return (
    <div className="grid" style={{ gap: 18 }}>
      {err && <div className="error-box">{err}</div>}
      <div className="card card-pad row" style={{ gap: 10, flexWrap: 'wrap' }}>
        <Activity size={20} color="var(--brand)" />
        <div style={{ flex: 1, minWidth: 240 }}>
          <div className="card-title">Live prediction monitoring</div>
          <div className="card-sub">Every prediction (playground or API) is logged and compared with the training data to detect drift.</div>
        </div>
        <button className="btn" disabled={!!busy} onClick={() => act('n', () => api.simulate(run.id, { n: 100, drift: false }))}>{busy === 'n' ? '…' : 'Simulate normal traffic'}</button>
        <button className="btn btn-magic" disabled={!!busy} onClick={() => act('d', () => api.simulate(run.id, { n: 100, drift: true }))}>{busy === 'd' ? '…' : 'Simulate drifted traffic'}</button>
        <button className="btn" onClick={load}>Refresh</button>
        <button className="btn btn-danger" disabled={!!busy} onClick={() => act('c', () => api.clearMonitor(run.id))}>Clear log</button>
      </div>
      <div className="grid g4">
        <div className="card metric"><div className="metric-label">Predictions logged</div><div className="metric-value">{m.n}</div></div>
        <div className="card metric"><div className="metric-label">Latency avg · p95</div><div className="metric-value" style={{ fontSize: 22 }}>{m.avg_latency_ms} · {m.p95_latency_ms} ms</div></div>
        <div className="card metric"><div className="metric-label">Drift status</div><div style={{ marginTop: 8 }}><span className={`badge ${tone}`} style={{ fontSize: 13, padding: '5px 12px' }}>{m.drift_status}</span></div><div className="muted" style={{ fontSize: 12, marginTop: 6 }}>max PSI {m.max_psi}</div></div>
        <div className="card metric"><div className="metric-label">Drift detection time</div><div className="metric-value" style={{ fontSize: 22, color: 'var(--pass)' }}>{m.detect_ms} ms</div><div className="muted" style={{ fontSize: 12 }}>target &lt; 5 s</div></div>
      </div>
      {m.n === 0 ? (
        <div className="card"><Empty icon={Activity} title="No traffic yet" text="Use the playground, or press “Simulate” to replay traffic through the model." /></div>
      ) : (
        <>
          <div className="grid g2">
            <div className="card card-pad">
              <div className="card-title">Feature drift (PSI)</div>
              <div className="card-sub">Live inputs vs training data · &lt;0.10 stable · 0.10–0.25 warning · &gt;0.25 drift</div>
              <div style={{ height: 300, marginTop: 10 }}>
                <ResponsiveContainer>
                  <BarChart data={m.features.filter((f) => f.psi !== null).map((f) => ({ ...f, psi: +f.psi.toFixed(3) }))} layout="vertical" margin={{ left: 30, right: 20 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11.5 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <ReferenceLine x={0.25} stroke="#f03b2a" strokeDasharray="4 4" />
                    <ReferenceLine x={0.1} stroke="#f2a93b" strokeDasharray="4 4" />
                    <Bar isAnimationActive={false} dataKey="psi" radius={[0, 6, 6, 0]}>{m.features.filter((f) => f.psi !== null).map((f) => <Cell key={f.name} fill={col[f.status]} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {m.n < 30 && <div className="callout info">Log at least 30 predictions for a reliable drift verdict.</div>}
            </div>
            <div className="card card-pad">
              <div className="card-title">Prediction latency</div>
              <div className="card-sub">Last {m.latency_series.length} predictions (ms)</div>
              <div style={{ height: 300, marginTop: 10 }}>
                <ResponsiveContainer>
                  <LineChart data={m.latency_series.map((v, i) => ({ i: i + 1, ms: v }))} margin={{ left: -10, right: 16 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="i" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => `${v} ms`} />
                    <Line isAnimationActive={false} type="monotone" dataKey="ms" stroke="#9312ff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div className="card table-wrap">
            <div className="card-head" style={{ paddingBottom: 12 }}><div className="card-title">Recent predictions</div></div>
            <table className="table">
              <thead><tr><th>Prediction</th><th>Inputs</th><th>Latency</th><th>Source</th></tr></thead>
              <tbody>
                {m.recent.map((r, i) => (
                  <tr key={i}>
                    <td><b>{r.prediction}</b></td>
                    <td className="muted" style={{ fontSize: 12, maxWidth: 520 }}>{Object.entries(r.features).slice(0, 5).map(([k, v]) => `${k}=${typeof v === 'number' ? +v.toFixed(2) : v}`).join(' · ')}</td>
                    <td>{r.latency_ms} ms</td><td><span className={`badge ${r.simulated ? 'gray' : 'brand'}`}>{r.simulated ? 'simulated' : 'live'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

/* ------------------------------ detailed classification metrics ------------------------------ */
function DetailedMetrics({ m }) {
  const total = m.per_class.reduce((a, c) => a + c.support, 0)
  const wavg = (k) => m.per_class.reduce((a, c) => a + c[k] * c.support, 0) / Math.max(total, 1)
  const pct = (v) => (v * 100).toFixed(1) + '%'
  const cell = (v) => <b style={{ color: scoreColor(v * 100) }}>{pct(v)}</b>
  return (
    <div className="card">
      <div className="card-head" style={{ paddingBottom: 12 }}>
        <div>
          <div className="card-title">Detailed classification metrics</div>
          <div className="card-sub">Precision = of the rows predicted as a class, how many were right · Recall = of the real rows of a class, how many were found · F1 = balance of both</div>
        </div>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1-score</th><th>Support (test rows)</th></tr></thead>
          <tbody>
            {m.per_class.map((c) => (
              <tr key={c.class}><td><b>{c.class}</b></td><td>{cell(c.precision)}</td><td>{cell(c.recall)}</td><td>{cell(c.f1)}</td><td>{c.support}</td></tr>
            ))}
            <tr style={{ background: 'var(--surface-2)' }}><td><b>Macro average</b></td><td>{cell(m.precision)}</td><td>{cell(m.recall)}</td><td>{cell(m.f1)}</td><td>{total}</td></tr>
            <tr style={{ background: 'var(--surface-2)' }}><td><b>Weighted average</b></td><td>{cell(wavg('precision'))}</td><td>{cell(wavg('recall'))}</td><td>{cell(wavg('f1'))}</td><td>{total}</td></tr>
            <tr style={{ background: 'var(--surface-2)' }}><td><b>Accuracy</b></td><td colSpan={3}>{cell(m.accuracy)}</td><td>{total}</td></tr>
          </tbody>
        </table>
      </div>
      <div className="row" style={{ gap: 10, padding: '14px 22px 18px', flexWrap: 'wrap' }}>
        <span className="perf-chip">Train F1 {pct(m.train_f1)}</span>
        <span className="perf-chip">Test F1 {pct(m.f1)}</span>
        <span className="perf-chip">Cross-validation F1 {pct(m.cv_mean)} ± {(m.cv_std * 100).toFixed(1)}</span>
        <span className="perf-chip">Train–test gap {((m.train_f1 - m.f1) * 100).toFixed(1)} pts</span>
      </div>
    </div>
  )
}
