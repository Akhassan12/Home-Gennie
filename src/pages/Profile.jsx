import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { supabase } from '../services/supabase'
import { User, Mail, Save, AlertCircle, ArrowLeft, ChevronDown, Palette, LogOut, Key } from 'lucide-react'

const T = {
  bg:        '#fbf9f6',
  surface:   '#ffffff',
  container: '#efeeeb',
  low:       '#f5f3f0',
  text:      '#1b1c1a',
  muted:     '#54433e',
  primary:   '#884530',
  secondary: '#6b5c4c',
}

export default function Profile() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const dropdownRef = useRef(null)
  
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [dropdownOpen, setDropdown] = useState(false)

  const username  = user?.user_metadata?.display_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'
  const initials  = username.slice(0, 2).toUpperCase()
  const userEmail = user?.email || ''

  const handleSignOut = async () => {
    setDropdown(false)
    await signOut()
    navigate('/login')
  }

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  useEffect(() => {
    if (user) {
      setName(user.user_metadata?.display_name || user.user_metadata?.full_name || '')
      setEmail(user.email || '')
    }
  }, [user])

  const handleUpdate = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    
    try {
      const { data, error: err } = await supabase.auth.updateUser({
        data: { display_name: name, full_name: name }
      })
      
      if (err) throw err
      setMessage('Profile updated successfully!')
    } catch (err) {
      setError(err.message || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    width: '100%', padding: '0.875rem 1rem',
    background: '#f5f3f0', border: 'none', outline: 'none',
    borderRadius: '10px', fontFamily: 'Inter, sans-serif',
    fontSize: '0.9375rem', color: '#1b1c1a', boxSizing: 'border-box',
    transition: 'background 0.2s',
  }

  const labelStyle = {
    fontFamily: 'Inter, sans-serif', fontSize: '0.75rem', fontWeight: 600,
    letterSpacing: '0.08em', textTransform: 'uppercase', color: '#54433e',
    display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem',
  }

  const handleResetPassword = async () => {
    if (!email) return
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/update-password',
      })
      if (error) throw error
      setMessage('Password reset email sent! Check your inbox.')
    } catch (err) {
      setError(err.message || 'Failed to send reset email.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: T.bg, paddingBottom: '3rem' }}>
      {/* ── Top Nav ── */}
      <nav style={{
        background: T.surface, boxShadow: '0 1px 20px rgba(27,28,26,0.06)',
        position: 'sticky', top: 0, zIndex: 100,
        height: '72px', display: 'flex', alignItems: 'center',
        padding: '0 2.5rem', gap: '2rem', marginBottom: '3rem'
      }}>
        <span style={{ fontFamily: '"Noto Serif", Georgia, serif', fontWeight: 700, fontSize: '1.1rem', color: T.text, letterSpacing: '0.02em', flexShrink: 0 }}>
          Home Gennie
        </span>

        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '2rem' }}>
          {[['Dashboard','/dashboard'],['Create','/upload'],['Gallery','/gallery'],['3D Viewer','/viewer']].map(([label, to]) => (
            <Link key={to} to={to} style={{
              fontFamily: 'Inter, sans-serif', fontSize: '0.875rem',
              color: location.pathname === to ? T.primary : T.muted,
              textDecoration: 'none',
              fontWeight: location.pathname === to ? 600 : 400,
              transition: 'color 0.15s',
            }}>
              {label}
            </Link>
          ))}
        </div>

        <div ref={dropdownRef} style={{ position: 'relative', flexShrink: 0 }}>
          <button
            onClick={() => setDropdown(prev => !prev)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              background: T.low, padding: '0.35rem 0.75rem 0.35rem 0.35rem',
              borderRadius: '9999px', border: 'none', cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = T.container}
            onMouseLeave={e => { if (!dropdownOpen) e.currentTarget.style.background = T.low }}
          >
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #884530, #A65D46)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: '0.7rem', fontWeight: 700, flexShrink: 0,
            }}>
              {initials}
            </div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: T.text, maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {username}
            </span>
            <ChevronDown size={14} style={{ color: T.muted, transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
          </button>

          {dropdownOpen && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 10px)', right: 0,
              background: T.surface, borderRadius: '14px',
              boxShadow: '0 8px 32px rgba(27,28,26,0.12)',
              minWidth: '220px', overflow: 'hidden',
              animation: 'fadeInDown 0.15s ease',
              zIndex: 200,
            }}>
              <div style={{ padding: '1rem 1.25rem', background: T.low }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                  <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'linear-gradient(135deg, #884530, #A65D46)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>
                    {initials}
                  </div>
                  <div style={{ overflow: 'hidden' }}>
                    <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: 700, color: T.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</p>
                    <p style={{ margin: 0, fontSize: '0.75rem', color: T.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{userEmail}</p>
                  </div>
                </div>
              </div>

              <div style={{ padding: '0.5rem' }}>
                <button
                  onClick={() => { setDropdown(false); navigate('/profile') }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.625rem 0.875rem', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '0.875rem', color: T.text, fontWeight: 500, transition: 'background 0.15s', textAlign: 'left' }}
                  onMouseEnter={e => e.currentTarget.style.background = T.low}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <User size={16} style={{ color: T.muted }} /> My Profile
                </button>

                <button
                  onClick={() => { setDropdown(false); navigate('/gallery') }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.625rem 0.875rem', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '0.875rem', color: T.text, fontWeight: 500, transition: 'background 0.15s', textAlign: 'left' }}
                  onMouseEnter={e => e.currentTarget.style.background = T.low}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <Palette size={16} style={{ color: T.muted }} /> My Designs
                </button>

                <div style={{ height: '1px', background: T.container, margin: '0.375rem 0.875rem' }} />

                <button
                  id="signout-button"
                  onClick={handleSignOut}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.625rem 0.875rem', borderRadius: '8px', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '0.875rem', color: '#ba1a1a', fontWeight: 600, transition: 'background 0.15s', textAlign: 'left' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#ffdad6'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <LogOut size={16} /> Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </nav>

      <div style={{ maxWidth: '600px', margin: '0 auto', padding: '0 2rem' }}>
        
        <button 
          onClick={() => navigate(-1)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'transparent', border: 'none', color: T.muted, cursor: 'pointer', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', fontWeight: 600, marginBottom: '2rem' }}
        >
          <ArrowLeft size={16} /> Back
        </button>

        <h1 style={{ fontFamily: '"Noto Serif", Georgia, serif', fontWeight: 700, fontSize: '2.5rem', color: T.text, margin: '0 0 0.5rem', lineHeight: 1.1 }}>
          Your <em style={{ fontStyle: 'italic', fontWeight: 400 }}>Profile</em>
        </h1>
        <p style={{ fontFamily: 'Inter, sans-serif', color: T.secondary, fontSize: '1rem', marginBottom: '2.5rem' }}>
          Manage your personal details and studio identity.
        </p>

        <div style={{ background: T.surface, padding: '2.5rem', borderRadius: '24px', boxShadow: '0 8px 32px rgba(27,28,26,0.06)' }}>
          
          {error && (
            <div style={{ background: '#ffdad6', color: '#93000a', padding: '1rem', borderRadius: '12px', fontSize: '0.875rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', fontFamily: 'Inter, sans-serif' }}>
              <AlertCircle size={18} /> {error}
            </div>
          )}
          
          {message && (
            <div style={{ background: '#d3f9d8', color: '#2b8a3e', padding: '1rem', borderRadius: '12px', fontSize: '0.875rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', fontFamily: 'Inter, sans-serif' }}>
              <Save size={18} /> {message}
            </div>
          )}

          <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            <div>
              <label style={labelStyle}><User size={14} /> Display Name</label>
              <input 
                type="text" 
                value={name} 
                onChange={e => setName(e.target.value)} 
                placeholder="Your studio name" 
                required 
                style={inputStyle}
                onFocus={e => e.target.style.background = '#eae8e5'} 
                onBlur={e => e.target.style.background = '#f5f3f0'} 
              />
            </div>

            <div>
              <label style={labelStyle}><Mail size={14} /> Email Address</label>
              <input 
                type="email" 
                value={email} 
                disabled 
                style={{ ...inputStyle, opacity: 0.6, cursor: 'not-allowed' }}
                title="Email cannot be changed directly."
              />
              <p style={{ fontSize: '0.75rem', color: T.muted, marginTop: '8px', fontFamily: 'Inter, sans-serif' }}>
                Contact support if you need to change your email address.
              </p>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              style={{ 
                marginTop: '1rem', width: '100%', padding: '1rem',
                background: loading ? '#b07060' : 'linear-gradient(135deg, #884530, #A65D46)', 
                border: 'none', borderRadius: '12px', 
                fontFamily: 'Inter, sans-serif', fontSize: '0.9375rem', fontWeight: 600, color: '#ffffff',
                cursor: loading ? 'not-allowed' : 'pointer', transition: 'transform 0.2s ease, box-shadow 0.2s ease', 
                boxShadow: '0 4px 20px rgba(136,69,48,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
              }}
              onMouseEnter={e => { if (!loading) { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.boxShadow = '0 6px 28px rgba(136,69,48,0.35)' } }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(136,69,48,0.25)' }}
            >
              <Save size={18} /> {loading ? 'Saving...' : 'Save Profile'}
            </button>
          </form>

          <div style={{ height: '1px', background: T.container, margin: '2rem 0' }} />

          <div>
            <h3 style={{ fontFamily: 'Inter, sans-serif', fontSize: '1.05rem', fontWeight: 700, color: '#1b1c1a', marginBottom: '0.5rem' }}>Security</h3>
            <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.85rem', color: '#54433e', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              Need a new password? We will send a secure link to your registered email address allowing you to reset it safely.
            </p>
            <button
              onClick={handleResetPassword}
              disabled={loading}
              style={{
                width: '100%', padding: '0.875rem',
                background: 'transparent', border: '1.5px solid #dcdacb', borderRadius: '12px',
                fontFamily: 'Inter, sans-serif', fontSize: '0.9rem', fontWeight: 600, color: '#1b1c1a',
                cursor: loading ? 'not-allowed' : 'pointer', transition: 'background 0.2s ease, border-color 0.2s ease',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
              }}
              onMouseEnter={e => { if (!loading) { e.currentTarget.style.background = '#f5f3f0'; e.currentTarget.style.borderColor = '#c6c4b5' } }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = '#dcdacb' }}
            >
              <Key size={16} style={{ color: '#54433e' }} /> Request Password Reset
            </button>
          </div>

        </div>
      </div>
      {/* Dropdown fade-in animation */}
      <style>{`
        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
