import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { BookOpen, ClipboardCheck, GraduationCap, Database, FlaskConical, GitCompare, History, LayoutDashboard, LogOut, ShieldCheck } from 'lucide-react'
import { useAuth } from './auth.jsx'
import { Loading } from './components/ui.jsx'
import Landing from './pages/Landing.jsx'
import AuthPage from './pages/AuthPage.jsx'
import Dashboard from './pages/Dashboard.jsx'
import NewTest from './pages/NewTest.jsx'
import Datasets from './pages/Datasets.jsx'
import HistoryPage from './pages/History.jsx'
import Report from './pages/Report.jsx'
import Compare from './pages/Compare.jsx'
import HowItWorks from './pages/HowItWorks.jsx'
import Leaderboard from './pages/Leaderboard.jsx'
import Requirements from './pages/Requirements.jsx'
import Viva from './pages/Viva.jsx'

const links = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/new', label: 'New Test', icon: FlaskConical },
  { to: '/app/datasets', label: 'Datasets', icon: Database },
  { to: '/app/history', label: 'Test History', icon: History },
  { to: '/app/compare', label: 'Compare Runs', icon: GitCompare },
]

function Shell() {
  const { user, loading, logout } = useAuth()
  const nav = useNavigate()
  if (loading) return <Loading />
  if (!user) return <Navigate to="/login" replace />
  const initials = user.name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand" style={{ cursor: 'pointer' }} onClick={() => nav('/')}>
          <div className="brand-logo"><ShieldCheck size={21} /></div>
          <div>
            <div className="brand-name">Testrion</div>
            <div className="brand-sub">Automated ML testing</div>
          </div>
        </div>
        <nav className="nav">
          <div className="nav-label" style={{ paddingTop: 0 }}>Workspace</div>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}><l.icon size={18} /> {l.label}</NavLink>
          ))}
          <div className="nav-label">Learn</div>
          <NavLink to="/app/requirements"><ClipboardCheck size={18} /> Requirements</NavLink>
          <NavLink to="/app/viva"><GraduationCap size={18} /> Viva guide</NavLink>
          <NavLink to="/app/how-it-works"><BookOpen size={18} /> How it works</NavLink>
        </nav>
        <div className="user-card">
          <div className="avatar">{initials}</div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div className="user-name">{user.name}</div>
            <div className="user-mail">{user.email}</div>
          </div>
          <button className="icon-btn" title="Log out" onClick={async () => { await logout(); nav('/') }}><LogOut size={17} /></button>
        </div>
      </aside>
      <main className="main"><Outlet /></main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/signup" element={<AuthPage mode="signup" />} />
      <Route path="/app" element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="new" element={<NewTest />} />
        <Route path="datasets" element={<Datasets />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="compare" element={<Compare />} />
        <Route path="leaderboard" element={<Leaderboard />} />
        <Route path="requirements" element={<Requirements />} />
        <Route path="viva" element={<Viva />} />
        <Route path="runs/:id" element={<Report />} />
        <Route path="how-it-works" element={<HowItWorks />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
