import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, Download, Eye, FlaskConical, Trash2, Upload, X } from 'lucide-react'
import { api } from '../api.js'
import { Loading, Page } from '../components/ui.jsx'

export default function Datasets() {
  const nav = useNavigate()
  const [list, setList] = useState(null)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const load = () => api.datasets().then(setList)
  useEffect(() => { load() }, [])

  const upload = async (file) => {
    if (!file) return
    setError('')
    try { await api.upload(file); load() } catch (e) { setError(e.message) }
  }
  const remove = async (d) => {
    if (!confirm(`Delete dataset "${d.name}"?`)) return
    await api.deleteDataset(d.id)
    load()
  }

  if (!list) return <Loading />
  return (
    <Page
      title="Datasets"
      sub="Built-in samples and your uploaded CSV files"
      actions={
        <button className="btn btn-primary" onClick={() => fileRef.current.click()}>
          <Upload size={16} /> Upload CSV
          <input ref={fileRef} type="file" accept=".csv" hidden onChange={(e) => upload(e.target.files[0])} />
        </button>
      }
    >
      {error && <div className="error-box">{error}</div>}
      <div className="card table-wrap">
        <table className="table">
          <thead><tr><th>Name</th><th>Description</th><th>Rows</th><th>Columns</th><th>Source</th><th>Tags</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead>
          <tbody>
            {list.map((d) => (
              <tr key={d.id}>
                <td><div className="row"><Database size={16} color="var(--brand)" /><b>{d.name}</b></div></td>
                <td className="muted" style={{ maxWidth: 320 }}>{d.description}</td>
                <td>{d.rows.toLocaleString()}</td>
                <td>{d.cols}</td>
                <td style={{ maxWidth: 190 }}><span className={`badge ${d.origin === 'real' ? 'pass' : d.origin === 'synthetic' ? 'warn' : 'brand'}`}>{d.origin === 'real' ? 'Real data' : d.origin === 'synthetic' ? 'Synthetic' : 'Your upload'}</span><div className="muted" style={{ fontSize: 11.5, marginTop: 4, lineHeight: 1.35 }}>{d.source}</div></td>
                <td><div className="tags">{d.tags.map((t) => <span key={t} className={`tag ${['Messy', 'Leakage'].includes(t) ? 'messy' : ''}`}>{t}</span>)}</div></td>
                <td>
                  <div className="row" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn" onClick={() => api.preview(d.id).then(setPreview)}><Eye size={14} /> Preview</button>
                    <button className="btn" title="Download as CSV" onClick={() => api.downloadDataset(d.id, d.name).catch((e) => setError(e.message))}><Download size={14} /> CSV</button>
                    <button className="btn btn-primary" onClick={() => nav(`/app/new?dataset=${encodeURIComponent(d.id)}`)}><FlaskConical size={14} /> Test</button>
                    {!d.builtin && <button className="btn btn-danger" onClick={() => remove(d)}><Trash2 size={14} /></button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {preview && (
        <div className="overlay" onClick={() => setPreview(null)}>
          <div className="modal wide" onClick={(e) => e.stopPropagation()}>
            <div className="row" style={{ marginBottom: 16 }}>
              <div>
                <h3>{preview.name}</h3>
                <div className="muted">{preview.rows.toLocaleString()} rows · {preview.cols} columns</div>
              </div>
              <div className="spacer" />
              <button className="btn btn-ghost" onClick={() => setPreview(null)}><X size={18} /></button>
            </div>
            <div className="muted" style={{ marginBottom: 14, fontSize: 13 }}>Source: <b>{preview.source}</b></div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Data dictionary</div>
            <div className="preview-scroll" style={{ marginBottom: 18, maxHeight: 300 }}>
              <table>
                <thead><tr><th>Column</th><th>Type</th><th>Unique</th><th>Missing</th><th>Meaning</th></tr></thead>
                <tbody>
                  {preview.columns.map((c) => (
                    <tr key={c.name}>
                      <td><b>{c.name}</b></td><td>{c.dtype}</td><td>{c.unique}</td>
                      <td style={c.missing ? { color: 'var(--fail)' } : {}}>{c.missing || '—'}</td>
                      <td style={{ whiteSpace: 'normal', minWidth: 260 }}>{c.doc || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>First rows</div>
            <div className="preview-scroll">
              <table>
                <thead><tr>{preview.head_columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                <tbody>{preview.head.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} style={v === null ? { color: 'var(--fail)' } : {}}>{v === null ? 'NaN' : String(v).slice(0, 20)}</td>)}</tr>)}</tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
