import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './services/auth'
import { useState, useEffect, createContext, useContext } from 'react'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Gallery from './pages/Gallery'
import Viewer3D from './pages/Viewer3D'
import Profile from './pages/Profile'
import UpdatePassword from './pages/UpdatePassword'

/* ── Theme Context ─────────────────────────────────────────── */
export const ThemeContext = createContext({ theme: 'light', toggleTheme: () => {} })
export const useTheme = () => useContext(ThemeContext)

function ThemeProvider({ children }) {
  // Always default to light — user can toggle to dark, which persists.
  // But stale localStorage dark values from dev sessions are ignored on first load.
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    const saved = localStorage.getItem('homegennie-theme')
    if (saved) setTheme(saved)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('homegennie-theme', theme) } catch {}
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/upload"    element={<ProtectedRoute><Upload /></ProtectedRoute>} />
      <Route path="/gallery"   element={<ProtectedRoute><Gallery /></ProtectedRoute>} />
      <Route path="/viewer"    element={<Viewer3D />} />
      <Route path="/profile"   element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/update-password" element={<UpdatePassword />} />
    </Routes>
  )
}

// Pages that own their own nav — skip the global Navbar/Footer for them
const SELF_NAV_ROUTES = ['/', '/login', '/signup', '/dashboard', '/upload', '/gallery', '/viewer', '/profile', '/update-password']

function AppContent() {
  const { loading } = useAuth()
  const location = useLocation()
  const isSelfNav = SELF_NAV_ROUTES.includes(location.pathname)

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000000' }}>
        <div style={{ width: '40px', height: '40px', border: '2px solid #ffffff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen" style={{ background: 'var(--bg-page)', color: 'var(--text-primary)' }}>
      {!isSelfNav && <Navbar />}
      <main className={`flex-1 ${isSelfNav ? '' : 'mt-20'}`}>
        <AppRoutes />
      </main>
      {!isSelfNav && <Footer />}
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  )
}
