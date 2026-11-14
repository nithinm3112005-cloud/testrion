import { CheckCircle2, MessageSquareQuote, Play, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Page } from '../components/ui.jsx'

const PITCH = [
  'Our project is Automated Software Testing and Problem Solving of Machine Learning Models. Its aim is to test ML models automatically — the way we test software — and to fix the problems we find.',
  'A trained model can pass its own accuracy check and still fail in production: it crashes on missing values, behaves badly on unusual inputs, treats groups unequally, or drifts as data changes. Ordinary unit tests do not catch these failures.',
  'Testrion runs up to 24 automated tests — data quality, performance, robustness with edge-case and adversarial inputs, reliability, and fairness with data-slice testing. A deployment gate then approves or blocks the release: hold-out accuracy (R² for regression) at least 85%, demographic parity difference below 10%.',
  'When a model is blocked, the Auto-fix engine repairs the data pipeline, tunes the model, searches better algorithms and re-runs every test to prove the improvement. The same checks run in GitHub Actions on every push, and a live monitor watches predictions for drift.',
  'Our demonstration uses house-price prediction, but the framework is domain-agnostic: it works on any classification or regression CSV.',
]

const DEMO = [
  ['Dashboard → One-click demo', 'Linear Regression on the house-price data is tested, auto-fixed and re-tested live.'],
  ['Show the gate', 'Before: “Deployment blocked” (R² below 0.85, crashes on null inputs). After: “Deployment approved”.'],
  ['Open “What was fixed”', 'Imputation, de-duplication, log-target, scaling, tuning, model switch — each with its reason.'],
  ['Open Test results', 'Expand Edge-case inputs, Adversarial perturbation, Data-slice performance and Fairness for real evidence.'],
  ['Model performance tab', 'Actual-vs-predicted table and scatter, residuals, per-region slices.'],
  ['Live monitoring tab', 'Press “Simulate drifted traffic” → DRIFT DETECTED in milliseconds.'],
  ['Requirements page', 'Every slide requirement mapped to the feature, with measured benchmark numbers.'],
]

const QA = [
  ['What is the main objective?', 'To automate the testing and evaluation of ML models, find failures (accuracy drops, edge cases, bias, drift) and stop models that fail predefined checks from being deployed — and to repair what can be repaired automatically.'],
  ['Why is traditional software testing not enough for ML?', 'Code can run perfectly while the model is wrong. Model quality depends on data and learned patterns, so it changes with new data, drift, bias and unexpected inputs. Unit tests check code, not predictions.'],
  ['Does the system automatically correct a defective model?', 'Yes. The Auto-fix module diagnoses failed tests and applies repairs (imputation, de-duplication, leakage and protected-attribute removal, scaling, class balancing, log-transform, tuning, model search), then re-runs the whole suite. Example: house prices 75 → 97, blocked → approved.'],
  ['Why R² and not accuracy for house prices?', 'Accuracy is a classification metric. For regression we apply the 85% rule as hold-out R² ≥ 0.85 and also report MAE, RMSE and % error. For classification models the gate uses accuracy ≥ 85% plus a worst-class recall check, because accuracy alone hides weak classes on imbalanced data.'],
  ['How do you prevent test-set leakage?', '75% train / 25% hold-out test. Validation is cross-validation inside the 75%; tuning and model search use only that. The test split is used only for the final report. The exported model is re-trained on all rows after evaluation.'],
  ['How is fairness defined and measured?', 'Demographic parity difference: classification — largest gap in predicted-class rate between groups; regression — |mean prediction − mean actual| per group. Protected columns (gender, age, region …) are auto-detected or chosen by the user; the limit is 10%. Demographic parity alone does not prove a model is fair — it is one criterion.'],
  ['What is data drift and how do you detect it?', 'A change in incoming data compared with training data. We log every prediction and compute the Population Stability Index per feature (<0.10 stable, 0.10–0.25 warning, >0.25 drift). Measured verdict time: about 11 ms after 200 predictions.'],
  ['What does GitHub Actions do here?', 'On every push or pull request it runs the pytest suite and the deployment gate (ci_check.py). If the gate is blocked the script exits non-zero, so the pipeline fails before deployment.'],
  ['Why model.pkl?', 'It stores the trained pipeline (preprocessing + model) so it can be loaded and used for predictions without retraining: pickle.load(open("model-run1.pkl","rb")).'],
  ['What did you measure for the non-functional requirements?', '1,000,000 records through the full 24-test suite in 22 s (Ridge); 100 models tested concurrently in 41 s (9.6× faster than sequential); drift verdict in 11 ms; dashboard bundle transfer 13 ms. Measured on one 10-core Mac — see backend/EVIDENCE.md.'],
  ['Can it support different ML algorithms?', 'Yes — 6 classifiers and 6 regressors are registered, and any scikit-learn-style estimator can be added to the registry; every model goes through the same tests and gate.'],
  ['What is the real-world contribution?', 'Earlier detection of model weaknesses, less manual testing, visibility into bias, and a repeatable release gate for ML — useful wherever models drive decisions (finance, retail, manufacturing…).'],
]

const LIMITS = [
  'Testing detects specified risks; it cannot guarantee every prediction is correct or remove all bias.',
  'Synthetic sample datasets are used for the demo; results on real data will differ.',
  'Benchmark numbers come from one machine; the 1M-record figure is for a linear model, and tree ensembles are slower. The interactive app caps a run at 6,000 rows.',
  'Healthcare, vehicles and other domains are potential applications only — nothing domain-specific is implemented.',
  'The GitHub Actions workflow and the Dockerfile are provided but have not been executed on GitHub / Docker from this machine.',
]

export default function Viva() {
  return (
    <Page title="Viva & presentation guide" sub="A script, a demo order and answers that match what this application really does"
      actions={<Link to="/app" className="btn btn-primary"><Play size={16} /> Start the demo</Link>}>
      <div className="card card-pad">
        <div className="row" style={{ marginBottom: 12 }}><MessageSquareQuote size={20} color="var(--brand)" /><div className="card-title">One-minute explanation</div></div>
        {PITCH.map((p, i) => <p key={i} style={{ margin: '0 0 10px', lineHeight: 1.65 }}>{p}</p>)}
        <div className="callout fix"><b>Key point:</b> this is not just a house-price app. House-price prediction is the demonstration use case — the project is the framework that tests ML models.</div>
      </div>

      <div className="card card-pad mt">
        <div className="card-title" style={{ marginBottom: 14 }}>Demo order (about 5 minutes)</div>
        <div className="timeline">
          {DEMO.map(([t, d], i) => (
            <div key={t} className="tl-item"><div className="tl-dot">{i + 1}</div><div><div className="tl-title">{t}</div><div className="tl-why">{d}</div></div></div>
          ))}
        </div>
      </div>

      <div className="card mt">
        <div className="card-head" style={{ paddingBottom: 6 }}><div className="card-title">Likely questions & answers</div></div>
        <div style={{ padding: '6px 22px 18px' }}>
          {QA.map(([q, a]) => (
            <details key={q} className="qa"><summary>{q}</summary><p>{a}</p></details>
          ))}
        </div>
      </div>

      <div className="card card-pad mt" style={{ borderColor: 'rgba(242,169,59,0.35)', background: 'rgba(242,169,59,0.07)' }}>
        <div className="row" style={{ marginBottom: 10 }}><ShieldAlert size={20} color="var(--warn)" /><div className="card-title">Be upfront about these limits</div></div>
        <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.7 }}>{LIMITS.map((l) => <li key={l}>{l}</li>)}</ul>
        <div className="muted" style={{ marginTop: 10, fontSize: 12.5 }}><CheckCircle2 size={13} style={{ verticalAlign: -2 }} /> Saying these first makes the rest of your answers more credible.</div>
      </div>
    </Page>
  )
}
