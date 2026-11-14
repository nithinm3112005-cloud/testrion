import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Activity, ArrowRight, Bug, CheckCircle2, FlaskConical, Play, ShieldCheck, Sparkles, TrendingUp, Wand2,
} from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Empty, Loading, MODEL_LABELS, Page, ScoreRing, Stat, fmtDate, scoreColor } from '../components/ui.jsx'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [runs, setRuns] = useState([])
  const nav = useNavigate()
  const { user } = useAuth()
  const [t0] = useState(() => performance.now())
  const [loadMs, setLoadMs] = useState(null)
  const [demo, setDemo] = useState(0) // 0 idle, 1 testing, 2 fixing
  const [demoErr, setDemoErr] = useState('')
  const runDemo = async () => {
    setDemoErr(''); setDemo(1)
    try {
      const r = await api.createRun({ dataset_id: 'builtin:house_price', target: 'price_lakhs', model: 'linear_regression' })
      setDemo(2)
      const f = await api.autofix(r.id)
      nav(`/app/runs/${f.id}`)
    } catch (e) { setDemo(0); setDemoErr(e.message) }
  }

  useEffect(() => {
    api.stats().then((s) => { setStats(s); requestAnimationFrame(() => setLoadMs(Math.round(performance.now() - t0))) })
    api.runs().then(setRuns)
  }, [])

  if (!stats) return <Loading />

  return (
    <Page title={`Welcome back, ${user.name.split(' ')[0]} 👋`} sub={<span className="row" style={{ gap: 10, flexWrap: 'wrap' }}>Overview of your machine-learning quality checks{loadMs !== null && <span className="perf-chip" title="Requirement: dashboard loads in under 3 seconds">⚡ Loaded in {loadMs} ms {loadMs < 3000 ? '✓' : ''} <span className="muted" style={{ fontWeight: 500 }}>(target &lt; 3000 ms)</span></span>}</span>}>
      <div className="hero">
        <ShieldCheck className="hero-art" size={200} />
        <h1>Test your ML models automatically — and let the platform fix the problems.</h1>
        <p>
          Upload a dataset, pick a model, and Testrion runs 20+ checks across data quality, performance, robustness,
          reliability and fairness. Failed tests are diagnosed and repaired with one click.
        </p>
        <div className="row">
          <button className="btn btn-white btn-lg" onClick={runDemo} disabled={demo > 0}>
            <Play size={16} /> One-click demo
          </button>
          <Link to="/app/new" className="btn btn-glass btn-lg">
            Run a new test
          </Link>
          <Link to="/app/how-it-works" className="btn btn-glass btn-lg">
            How it works <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      {demoErr && <div className="error-box mt">{demoErr}</div>}
      {demo > 0 && (
        <div className="overlay"><div className="modal" style={{ textAlign: 'center' }}>
          <div className="spinner" />
          <h3>{demo === 1 ? 'Testing a house-price model…' : 'Auto-fixing the problems…'}</h3>
          <div className="muted">{demo === 1 ? 'Linear Regression on raw, messy data → running all automated tests.' : 'Repairing the data, tuning, searching better models and re-testing everything.'}</div>
        </div></div>
      )}

      <div className="grid g6 mt-lg">
        <Stat icon={FlaskConical} label="Total runs" value={stats.total_runs} />
        <Stat icon={Activity} label="Average score" value={stats.avg_score} suffix="/100" color="#22d3ee" bg="rgba(34,211,238,0.12)" />
        <Stat icon={CheckCircle2} label="Tests passed" value={stats.tests_passed} color="var(--pass)" bg="var(--pass-bg)" />
        <Stat icon={Bug} label="Issues found" value={stats.issues_found} color="var(--fail)" bg="var(--fail-bg)" />
        <Stat icon={Wand2} label="Auto-fixes applied" value={stats.auto_fixes} color="#b24bff" bg="rgba(147,18,255,0.16)" />
        <Stat icon={TrendingUp} label="Avg. score gain" value={`+${stats.avg_improvement}`} color="var(--warn)" bg="var(--warn-bg)" />
      </div>

      <div className="grid mt-lg" style={{ gridTemplateColumns: '1.6fr 1fr' }}>
        <div className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Quality score trend</div>
              <div className="card-sub">Last {stats.trend.length} runs (tests and auto-fixes)</div>
            </div>
          </div>
          <div style={{ height: 270, padding: '10px 10px 14px 0' }}>
            {stats.trend.length ? (
              <ResponsiveContainer>
                <AreaChart data={stats.trend} margin={{ left: 0, right: 20, top: 16 }}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#a855f7" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#8b8988' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#8b8988' }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip formatter={(v) => [`${v}/100`, 'Score']} />
                  <Area isAnimationActive={false} type="monotone" dataKey="score" stroke="#9312ff" strokeWidth={2.5} fill="url(#g)" dot={{ r: 3.5, fill: '#9312ff' }} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Empty icon={TrendingUp} title="No runs yet" text="Run your first test to see the trend." />
            )}
          </div>
        </div>

        <div className="card card-pad">
          <div className="card-title">Try a demo in seconds</div>
          <div className="card-sub" style={{ marginBottom: 14 }}>
            Datasets with built-in problems, perfect for the auto-fix feature.
          </div>
          <div className="grid" style={{ gap: 10 }}>
            {[
              ['builtin:house_price', 'House Price Prediction', 'Regression · project dataset · gate & fairness', 'linear_regression'],
              ['builtin:churn', 'Customer Churn', 'Missing values · duplicates · imbalance', 'logistic_regression'],
              ['builtin:credit', 'Credit Default', 'Data leakage · severe imbalance', 'knn'],
              ['builtin:wine', 'Wine Cultivars', 'Unscaled features · SVM', 'svm'],
            ].map(([id, name, desc, model]) => (
              <button
                key={id}
                className="choice"
                style={{ flexDirection: 'row', alignItems: 'center' }}
                onClick={() => nav(`/app/new?dataset=${encodeURIComponent(id)}&model=${model}`)}
              >
                <div style={{ flex: 1 }}>
                  <div className="choice-title">{name}</div>
                  <div className="choice-desc">{desc}</div>
                </div>
                <ArrowRight size={16} color="var(--brand)" />
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card mt-lg">
        <div className="card-head" style={{ paddingBottom: 14 }}>
          <div className="card-title">Recent runs</div>
          <Link to="/app/history" className="btn btn-ghost" style={{ color: 'var(--brand)' }}>
            View all <ArrowRight size={14} />
          </Link>
        </div>
        {runs.length === 0 ? (
          <Empty icon={Sparkles} title="Nothing here yet" text="Your test runs will show up here."
            action={<Link to="/app/new" className="btn btn-primary">Run first test</Link>} />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Run</th><th>Dataset</th><th>Model</th><th>Score</th><th>Result</th><th>When</th><th /></tr>
              </thead>
              <tbody>
                {runs.slice(0, 6).map((r) => (
                  <tr key={r.id} className="clickable" onClick={() => nav(`/app/runs/${r.id}`)}>
                    <td><b>#{r.id}</b> {r.kind === 'autofix' && <span className="badge brand" style={{ marginLeft: 6 }}><Wand2 size={11} /> Auto-fix</span>}</td>
                    <td>{r.dataset_name}</td>
                    <td className="muted">{MODEL_LABELS[r.model] || r.model}</td>
                    <td><b style={{ color: scoreColor(r.score) }}>{r.score}</b></td>
                    <td>
                      <span className="badge pass">{r.passed}</span>{' '}
                      <span className="badge warn">{r.warned}</span>{' '}
                      <span className="badge fail">{r.failed}</span>
                    </td>
                    <td className="muted">{fmtDate(r.created_at)}</td>
                    <td><ArrowRight size={15} color="#8b8988" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Page>
  )
}
