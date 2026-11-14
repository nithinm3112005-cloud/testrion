import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, FlaskConical, GitCompare, History, Trash2, Wand2 } from 'lucide-react'
import { api } from '../api.js'
import { Empty, Loading, MODEL_LABELS, Page, fmtDate, scoreColor } from '../components/ui.jsx'

export default function HistoryPage() {
  const nav = useNavigate()
  const [runs, setRuns] = useState(null)
  const [q, setQ] = useState('')
  const [kind, setKind] = useState('all')
  const [sel, setSel] = useState([])
  const toggle = (e, id) => { e.stopPropagation(); setSel((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id].slice(-2)) }

  const load = () => api.runs().then(setRuns)
  useEffect(() => { load() }, [])

  const remove = async (e, r) => {
    e.stopPropagation()
    if (!confirm(`Delete run #${r.id}?`)) return
    await api.deleteRun(r.id)
    load()
  }

  if (!runs) return <Loading />
  const shown = runs.filter((r) =>
    (kind === 'all' || r.kind === kind) &&
    `${r.dataset_name} ${r.model} ${r.target} ${r.id}`.toLowerCase().includes(q.toLowerCase())
  )

  return (
    <Page
      title="Test history"
      sub={`${runs.length} run${runs.length === 1 ? '' : 's'} recorded`}
      actions={<>{sel.length === 2 && <Link to={`/app/compare?a=${sel[0]}&b=${sel[1]}`} className="btn btn-magic"><GitCompare size={16} /> Compare selected</Link>}<Link to="/app/new" className="btn btn-primary"><FlaskConical size={16} /> New test</Link></>}
    >
      <div className="row" style={{ marginBottom: 16 }}>
        <input className="input" style={{ maxWidth: 320 }} placeholder="Search by dataset, model or run id…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="chips">
          {[['all', 'All'], ['test', 'Tests'], ['autofix', 'Auto-fixes']].map(([k, l]) => (
            <button key={k} className={`chip ${kind === k ? 'active' : ''}`} onClick={() => setKind(k)}>{l}</button>
          ))}
        </div>
      </div>
      <div className="card">
        {shown.length === 0 ? (
          <Empty icon={History} title="No runs found" text="Run a test to see it here." />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th style={{ width: 30 }} /><th>Run</th><th>Dataset</th><th>Target</th><th>Model</th><th>Score</th><th>Pass</th><th>Warn</th><th>Fail</th><th>When</th><th /></tr></thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.id} className="clickable" onClick={() => nav(`/app/runs/${r.id}`)}>
                    <td><input type="checkbox" checked={sel.includes(r.id)} onClick={(e) => toggle(e, r.id)} onChange={() => {}} title="Select to compare" /></td>
                    <td>
                      <b>#{r.id}</b>{' '}
                      {r.kind === 'autofix' && <span className="badge brand" style={{ marginLeft: 4 }}><Wand2 size={11} /> from #{r.parent_run_id}</span>}
                    </td>
                    <td>{r.dataset_name}</td>
                    <td className="muted">{r.target}</td>
                    <td className="muted">{MODEL_LABELS[r.model] || r.model}</td>
                    <td style={{ width: 150 }}>
                      <div className="row" style={{ gap: 8 }}>
                        <b style={{ color: scoreColor(r.score), width: 34 }}>{r.score}</b>
                        <div className="bar" style={{ flex: 1 }}><i style={{ width: `${r.score}%`, background: scoreColor(r.score) }} /></div>
                      </div>
                    </td>
                    <td><span className="badge pass">{r.passed}</span></td>
                    <td><span className="badge warn">{r.warned}</span></td>
                    <td><span className="badge fail">{r.failed}</span></td>
                    <td className="muted">{fmtDate(r.created_at)}</td>
                    <td>
                      <div className="row" style={{ gap: 4 }}>
                        <button className="btn btn-ghost btn-danger" onClick={(e) => remove(e, r)}><Trash2 size={15} /></button>
                        <ArrowRight size={15} color="#8b8988" />
                      </div>
                    </td>
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
