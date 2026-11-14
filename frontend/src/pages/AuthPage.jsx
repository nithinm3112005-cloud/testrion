import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Loader2 } from 'lucide-react'
import '@fontsource-variable/inter'
import '../landing.css'
import { TrMark } from './Landing.jsx'
import { useAuth } from '../auth.jsx'

export default function AuthPage({ mode }) {
  const isSignup = mode === 'signup'
  const { user, login, signup } = useAuth()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [form, setForm] = useState({ name: '', email: params.get('email') || '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e, creds) => {
    e?.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (creds) await login(creds.email, creds.password)
      else if (isSignup) await signup(form.name, form.email, form.password)
      else await login(form.email, form.password)
      const next = params.get('next')
      nav(next && /^\/app(\/|$)/.test(next) ? next : '/app')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  useEffect(() => {
    if (params.get('demo') && !isSignup) submit(null, { email: 'demo@mltestlab.com', password: 'demo1234' })
  }, [])

  if (user && !busy) return <Navigate to="/app" replace />

  return (
    <div className="auth tr-auth">
      <div className="auth-side">
        <Link to="/" className="row" style={{ gap: 11 }}>
          <TrMark size={26} />
          <span style={{ fontWeight: 700, fontSize: 20, letterSpacing: '-0.02em' }}>Testrion</span>
        </Link>
        <div>
          <h1>Trust your models before your users do.</h1>
          <p>Automated testing and problem solving for machine-learning models.</p>
          <ul>
            {['20+ automated tests in seconds', 'Plain-English diagnosis of every failure', 'One-click auto-fix with before/after proof', 'Deployment gate, live monitoring and model export'].map((t) => (
              <li key={t}><CheckCircle2 size={18} /> {t}</li>
            ))}
          </ul>
        </div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>© {new Date().getFullYear()} Testrion</div>
      </div>

      <div className="auth-main">
        <form className="auth-card" onSubmit={submit}>
          <h2>{isSignup ? 'Create your account' : 'Welcome back'}</h2>
          <p className="muted" style={{ margin: '4px 0 22px' }}>
            {isSignup ? 'Start testing your models in under a minute.' : 'Log in to continue to your workspace.'}
          </p>
          {error && <div className="error-box">{error}</div>}

          {isSignup && (
            <label className="field">Full name
              <input className="input" value={form.name} onChange={set('name')} placeholder="Ada Lovelace" autoComplete="name" required />
            </label>
          )}
          <label className="field">Email
            <input className="input" type="email" value={form.email} onChange={set('email')} placeholder="you@example.com" autoComplete="email" required />
          </label>
          <label className="field">Password
            <input className="input" type="password" value={form.password} onChange={set('password')} placeholder={isSignup ? 'At least 6 characters' : 'Your password'} autoComplete={isSignup ? 'new-password' : 'current-password'} required minLength={isSignup ? 6 : undefined} />
          </label>

          <button className="btn btn-primary btn-lg" style={{ width: '100%', justifyContent: 'center', marginTop: 6 }} disabled={busy}>
            {busy && <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />}
            {isSignup ? 'Create account' : 'Log in'}
          </button>

          {!isSignup && (
            <>
              <div className="auth-or"><span>or</span></div>
              <button type="button" className="btn btn-lg" style={{ width: '100%', justifyContent: 'center' }} disabled={busy}
                onClick={() => submit(null, { email: 'demo@mltestlab.com', password: 'demo1234' })}>
                Continue with demo account
              </button>
            </>
          )}

          <div className="muted" style={{ textAlign: 'center', marginTop: 20 }}>
            {isSignup ? <>Already have an account? <Link to="/login" className="auth-link">Log in</Link></> : <>New here? <Link to="/signup" className="auth-link">Create an account</Link></>}
          </div>
        </form>
      </div>
    </div>
  )
}
