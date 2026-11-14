import { useEffect, useState } from 'react'
import { Database, FlaskConical, Search, ShieldCheck, Wand2 } from 'lucide-react'
import { api } from '../api.js'
import { Loading, Page } from '../components/ui.jsx'

const FLOW = [
  [Database, 'Upload data', 'Bring any CSV or use a built-in sample dataset.', '#9312ff', 'rgba(147,18,255,0.12)'],
  [FlaskConical, 'Train & test', 'The model is trained and 20+ automated tests are executed.', '#22d3ee', 'rgba(34,211,238,0.12)'],
  [Search, 'Diagnose', 'Each failure is explained with evidence and a recommended fix.', '#f2a93b', 'rgba(242,169,59,0.14)'],
  [Wand2, 'Auto-fix', 'Data is repaired, hyper-parameters tuned, better models searched.', '#b24bff', 'rgba(147,18,255,0.16)'],
  [ShieldCheck, 'Re-validate', 'Every test is re-run so improvements are proven, not assumed.', '#45b558', 'rgba(69,181,88,0.14)'],
]

export default function HowItWorks() {
  const [cat, setCat] = useState(null)
  useEffect(() => { api.catalog().then(setCat) }, [])
  if (!cat) return <Loading />
  return (
    <Page title="How it works" sub="Automated software testing and problem solving of machine-learning models">
      <div className="flow">
        {FLOW.map(([Icon, t, d, c, bg], i) => (
          <div key={t} className="card flow-step">
            <div className="stat-icon" style={{ background: bg, color: c }}><Icon size={20} /></div>
            <h4>{i + 1}. {t}</h4>
            <p>{d}</p>
          </div>
        ))}
      </div>

      <h3 style={{ margin: '34px 0 14px' }}>The automated tests</h3>
      <div className="grid g2">
        {cat.map((c) => (
          <div key={c.category} className="card card-pad cat-card">
            <h3>{c.category}</h3>
            {c.tests.map(([n, d]) => (
              <div key={n} className="cat-test"><b>{n}</b><span>{d}</span></div>
            ))}
          </div>
        ))}
      </div>

      <div className="grid g2 mt-lg">
        <div className="card card-pad">
          <h3 style={{ marginBottom: 12 }}>Scoring</h3>
          <p className="muted" style={{ margin: 0 }}>
            Every test is <b style={{ color: 'var(--pass)' }}>passed</b> (1 point), <b style={{ color: 'var(--warn)' }}>warning</b> (½ point) or{' '}
            <b style={{ color: 'var(--fail)' }}>failed</b> (0). Categories are weighted — Model Performance ×2, Robustness and Fairness ×1.5, Data Quality and
            Reliability ×1 — to produce a 0–100 quality score and a grade from A to F.
          </p>
        </div>
        <div className="card card-pad">
          <h3 style={{ marginBottom: 12 }}>Problem-solving engine</h3>
          <p className="muted" style={{ margin: 0 }}>
            Stage 1 repairs the pipeline (imputation, de-duplication, leakage removal, scaling, class balancing, log-transform, fairness). Stage 2 runs a cross-validated
            hyper-parameter search. Stage 3 compares alternative algorithms. Later stages are only kept if the full test-suite score improves.
          </p>
        </div>
      </div>
    </Page>
  )
}
