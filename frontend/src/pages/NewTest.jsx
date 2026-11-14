import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Check, CheckCircle2, ChevronDown, Layers, Loader2, Play, SlidersHorizontal, Upload } from 'lucide-react'
import { api } from '../api.js'
import { Loading, Page } from '../components/ui.jsx'

const STAGES = [
  'Validating dataset',
  'Training the model',
  'Running data-quality & performance tests',
  'Stress-testing robustness (noise, missing data, metamorphic)',
  'Checking reliability, fairness & building the report',
]

export default function NewTest() {
  const [params] = useSearchParams()
  const nav = useNavigate()
  const [step, setStep] = useState(1)
  const [datasets, setDatasets] = useState(null)
  const [models, setModels] = useState([])
  const [datasetId, setDatasetId] = useState(params.get('dataset') || '')
  const [preview, setPreview] = useState(null)
  const [target, setTarget] = useState('')
  const [model, setModel] = useState(params.get('model') || 'random_forest')
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)
  const [stage, setStage] = useState(0)
  const [over, setOver] = useState(false)
  const [showAdv, setShowAdv] = useState(false)
  const [adv, setAdv] = useState({ impute: false, scale: 'none', balance: '', dedupe: false, drop_constant: false, log_target: false, protected: [] })
  const col = preview?.columns.find((c) => c.name === target)
  const task = col?.task || 'classification'
  const taskModels = models.filter((m) => m.task === task)
  useEffect(() => {
    if (taskModels.length && !taskModels.some((m) => m.id === model)) setModel(task === 'regression' ? 'random_forest_reg' : 'random_forest')
  }, [task, models])
  const togglePro = (n) => setAdv((a) => ({ ...a, protected: a.protected.includes(n) ? a.protected.filter((x) => x !== n) : [...a.protected, n] }))
  const benchmark = async () => {
    setError(''); setRunning(true); setStage(0)
    const timer = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 1100)
    try {
      const r = await api.batch({ dataset_id: datasetId, target, config: { ...adv, balance: adv.balance || null } })
      clearInterval(timer)
      const ids = r.runs.filter((x) => x.id).map((x) => x.id).join(',')
      nav(`/app/leaderboard?ids=${ids}&t=${r.elapsed_sec}&seq=${r.sequential_sec}&sp=${r.speedup}`)
    } catch (e) { clearInterval(timer); setRunning(false); setError(e.message) }
  }
  const go = (n) => { setError(''); setStep(n) }
  const fileRef = useRef()

  const loadDatasets = () => api.datasets().then(setDatasets)
  useEffect(() => {
    loadDatasets()
    api.models().then(setModels)
  }, [])

  // when a dataset is picked, load its preview
  useEffect(() => {
    if (!datasetId) return
    setPreview(null)
    api.preview(datasetId).then((p) => {
      setPreview(p)
      setTarget(p.suggested_target || (p.columns.find((c) => c.suitable) || {}).name || '')
    }).catch((e) => setError(e.message))
  }, [datasetId])

  // jump straight to step 2 when launched from a demo card
  useEffect(() => {
    if (params.get('dataset') && datasets) go(2)
  }, [datasets])

  const upload = async (file) => {
    if (!file) return
    setError('')
    try {
      const d = await api.upload(file)
      await loadDatasets()
      setDatasetId(d.id)
    } catch (e) {
      setError(e.message)
    }
  }

  const run = async () => {
    setError('')
    setRunning(true)
    setStage(0)
    const timer = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 900)
    try {
      const r = await api.createRun({ dataset_id: datasetId, target, model, config: { ...adv, balance: adv.balance || null } })
      clearInterval(timer)
      setStage(STAGES.length)
      setTimeout(() => nav(`/app/runs/${r.id}`), 350)
    } catch (e) {
      clearInterval(timer)
      setRunning(false)
      setError(e.message)
    }
  }

  if (!datasets) return <Loading />
  const labels = ['Dataset', 'Target & data', 'Model']

  return (
    <Page title="New test" sub="Configure a run in three quick steps">
      <div className="steps">
        {labels.map((l, i) => (
          <div key={l} className="row">
            <div className={`step ${step === i + 1 ? 'active' : step > i + 1 ? 'done' : ''}`}>
              <div className="step-dot">{step > i + 1 ? <Check size={15} /> : i + 1}</div>
              {l}
            </div>
            {i < 2 && <div className="step-line" />}
          </div>
        ))}
      </div>

      {error && <div className="error-box">{error}</div>}

      {step === 1 && (
        <>
          <div className="grid g3">
            {datasets.map((d) => (
              <button key={d.id} className={`choice ${datasetId === d.id ? 'selected' : ''}`} onClick={() => setDatasetId(d.id)}>
                {datasetId === d.id && <CheckCircle2 className="choice-check" size={20} />}
                <div className="choice-title">{d.name}</div>
                <div className="choice-desc">{d.description}</div>
                <div className="tags">
                  {d.tags.map((t) => (
                    <span key={t} className={`tag ${['Messy', 'Leakage'].includes(t) ? 'messy' : ''}`}>{t}</span>
                  ))}
                </div>
                <div className="muted" style={{ fontSize: 12 }}>{d.rows.toLocaleString()} rows · {d.cols} columns</div>
              </button>
            ))}
            <div
              className={`drop ${over ? 'over' : ''}`}
              onClick={() => fileRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setOver(true) }}
              onDragLeave={() => setOver(false)}
              onDrop={(e) => { e.preventDefault(); setOver(false); upload(e.dataTransfer.files[0]) }}
            >
              <Upload size={26} />
              <div style={{ fontWeight: 700, marginTop: 8 }}>Upload your CSV</div>
              <div style={{ fontSize: 12.5 }}>Drag & drop or click to browse (max 10 MB)</div>
              <input ref={fileRef} type="file" accept=".csv" hidden onChange={(e) => upload(e.target.files[0])} />
            </div>
          </div>
          <div className="row mt-lg">
            <div className="spacer" />
            <button className="btn btn-primary btn-lg" disabled={!datasetId} onClick={() => go(2)}>
              Continue <ArrowRight size={16} />
            </button>
          </div>
        </>
      )}

      {step === 2 && (
        <>
          {!preview ? <Loading text="Reading dataset…" /> : (
            <div className="card card-pad">
              <div className="row" style={{ marginBottom: 6 }}>
                <div>
                  <div className="card-title">{preview.name}</div>
                  <div className="card-sub">{preview.rows.toLocaleString()} rows · {preview.cols} columns</div>
                </div>
              </div>
              <div style={{ margin: '18px 0 8px', fontWeight: 600 }}>Which column should the model predict?</div>
              <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>Pick a label to classify (2–30 categories) or a numeric value to estimate, like price (regression). Other columns are greyed out.</div>
              <div className="chips" style={{ gap: 8 }}>
                {preview.columns.map((c) => (
                  <button key={c.name} disabled={!c.suitable}
                    title={c.suitable ? `${c.unique} classes` : `${c.unique} distinct values - not a usable classification target`}
                    className={`col-pill ${target === c.name ? 'selected' : ''} ${c.suitable ? '' : 'disabled'}`} onClick={() => setTarget(c.name)}>
                    {c.name} <small>{c.task === 'regression' ? 'numeric · regression' : c.suitable ? `${c.unique} classes` : c.dtype}{c.missing ? ` · ${c.missing} missing` : ''}</small>
                  </button>
                ))}
              </div>
              <div style={{ margin: '22px 0 8px', fontWeight: 600 }}>Data preview</div>
              <div className="preview-scroll">
                <table>
                  <thead><tr>{preview.head_columns.map((c) => <th key={c} style={c === target ? { color: 'var(--brand)' } : {}}>{c}{c === target ? ' (target)' : ''}</th>)}</tr></thead>
                  <tbody>
                    {preview.head.map((r, i) => (
                      <tr key={i}>{r.map((v, j) => <td key={j} style={v === null ? { color: 'var(--fail)' } : {}}>{v === null ? 'NaN' : String(v).slice(0, 18)}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          <div className="row mt-lg">
            <button className="btn btn-lg" onClick={() => go(1)}><ArrowLeft size={16} /> Back</button>
            <div className="spacer" />
            <button className="btn btn-primary btn-lg" disabled={!preview || !target} onClick={() => go(3)}>
              Continue <ArrowRight size={16} />
            </button>
          </div>
        </>
      )}

      {step === 3 && (
        <>
          <div style={{ marginBottom: 12, fontWeight: 600 }}>Choose the model to test <span className="badge brand" style={{ marginLeft: 8 }}>{task} task</span></div>
          <div className="grid g3">
            {taskModels.map((m) => (
              <button key={m.id} className={`choice ${model === m.id ? 'selected' : ''}`} onClick={() => setModel(m.id)}>
                {model === m.id && <CheckCircle2 className="choice-check" size={20} />}
                <div className="choice-title">{m.label}</div>
                <div className="choice-desc">{m.description}</div>
              </button>
            ))}
          </div>
          <div className="card mt-lg">
            <button className="adv-toggle" onClick={() => setShowAdv(!showAdv)}>
              <SlidersHorizontal size={16} /> <b>Advanced pipeline options</b>
              <span className="muted">· optional — leave off to see what the tests uncover</span>
              <span className="spacer" /><ChevronDown size={18} className={`chev ${showAdv ? 'open' : ''}`} />
            </button>
            {showAdv && (
              <div className="grid g3" style={{ padding: '4px 22px 22px' }}>
                {[['impute', 'Impute missing values'], ['dedupe', 'Remove duplicate rows'], ['drop_constant', 'Drop constant columns'], ...(task === 'regression' ? [['log_target', 'Log-transform the target']] : [])].map(([k, l]) => (
                  <label key={k} className="switch-row">
                    <input type="checkbox" checked={adv[k]} onChange={(e) => setAdv({ ...adv, [k]: e.target.checked })} /> {l}
                  </label>
                ))}
                <div style={{ gridColumn: '1 / -1' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Protected attributes to audit for fairness <span className="muted" style={{ fontWeight: 400 }}>(gender, age, region… are detected automatically)</span></div>
                  <div className="chips">
                    {preview?.columns.filter((c) => c.name !== target).map((c) => (
                      <button key={c.name} type="button" className={`chip ${adv.protected.includes(c.name) ? 'active' : ''}`} onClick={() => togglePro(c.name)}>{c.name}</button>
                    ))}
                  </div>
                </div>
                <label className="field" style={{ margin: 0 }}>Feature scaling
                  <select className="select" value={adv.scale} onChange={(e) => setAdv({ ...adv, scale: e.target.value })}>
                    <option value="none">None</option><option value="standard">Standardisation</option><option value="robust">Robust (median / IQR)</option>
                  </select>
                </label>
                {task === 'classification' && <label className="field" style={{ margin: 0 }}>Class balancing
                  <select className="select" value={adv.balance} onChange={(e) => setAdv({ ...adv, balance: e.target.value })}>
                    <option value="">None</option><option value="class_weight">Class weights</option><option value="oversample">Random oversampling</option>
                  </select>
                </label>}
              </div>
            )}
          </div>
          <div className="card card-pad mt row" style={{ background: 'var(--brand-50)', borderColor: 'var(--brand-100)' }}>
            <div>
              <b>Ready to run</b>
              <div className="muted">
                {preview?.name} · target <b>{target}</b> · {models.find((m) => m.id === model)?.label}
              </div>
            </div>
          </div>
          <div className="row mt-lg">
            <button className="btn btn-lg" onClick={() => go(2)}><ArrowLeft size={16} /> Back</button>
            <div className="spacer" />
            <button className="btn btn-lg" onClick={benchmark} title="Test every model for this task at the same time"><Layers size={16} /> Benchmark all {taskModels.length} models in parallel</button>
            <button className="btn btn-primary btn-lg" onClick={run}><Play size={16} /> Run automated tests</button>
          </div>
        </>
      )}

      {running && (
        <div className="overlay">
          <div className="modal" style={{ textAlign: 'center' }}>
            <div className="spinner" />
            <h3>Testing your model…</h3>
            <div className="muted">This usually takes a few seconds.</div>
            <div className="run-steps">
              {STAGES.map((s, i) => (
                <div key={s} className={`run-step ${i < stage ? 'done' : i === stage ? 'on' : ''}`}>
                  {i < stage ? <CheckCircle2 size={16} /> : i === stage ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <span style={{ width: 16 }} />}
                  {s}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
