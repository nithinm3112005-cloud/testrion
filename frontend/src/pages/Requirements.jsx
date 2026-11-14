import { CheckCircle2, CircleDot } from 'lucide-react'
import { Page } from '../components/ui.jsx'

// Traceability matrix: every item of the Stage-1 presentation mapped to its implementation.
const SECTIONS = [
  ['Functional requirements (FR-1 · slide 7)', [
    ['Edge-case generation: out-of-distribution, min/max, null, special-character inputs', 'done',
     'Robustness → “Edge-case inputs (generated)”. Builds min, max, zero, 10× out-of-range, null, unseen-category, empty and special-character inputs and counts crashes.', 'Report → Test results'],
    ['Adversarial test generation', 'done',
     'Robustness → “Adversarial perturbation”. Searches 8 worst-case perturbations per row for prediction flips.', 'Report → Test results'],
    ['Data-slice testing: gender-wise, age-wise, region-wise', 'done',
     'Fairness & Slices → “Data-slice performance”. Gender / age (3 bands) / region columns are auto-detected; slice charts per group.', 'Report → Model performance'],
    ['Accuracy < 85% on the test set ⇒ deployment fails', 'done',
     'Deployment gate banner: accuracy (R² for regression) must be ≥ 85%, otherwise the release is BLOCKED. The CI job exits non-zero.', 'Top of every report'],
    ['Fairness: demographic parity difference < 10% for protected groups', 'done',
     'Fairness & Slices → “Demographic parity difference”. Part of the gate. Protected columns are auto-detected or chosen under Advanced options.', 'Report → Test results'],
  ]],
  ['Non-functional requirements (slide 8)', [
    ['Test-execution speed: 1M records, full suite < 15 min', 'done',
     'Measured: the full 24-test suite on 1,000,000 records took 22 s with Ridge Regression (10-core Mac). Tree ensembles are slower per row, and the interactive app caps runs at 6,000 rows. Evidence: backend/EVIDENCE.md.', 'backend/evidence.py'],
    ['Monitoring latency: drift detection < 5 s from real-time predictions', 'done',
     'Every prediction is logged and drift (PSI per feature) is recomputed on demand. Measured: DRIFT DETECTED 11 ms after 200 live predictions. “Under 5” is interpreted as 5 seconds.', 'Report → Live monitoring'],
    ['Dashboard load time < 3 s (Grafana / Evidently style)', 'done',
     'Built-in React dashboard (replaces Grafana / Evidently). Measured: page + bundles in 13 ms over localhost; the browser load time is also shown live on the Dashboard.', 'Dashboard'],
    ['Scalability: 100 models tested in parallel', 'done',
     'Measured: 100 model runs (full test-suite each) completed concurrently in 41 s, 9.6× faster than one-by-one. The app’s “Benchmark all models” button uses the same engine.', 'New Test → Benchmark all models'],
  ]],
  ['Methodology & implementation (slides 10–13)', [
    ['Data collection and preprocessing: house-price dataset', 'done',
     'Built-in “House Price Prediction” regression dataset (with missing values, duplicates and outliers) plus CSV upload; cleaning is automated by Auto-fix.', 'Datasets'],
    ['Train the ML model and save it as MODEL.PKL', 'done', 'The “Model” button downloads the trained pipeline as a standard Python pickle (model-run<N>.pkl), loadable with pickle.load.', 'Report → Model'],
    ['Test the trained model using automated test cases', 'done', 'Up to 24 automated tests per run (data, performance, robustness, reliability, fairness & slices).', 'New Test'],
    ['CI/CD: automatically run tests whenever code is pushed (GitHub Actions)', 'done',
     '.github/workflows/ml-tests.yml runs the pytest suite and the deployment gate (ci_check.py) on every push / pull request. Verified locally; the workflow itself runs once pushed to GitHub.', 'Repository'],
    ['Compare actual and predicted values', 'done', 'Actual-vs-predicted comparison table, scatter plot and residual histogram.', 'Report → Model performance'],
    ['GUI to enter data and view prediction + testing results', 'done',
     'React web app: “Try the model” playground for inputs and predictions, and full test reports. (Streamlit is replaced by React; a Streamlit version is also provided.)', 'Report → Try the model'],
    ['Problem solving: detect and fix issues (project title)', 'done', 'Auto-fix repairs data, tunes hyper-parameters, searches better models and re-verifies every test.', 'Report → Auto-fix'],
    ['Test set never used for training or validation; validation set used to tune (slide 12)', 'done',
     '75% train / 25% hold-out test. Validation is cross-validation inside the training 75%; tuning and model search use only that. The test split is used only for the final report.', 'Report → Configuration'],
  ]],
  ['Clarifications from the project explanation document (section 9)', [
    ['Regression vs classification accuracy', 'done',
     'Accuracy is not used for house prices. The 85% rule is applied as hold-out R² ≥ 0.85 for regression; MAE, RMSE and % error are also reported.', 'Report → Model performance'],
    ['Fairness criterion defined precisely', 'done',
     'Classification: largest gap in predicted-class rate between groups. Regression: |mean prediction − mean actual| per group. Limit 10%. The report notes that demographic parity alone does not prove fairness.', 'Report → Test results'],
    ['Evidence for every test type', 'done', 'backend/EVIDENCE.md lists real edge-case, adversarial, slice, fairness and gate results (regenerate with python evidence.py).', 'backend/EVIDENCE.md'],
    ['Testing vs automatic problem solving', 'done', 'An automatic repair module exists and is demonstrated with before/after results — it is not only a detector.', 'Report → Auto-fix report'],
    ['Dataset: house prices vs Iris', 'note',
     'Both are built in. The slides’ reference page names Iris while the method uses house prices — update the slide to name the House Price dataset (synthetic) to stay consistent.', 'Datasets'],
    ['Domain applications (healthcare, banking, vehicles…)', 'note',
     'These are potential uses only. The tool is domain-agnostic (any CSV), and no healthcare-specific feature is implemented or claimed.', '—'],
  ]],
]

export default function Requirements() {
  const all = SECTIONS.flatMap((s) => s[1])
  const scored = all.filter((r) => r[1] !== 'note')
  const done = scored.filter((r) => r[1] === 'done').length
  return (
    <Page title="Requirements coverage" sub="Traceability from the Stage-1 project presentation to what is implemented in this application">
      <div className="card card-pad row" style={{ gap: 28, flexWrap: 'wrap', marginBottom: 20 }}>
        <div><div className="stat-value">{done}/{scored.length}</div><div className="stat-label">items fully implemented</div></div>
        <div className="muted" style={{ flex: 1, minWidth: 260 }}>
          Every requirement is implemented, and the performance targets (1M records, 100 models, drift &lt; 5 s, dashboard &lt; 3 s) were
          <b> measured</b> — see <b>backend/EVIDENCE.md</b>. Numbers are from one 10-core Mac and will differ on other machines.
        </div>
      </div>
      {SECTIONS.map(([title, items]) => (
        <div key={title} className="card mt table-wrap">
          <div className="cat-head"><div className="cat-name">{title}</div></div>
          <table className="table">
            <thead><tr><th>Requirement</th><th>Status</th><th>How it is implemented</th><th>Where to see it</th></tr></thead>
            <tbody>
              {items.map(([req, st, how, where]) => (
                <tr key={req}>
                  <td style={{ width: '28%' }}><b>{req}</b></td>
                  <td className="req-status">
                    {st === 'done' ? <span className="badge pass"><CheckCircle2 size={13} /> Implemented</span> : st === 'note' ? <span className="badge gray"><CircleDot size={13} /> Note</span> : <span className="badge warn"><CircleDot size={13} /> Partial</span>}
                  </td>
                  <td className="muted" style={{ fontSize: 13 }}>{how}</td>
                  <td style={{ width: 170 }}><span className="badge brand">{where}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </Page>
  )
}
