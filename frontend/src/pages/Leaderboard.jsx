import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, Layers, Timer, Trophy, Zap } from 'lucide-react'
import { api } from '../api.js'
import { Loading, MODEL_LABELS, Page, scoreColor } from '../components/ui.jsx'

export default function Leaderboard() {
  const [p] = useSearchParams()
  const nav = useNavigate()
  const [runs, setRuns] = useState(null)
  const ids = (p.get('ids') || '').split(',').filter(Boolean).map(Number)

  useEffect(() => { api.runs().then((r) => setRuns(r.filter((x) => ids.includes(x.id)).sort((a, b) => b.score - a.score))) }, [p.get('ids')])
  if (!runs) return <Loading />

  const elapsed = p.get('t'), seq = p.get('seq'), sp = p.get('sp')
  return (
    <Page title="Model leaderboard" sub={runs[0] ? `${runs[0].dataset_name} · ${runs.length} models tested in parallel` : ''}
      actions={<Link to="/app/new" className="btn btn-primary"><Layers size={16} /> New benchmark</Link>}>
      <div className="row" style={{ gap: 10, marginBottom: 18, flexWrap: 'wrap' }}>
        <span className="perf-chip"><Layers size={15} color="var(--brand)" /> {runs.length} models</span>
        {elapsed && <span className="perf-chip"><Timer size={15} color="var(--brand)" /> {elapsed}s wall-clock (parallel)</span>}
        {seq && <span className="perf-chip">{seq}s if run one-by-one</span>}
        {sp && <span className="perf-chip"><Zap size={15} color="var(--warn)" /> {sp}× faster</span>}
      </div>
      <div className="card">
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th style={{ width: 50 }}>Rank</th><th>Model</th><th>Quality score</th><th>Pass</th><th>Warn</th><th>Fail</th><th /></tr></thead>
            <tbody>
              {runs.map((r, i) => (
                <tr key={r.id} className="clickable" onClick={() => nav(`/app/runs/${r.id}`)}>
                  <td><div className={`rank ${i === 0 ? 'first' : ''}`}>{i === 0 ? <Trophy size={14} /> : i + 1}</div></td>
                  <td><b>{MODEL_LABELS[r.model] || r.model}</b> <span className="muted">· run #{r.id}</span></td>
                  <td style={{ width: 260 }}>
                    <div className="row" style={{ gap: 8 }}>
                      <b style={{ color: scoreColor(r.score), width: 38 }}>{r.score}</b>
                      <div className="bar" style={{ flex: 1 }}><i style={{ width: `${r.score}%`, background: scoreColor(r.score) }} /></div>
                    </div>
                  </td>
                  <td><span className="badge pass">{r.passed}</span></td>
                  <td><span className="badge warn">{r.warned}</span></td>
                  <td><span className="badge fail">{r.failed}</span></td>
                  <td><ArrowRight size={15} color="#8b8988" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="muted mt" style={{ fontSize: 13 }}>Open any model to see its deployment gate, then use <b>Auto-fix</b> to improve the best candidates further.</div>
    </Page>
  )
}
