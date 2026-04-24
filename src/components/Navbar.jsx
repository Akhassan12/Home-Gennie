import { useState, useRef, useEffect } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { useTheme } from '../App'
import {
  Menu, X, Sparkles, LogOut, Moon, Sun,
  LayoutDashboard, Upload, Image, Box, ChevronDown, Settings
} from 'lucide-react'

export default function Navbar() {
  const [mobileOpen, setMobileOpen]   = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const { user, signOut } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const userMenuRef = useRef(null)

  const username  = user?.user_metadata?.display_name || user?.email?.split('@')[0] || 'User'
  const initials  = username.slice(0, 2).toUpperCase()
  const userEmail = user?.email || ''

  const handleLogout = async () => {
    await signOut()
    navigate('/')
    setMobileOpen(false)
    setUserMenuOpen(false)
  }

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const navLinks = user
    ? [
        { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/upload',    label: 'Create',    icon: Upload },
        { to: '/gallery',   label: 'Gallery',   icon: Image },
        { to: '/viewer',    label: '3D Viewer', icon: Box },
      ]
    : []

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-[1000]"
      style={{
        background: 'var(--bg-nav)',
        backdropFilter: 'blur(28px)',
        WebkitBackdropFilter: 'blur(28px)',
        borderBottom: '1px solid var(--border-color)',
        boxShadow: '0 2px 20px rgba(0,0,0,0.06)',
      }}
    >
      <div
        className="flex items-center justify-between gap-6"
        style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 2.5rem', height: '72px' }}
      >

        {/* ── Logo ── */}
        <Link to="/" className="flex items-center gap-3 shrink-0 group" style={{ textDecoration: 'none' }}>
          <div
            className="w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
            style={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%)',
              boxShadow: '0 4px 16px rgba(79,70,229,0.35)',
            }}
          >
            <Sparkles size={18} className="text-white" />
          </div>
          <div className="flex flex-col leading-none">
            <span
              className="font-display font-extrabold tracking-tight"
              style={{ fontSize: '1.15rem', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}
            >
              Home<span style={{ color: 'var(--color-primary-500)' }}>Gennie</span>
            </span>
            <span
              className="font-bold tracking-widest"
              style={{ fontSize: '0.5rem', color: 'var(--text-faint)', letterSpacing: '0.18em' }}
            >
              PRO STUDIO
            </span>
          </div>
        </Link>

        {/* ── Desktop Nav Links ── */}
        {user && (
          <div
            className="hidden md:flex items-center rounded-2xl p-1 gap-0.5"
            style={{
              background: 'var(--bg-subtle)',
              border: '1.5px solid var(--border-color)',
            }}
          >
            {navLinks.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '0.55rem 1rem',
                  borderRadius: '14px',
                  fontSize: '0.83rem',
                  fontWeight: 600,
                  letterSpacing: '0.01em',
                  textDecoration: 'none',
                  transition: 'all 0.18s ease',
                  color: isActive ? 'var(--color-primary-600)' : 'var(--text-muted)',
                  background: isActive
                    ? theme === 'dark'
                      ? 'rgba(99,102,241,0.18)'
                      : '#ffffff'
                    : 'transparent',
                  boxShadow: isActive
                    ? theme === 'dark'
                      ? '0 2px 8px rgba(99,102,241,0.2)'
                      : '0 2px 12px rgba(0,0,0,0.08)'
                    : 'none',
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      size={14}
                      style={{ color: isActive ? 'var(--color-primary-500)' : 'var(--text-faint)', flexShrink: 0 }}
                    />
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        )}

        {/* ── Right Controls ── */}
        <div className="hidden md:flex items-center gap-2 shrink-0">

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            className="flex items-center justify-center transition-all duration-200"
            style={{
              width: '40px', height: '40px', borderRadius: '14px',
              background: 'var(--bg-subtle)',
              border: '1.5px solid var(--border-color)',
              color: 'var(--text-muted)',
              cursor: 'pointer',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.color = 'var(--color-primary-500)'
              e.currentTarget.style.borderColor = 'var(--color-primary-300)'
              e.currentTarget.style.background = 'rgba(99,102,241,0.06)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.color = 'var(--text-muted)'
              e.currentTarget.style.borderColor = 'var(--border-color)'
              e.currentTarget.style.background = 'var(--bg-subtle)'
            }}
          >
            {theme === 'light'
              ? <Moon size={16} strokeWidth={2} />
              : <Sun  size={16} strokeWidth={2} />
            }
          </button>

          {/* ── User Dropdown or Auth Buttons ── */}
          {user ? (
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(prev => !prev)}
                className="flex items-center gap-2.5 transition-all duration-200"
                style={{
                  padding: '0.45rem 0.75rem 0.45rem 0.45rem',
                  borderRadius: '16px',
                  background: 'var(--bg-subtle)',
                  border: '1.5px solid var(--border-color)',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--color-primary-300)'
                  e.currentTarget.style.background = 'rgba(99,102,241,0.06)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-color)'
                  e.currentTarget.style.background = 'var(--bg-subtle)'
                }}
              >
                {/* Avatar */}
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center text-white font-extrabold text-xs shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5, #ec4899)',
                    boxShadow: '0 2px 8px rgba(79,70,229,0.3)',
                    letterSpacing: '0.05em',
                  }}
                >
                  {initials}
                </div>

                <div className="flex flex-col items-start leading-none" style={{ maxWidth: '100px' }}>
                  <span className="font-bold text-xs truncate w-full" style={{ color: 'var(--text-primary)' }}>
                    {username}
                  </span>
                  <span className="text-[10px] mt-0.5" style={{ color: 'var(--text-faint)' }}>Online</span>
                </div>

                {/* Online dot */}
                <div className="w-2 h-2 rounded-full" style={{ background: '#10b981', boxShadow: '0 0 6px rgba(16,185,129,0.6)' }} />

                <ChevronDown
                  size={13}
                  style={{
                    color: 'var(--text-faint)',
                    transform: userMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s ease',
                  }}
                />
              </button>

              {/* Dropdown */}
              {userMenuOpen && (
                <div
                  className="absolute right-0 top-[calc(100%+10px)] rounded-2xl overflow-hidden"
                  style={{
                    minWidth: '220px',
                    background: 'var(--bg-card)',
                    border: '1.5px solid var(--border-color)',
                    boxShadow: '0 16px 48px rgba(0,0,0,0.16), 0 4px 12px rgba(0,0,0,0.08)',
                    animation: 'fadeInUp 0.18s ease-out',
                  }}
                >
                  {/* Email header */}
                  <div style={{ padding: '1rem 1.25rem 0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                    <p className="text-xs font-bold mb-0.5" style={{ color: 'var(--text-primary)' }}>{username}</p>
                    <p className="text-[11px] truncate" style={{ color: 'var(--text-faint)' }}>{userEmail}</p>
                  </div>

                  {/* Menu items */}
                  <div style={{ padding: '0.5rem' }}>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 rounded-xl text-sm font-semibold transition-all"
                      style={{ padding: '0.75rem 1rem', color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.07)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <LogOut size={15} />
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="font-semibold transition-all"
                style={{
                  padding: '0.55rem 1.1rem',
                  borderRadius: '14px',
                  fontSize: '0.83rem',
                  color: 'var(--text-secondary)',
                  border: '1.5px solid var(--border-color)',
                  background: 'var(--bg-subtle)',
                  textDecoration: 'none',
                }}
              >
                Log in
              </Link>
              <Link
                to="/signup"
                className="btn-primary"
                style={{ padding: '0.55rem 1.3rem', fontSize: '0.83rem', borderRadius: '14px' }}
              >
                Get Started
              </Link>
            </div>
          )}
        </div>

        {/* ── Mobile: Theme + Hamburger ── */}
        <div className="md:hidden flex items-center gap-2">
          <button
            onClick={toggleTheme}
            style={{
              width: '38px', height: '38px', borderRadius: '12px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--bg-subtle)', border: '1.5px solid var(--border-color)',
              color: 'var(--text-muted)', cursor: 'pointer',
            }}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{
              width: '38px', height: '38px', borderRadius: '12px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--bg-subtle)', border: '1.5px solid var(--border-color)',
              color: 'var(--text-muted)', cursor: 'pointer',
            }}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* ── Mobile Menu ── */}
      <div
        className="md:hidden overflow-hidden transition-all duration-300 ease-in-out"
        style={{
          maxHeight: mobileOpen ? '600px' : '0px',
          opacity: mobileOpen ? 1 : 0,
          borderBottom: mobileOpen ? '1px solid var(--border-color)' : 'none',
        }}
      >
        <div style={{ padding: '1.25rem 1.5rem 1.5rem', background: 'var(--bg-nav)' }}>
          {navLinks.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className="flex items-center gap-3 rounded-xl font-semibold transition-all"
              style={({ isActive }) => ({
                padding: '0.85rem 1rem', marginBottom: '4px',
                fontSize: '0.875rem', textDecoration: 'none', display: 'flex',
                color: isActive ? 'var(--color-primary-600)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(99,102,241,0.08)' : 'transparent',
              })}
            >
              {({ isActive }) => (
                <>
                  <Icon size={17} style={{ color: isActive ? 'var(--color-primary-500)' : 'var(--text-faint)' }} />
                  {label}
                </>
              )}
            </NavLink>
          ))}

          <div style={{ height: '1px', background: 'var(--border-color)', margin: '0.75rem 0' }} />

          {user ? (
            <div>
              <div
                className="flex items-center gap-3 rounded-2xl"
                style={{ padding: '0.85rem 1rem', background: 'var(--bg-subtle)', marginBottom: '8px' }}
              >
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-extrabold text-xs shrink-0"
                  style={{ background: 'linear-gradient(135deg, #4f46e5, #ec4899)' }}
                >
                  {initials}
                </div>
                <div>
                  <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{username}</p>
                  <p className="text-[11px]" style={{ color: 'var(--text-faint)' }}>{userEmail}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 rounded-xl font-semibold"
                style={{
                  padding: '0.85rem', fontSize: '0.875rem',
                  color: '#ef4444', background: 'rgba(239,68,68,0.06)',
                  border: '1px solid rgba(239,68,68,0.15)', cursor: 'pointer',
                }}
              >
                <LogOut size={16} /> Sign out
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <Link to="/login" onClick={() => setMobileOpen(false)} className="btn-secondary text-center"
                style={{ padding: '0.75rem', fontSize: '0.875rem' }}>Log in</Link>
              <Link to="/signup" onClick={() => setMobileOpen(false)} className="btn-primary text-center"
                style={{ padding: '0.75rem', fontSize: '0.875rem' }}>Join Free</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
