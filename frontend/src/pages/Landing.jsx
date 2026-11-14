import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import '@fontsource-variable/inter'
import '../landing.css'
import {
  ArrowRight, Bell, Bug, Database, FlaskConical, GitCompare, History, LayoutDashboard, LineChart, Lock, MousePointerClick,
  Search, Settings, ShieldCheck, Wand2, Zap,
} from 'lucide-react'
import { useAuth } from '../auth.jsx'

/** Testrion mark: three slashes in violet. */
export function TrMark({ size = 30 }) {
  return (
    <svg className="tr-mark" width={size * 1.4} height={size} viewBox="0 0 42 30" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="trm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#d2a8ff" /><stop offset="1" stopColor="#9312ff" /></linearGradient>
      </defs>
      {[4, 17, 30].map((x) => <path key={x} d={`M${x} 27 L${x + 9} 3`} stroke="url(#trm)" strokeWidth="4.4" strokeLinecap="round" />)}
    </svg>
  )
}

/** Starfield (+ procedural planet rim as the fallback until the glow video is ready, and on phones). */
function Sky({ rim, s }) {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current
    if (!c) return
    const draw = () => {
      const ctx = c.getContext('2d')
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const w = c.clientWidth, h = c.clientHeight
      c.width = w * dpr; c.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
      let seed = 11
      const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
      for (let i = 0; i < Math.round((w * h) / 5200); i++) {
        const x = rnd() * w, y = rnd() * h, r = rnd() * 1.1 + 0.2, a = rnd() * 0.65 + 0.15
        ctx.fillStyle = `rgba(255,255,255,${a})`; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill()
      }
      if (rim) {
        const R = w * (w < 900 ? 1.7 : 1.2), cx = w / 2, top = w < 900 ? 150 : 150 * s, cy = top + R
        const g = ctx.createRadialGradient(cx, cy, R * 0.985, cx, cy, R * 1.12)
        g.addColorStop(0, 'rgba(147,18,255,0)'); g.addColorStop(0.07, 'rgba(235,205,255,0.95)'); g.addColorStop(0.2, 'rgba(178,75,255,0.6)')
        g.addColorStop(0.5, 'rgba(147,18,255,0.22)'); g.addColorStop(1, 'rgba(147,18,255,0)')
        ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(0, 0, w, h)
        ctx.globalCompositeOperation = 'source-over'
        const body = ctx.createRadialGradient(cx, cy, R * 0.8, cx, cy, R)
        body.addColorStop(0, '#000'); body.addColorStop(0.9, '#05020b'); body.addColorStop(1, 'rgba(60,10,110,0.7)')
        ctx.fillStyle = body; ctx.beginPath(); ctx.arc(cx, cy, R * 0.996, 0, 7); ctx.fill()
      }
    }
    draw()
    window.addEventListener('resize', draw)
    return () => window.removeEventListener('resize', draw)
  }, [rim, s])
  return <canvas ref={ref} className="tz-sky" aria-hidden="true" />
}

const FEATURES = [
  [FlaskConical, '24 automated tests', 'Data quality, performance, robustness, reliability and fairness checks run in seconds on any classifier or regressor.'],
  [Bug, 'Leakage & bias detection', 'Spot target leakage, class imbalance, weak slices and drift before they reach production.'],
  [Wand2, 'One-click auto-fix', 'Repair data, tune hyper-parameters and search better models — every fix is proven by re-testing.'],
  [Zap, 'Edge-case & adversarial tests', 'Generated min/max, null, out-of-range and special-character inputs, plus worst-case perturbation search.'],
  [MousePointerClick, 'Deployment gate', 'Accuracy (R² for regression) of at least 85% and parity difference below 10% — or the release is blocked.'],
  [GitCompare, 'Monitor, compare & export', 'Live drift monitoring, side-by-side run comparison and a ready-to-use model.pkl download.'],
]
const STEPS = [
  ['1', 'Upload', 'Drop in a CSV or pick a sample dataset and choose the column to predict.'],
  ['2', 'Test', 'Testrion trains the model and runs 20+ automated tests with clear evidence.'],
  ['3', 'Fix', 'Hit Auto-fix. Problems are repaired and every test is re-run to verify.'],
]
const DIMENSIONS = [
  [Database, 'Data Quality', 'Missing values, duplicates, imbalance, outliers, leakage, sample size'],
  [LineChart, 'Model Performance', 'Macro F1 / R², cross-validation, stability, overfitting, worst-class recall'],
  [Zap, 'Robustness', 'Noise, edge cases, adversarial search, missing inputs, metamorphic tests'],
  [Lock, 'Reliability', 'Reproducibility, train/test drift (PSI), prediction latency'],
  [ShieldCheck, 'Fairness & Slices', 'Gender / age / region slices and demographic parity, with a deployment gate'],
]
const FAQ = [
  ['What kind of models can I test?', 'Any classification or regression model on tabular data. Upload a CSV, pick the column to predict and choose from 12 built-in algorithms.'],
  ['What does the deployment gate check?', 'Hold-out accuracy (R² ≥ 0.85 for regression), demographic parity difference below 10%, every class detected, no target leakage and reproducible predictions. If a check fails, the release is blocked.'],
  ['What does Auto-fix actually do?', 'It repairs the data pipeline (imputation, de-duplication, leakage and protected-attribute removal, scaling, balancing), tunes hyper-parameters, searches better algorithms and re-runs every test. The test split is never used to choose a model.'],
  ['Does it run in CI?', 'Yes. A GitHub Actions workflow runs the test-suite and the deployment gate on every push, and fails the build when the gate is blocked.'],
]

export default function Landing() {
  const { user } = useAuth()
  const nav = useNavigate()
  const heroRef = useRef(null)
  const ctaRef = useRef(null)
  const [s, setS] = useState(1)
  const [mobile, setMobile] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [videoOn, setVideoOn] = useState(false)
  const [email, setEmail] = useState('')
  const [inView, setInView] = useState(false)

  // 1672 x 941 design stage scaled to the viewport: s = min(vw/1672, vh/941)
  useLayoutEffect(() => {
    const set = () => {
      const w = window.innerWidth, h = window.innerHeight
      const m = w <= 900 || h > w
      const sc = m ? 1 : Math.min(w / 1672, h / 941)
      heroRef.current && heroRef.current.style.setProperty('--s', String(sc))
      setS(sc); setMobile(m)
    }
    set()
    window.addEventListener('resize', set)
    return () => window.removeEventListener('resize', set)
  }, [])

  // start the CTA entrance sequence when the card is on screen
  useEffect(() => {
    const el = ctaRef.current
    if (!el) return
    let done = false
    const start = () => { if (!done) { done = true; setInView(true); cleanup() } }
    const check = () => { if (el.getBoundingClientRect().top < window.innerHeight * 0.85) start() }
    const io = typeof IntersectionObserver !== 'undefined' ? new IntersectionObserver(([e]) => e.isIntersecting && start(), { threshold: 0.2 }) : null
    const cleanup = () => { io && io.disconnect(); window.removeEventListener('scroll', check); window.removeEventListener('resize', check) }
    window.addEventListener('scroll', check, { passive: true })
    window.addEventListener('resize', check)
    io && io.observe(el)
    check()
    return cleanup
  }, [])

  const join = (e) => {
    e.preventDefault()
    if (user) return nav('/app')
    nav(`/signup${email.trim() ? `?email=${encodeURIComponent(email.trim())}` : ''}`)
  }
  const goto = user ? '/app' : '/signup'

  return (
    <div className="tr">
      {/* ================= hero ================= */}
      <section className="tz" ref={heroRef}>
        <Sky rim={mobile || !videoOn} s={s} />
        <div className="tz-stage">
          {!mobile && (
            <video className={`tz-video ${videoOn ? 'on' : ''}`} src="/media/violet-glow.mp4" autoPlay muted loop playsInline preload="auto"
              onLoadedData={() => setVideoOn(true)} aria-hidden="true" />
          )}

          <nav className="tz-nav">
            <Link to="/" className="tz-logo"><TrMark size={26} /> Testrion</Link>
            <div className={`tz-menu ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(false)}>
              <a href="#top" className="home">Home</a>
              <a href="#features">Features</a>
              <a href="#how">How it works</a>
              <a href="#tests">Tests</a>
              <a href="#faq">FAQ</a>
            </div>
            <div className="tz-nav-right">
              {!user && <Link to="/login" className="tz-login">Log in</Link>}
              <Link to={goto} className="tr-btn primary">{user ? 'Dashboard' : 'Get Started'}</Link>
            </div>
            <button className="tr-btn tz-menu-btn" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">{menuOpen ? 'Close' : 'Menu'}</button>
          </nav>

          <div className="tz-head" id="top">
            <h1 className="tz-h1">
              <span className="l"><i><span className="tr-grad">Testrion</span> Test Smarter,</i></span>
              <span className="l"><i>Fix Faster, Ship Safer.</i></span>
            </h1>
            <p className="tz-lede">
              Fully integrated testing for machine learning. No manual checks, no silent failures — Testrion tests, gates and repairs{' '}<br />
              your models before they ever reach production.
            </p>
            <div className="tz-cta">
              <Link to={goto} className="tr-btn primary">{user ? 'Open dashboard' : 'Get Started'}</Link>
              <a href="#features" className="tr-btn">Learn More</a>
            </div>
          </div>

          <img className="tz-glow" src="/media/dash-glow.png" alt="" aria-hidden="true" />
          <div className="tz-panel" aria-label="Product preview">
            <aside className="tz-side">
              <div className="tz-side-h"><TrMark size={18} /> Testrion <Settings size={16} /></div>
              <div className="tz-item"><Search size={17} /> Search</div>
              <div className="tz-item on"><LayoutDashboard size={17} /> Dashboard</div>
              <div className="tz-item"><FlaskConical size={17} /> New Test</div>
              <div className="tz-item"><Database size={17} /> Datasets</div>
              <div className="tz-sep" />
              <div className="tz-item"><History size={17} /> Test History</div>
              <div className="tz-item"><GitCompare size={17} /> Compare Runs</div>
              <div className="tz-item"><Settings size={17} /> Settings</div>
              <div className="tz-promo"><b>Testrion Auto-fix</b><p>Repair failed tests and prove the improvement.</p><span className="tz-pill">Try it</span></div>
            </aside>
            <div className="tz-main">
              <div className="tz-top">
                <div className="tz-ico"><Search size={16} /></div><div className="tz-ico"><Bell size={16} /></div><div className="sp" />
                <div className="tz-user"><div className="tz-av">DU</div><div>Demo User<small>sample report</small></div></div>
              </div>
              <div className="tz-grid">
                <div className="tz-card"><div className="tz-lab">Quality score (after auto-fix)</div><div className="tz-val">97.1 <em className="up">+19.2</em></div></div>
                <div className="tz-card"><div className="tz-lab">Tests passed (of 24)</div><div className="tz-val">23 <em className="up">+7</em></div></div>
                <div className="tz-card tz-chart">
                  <div className="tz-lab">Quality score trend</div>
                  <svg viewBox="0 0 520 190" preserveAspectRatio="none">
                    <defs><linearGradient id="tzg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#9312ff" stopOpacity="0.55" /><stop offset="1" stopColor="#9312ff" stopOpacity="0" /></linearGradient></defs>
                    {[40, 80, 120, 160].map((y) => <line key={y} x1="0" x2="520" y1={y} y2={y} stroke="rgba(255,255,255,0.07)" />)}
                    <path d="M0 150 C40 140 60 120 100 125 S160 90 200 96 S270 110 310 70 S400 60 440 36 S500 24 520 18 L520 190 L0 190 Z" fill="url(#tzg)" />
                    <path d="M0 150 C40 140 60 120 100 125 S160 90 200 96 S270 110 310 70 S400 60 440 36 S500 24 520 18" fill="none" stroke="#b24bff" strokeWidth="3" />
                  </svg>
                </div>
                <div className="tz-card tz-cal">
                  <h4>Deployment gate</h4>
                  <div className="tz-lab">Sample report · House Price Prediction</div>
                  <div className="tz-row" style={{ marginTop: 12 }}><span>Hold-out R²</span><b>0.862 <span className="up">+0.109</span></b></div>
                  <div className="tz-row"><span>Edge-case inputs</span><b>100%</b></div>
                  <div className="tz-row"><span>Parity difference</span><b>6.9% <span className="up">&lt; 10%</span></b></div>
                  <div className="tz-row"><span>Connected</span><b>scikit-learn · GitHub Actions</b></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="tr-section">
        <div className="tr-wrap">
          <div className="tr-title"><span className="tr-eyebrow">Features</span><h2>Everything you need to trust a model</h2></div>
          <div className="tr-grid tr-g3">
            {FEATURES.map(([Icon, t, d]) => (
              <div key={t} className="tr-card"><div className="tr-ico"><Icon size={20} /></div><h3>{t}</h3><p>{d}</p></div>
            ))}
          </div>
        </div>
      </section>

      <section id="how" className="tr-section">
        <div className="tr-wrap">
          <div className="tr-title"><span className="tr-eyebrow">How it works</span><h2>From raw data to a verified model in three steps</h2></div>
          <div className="tr-grid tr-g3">
            {STEPS.map(([n, t, d]) => (<div key={n} className="tr-step"><div className="tr-step-n">{n}</div><h3>{t}</h3><p>{d}</p></div>))}
          </div>
        </div>
      </section>

      <section id="tests" className="tr-section">
        <div className="tr-wrap">
          <div className="tr-title"><span className="tr-eyebrow">Test suite</span><h2>Five dimensions of model quality</h2></div>
          <div className="tr-grid tr-g3">
            {DIMENSIONS.map(([Icon, t, d]) => (
              <div key={t} className="tr-card"><div className="tr-ico"><Icon size={19} /></div><h3>{t}</h3><p>{d}</p></div>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="tr-section">
        <div className="tr-wrap">
          <div className="tr-title"><span className="tr-eyebrow">FAQ</span><h2>Questions, answered</h2></div>
          <div className="tr-faq">
            {FAQ.map(([q, a]) => (<details key={q}><summary>{q}</summary><p>{a}</p></details>))}
          </div>
        </div>
      </section>

      {/* ===== signup call-to-action + footer ===== */}
      <section className={`tr-cta ${inView ? 'in' : ''}`} ref={ctaRef}>
        <div className="tr-frame">
          <div className="tr-card-cta">
            <div className="tr-cta-in">
              <h2>Get your Testrion Account</h2>
              <p className="tr-cta-sub">Test your ML models automatically,<br />and fix what fails before it ships.</p>
              <form className="tr-form" onSubmit={join}>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email to get started" aria-label="Email address" />
                <button type="submit">Get Free Access</button>
              </form>
            </div>
          </div>
          <footer className="tr-foot">
            <div className="tr-foot-top">
              <div className="tr-foot-left">
                <TrMark size={30} />
                <p>Test machine-learning models automatically across data quality, robustness, fairness and drift. Block risky releases with a deployment gate, then let Auto-fix repair what fails. Works with any classification or regression CSV.</p>
              </div>
              <div className="tr-foot-right">
                <h4>Contact Us</h4>
                <div>Project Team 52</div>
                <div>Dept. of Computer Science &amp; Engineering,<br />Sai Vidya Institute of Technology,<br />Rajanukunte, Bengaluru 560119</div>
              </div>
            </div>
            <div className="tr-foot-rule" />
            <div className="tr-foot-bot">
              <span>Copyright © Testrion. {new Date().getFullYear()}. All Rights Reserved.</span>
              <span>Major Project Phase-II · Automated testing of ML models</span>
            </div>
          </footer>
        </div>
      </section>
    </div>
  )
}
