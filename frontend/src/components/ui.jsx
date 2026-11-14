import { CheckCircle2, AlertTriangle, XCircle, MinusCircle, Loader2 } from 'lucide-react'

export const STATUS = {
  pass: { label: 'Passed', Icon: CheckCircle2, color: 'var(--pass)' },
  warn: { label: 'Warning', Icon: AlertTriangle, color: 'var(--warn)' },
  fail: { label: 'Failed', Icon: XCircle, color: 'var(--fail)' },
  skip: { label: 'Skipped', Icon: MinusCircle, color: 'var(--skip)' },
}

export function StatusBadge({ status }) {
  const s = STATUS[status] || STATUS.skip
  return (
    <span className={`badge ${status}`}>
      <s.Icon size={13} /> {s.label}
    </span>
  )
}

export const scoreColor = (s) => (s >= 80 ? 'var(--pass)' : s >= 60 ? 'var(--warn)' : 'var(--fail)')

export function gradeOf(s) {
  return s >= 90 ? 'A' : s >= 80 ? 'B' : s >= 70 ? 'C' : s >= 55 ? 'D' : 'F'
}

export function ScoreRing({ score, size = 150, stroke = 12, grade, label = true }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const color = scoreColor(score)
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - Math.min(100, score) / 100)}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="ring-text">
        <div className="ring-score" style={{ fontSize: size * 0.27, color }}>
          {Math.round(score)}
        </div>
        {label && <div className="ring-grade">Grade {grade || gradeOf(score)}</div>}
      </div>
    </div>
  )
}

export function Stat({ icon: Icon, label, value, color = 'var(--brand)', bg = 'var(--brand-50)', suffix = '' }) {
  return (
    <div className="card stat">
      <div className="stat-icon" style={{ background: bg, color }}>
        <Icon size={19} />
      </div>
      <div className="stat-value">
        {value}
        {suffix}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export function Page({ title, sub, actions, crumbs, children }) {
  return (
    <div className="page">
      {crumbs}
      <div className="page-head">
        <div>
          <h1 className="page-title">{title}</h1>
          {sub && <div className="page-sub">{sub}</div>}
        </div>
        <div className="row no-print">{actions}</div>
      </div>
      {children}
    </div>
  )
}

export function Loading({ text = 'Loading…' }) {
  return (
    <div className="loading-page">
      <div style={{ textAlign: 'center', color: 'var(--muted)' }}>
        <Loader2 size={30} style={{ animation: 'spin 1s linear infinite', color: 'var(--brand)' }} />
        <div style={{ marginTop: 10 }}>{text}</div>
      </div>
    </div>
  )
}

export function Empty({ icon: Icon, title, text, action }) {
  return (
    <div className="empty">
      <Icon size={38} style={{ color: '#6e6c75' }} />
      <h3>{title}</h3>
      <div>{text}</div>
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  )
}

export const fmtDate = (s) => {
  if (!s) return ''
  const d = new Date(s.replace(' ', 'T') + 'Z')
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export const MODEL_LABELS = {
  logistic_regression: 'Logistic Regression',
  random_forest: 'Random Forest',
  decision_tree: 'Decision Tree',
  knn: 'K-Nearest Neighbours',
  svm: 'Support Vector Machine',
  gradient_boosting: 'Gradient Boosting',
  linear_regression: 'Linear Regression',
  ridge: 'Ridge Regression',
  decision_tree_reg: 'Decision Tree Regressor',
  random_forest_reg: 'Random Forest Regressor',
  gradient_boosting_reg: 'Gradient Boosting Regressor',
  knn_reg: 'KNN Regressor',
}
