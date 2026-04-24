import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'

export default function UpdatePassword() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    // Check if we have an active session (from the recovery link)
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        setError('No active recovery session found. Please request a new password reset link.')
      }
    })
  }, [])

  const handleUpdate = async (e) => {
    e.preventDefault()
    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    
    setError('')
    setMessage('')
    setLoading(true)

    try {
      const { error: err } = await supabase.auth.updateUser({ password })
      if (err) throw err
      
      setMessage('Password updated successfully! Redirecting...')
      setTimeout(() => navigate('/dashboard'), 2000)
    } catch (err) {
      setError(err.message || 'Failed to update password.')
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
    display: 'block', marginBottom: '0.5rem',
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100%', overflow: 'hidden', background: '#fbf9f6', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ width: '100%', maxWidth: '400px', padding: '3rem' }}>
        <p style={{
          fontFamily: '"Noto Serif", Georgia, serif',
          fontWeight: 700,
          fontSize: '1.05rem',
          letterSpacing: '0.04em',
          color: '#1b1c1a',
          marginBottom: '2.5rem',
          textAlign: 'center'
        }}>
          Home Gennie
        </p>

        <h1 style={{
          fontFamily: '"Noto Serif", Georgia, serif',
          fontWeight: 700,
          fontSize: '2.25rem',
          letterSpacing: '-0.02em',
          color: '#1b1c1a',
          margin: '0 0 0.5rem',
          lineHeight: 1.1,
          textAlign: 'center'
        }}>
          Set new password
        </h1>
        <p style={{ fontFamily: 'Inter, sans-serif', color: '#6b5c4c', fontSize: '0.95rem', marginBottom: '2.5rem', textAlign: 'center' }}>
          Please construct a strong password below.
        </p>

        {error && (
          <div style={{ background: '#ffdad6', color: '#93000a', padding: '0.75rem 1rem', borderRadius: '10px', fontSize: '0.875rem', marginBottom: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
            {error}
          </div>
        )}
        
        {message && (
          <div style={{ background: '#d3f9d8', color: '#2b8a3e', padding: '0.75rem 1rem', borderRadius: '10px', fontSize: '0.875rem', marginBottom: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
            {message}
          </div>
        )}

        <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>New Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={inputStyle}
              onFocus={e => e.target.style.background = '#eae8e5'}
              onBlur={e => e.target.style.background = '#f5f3f0'}
            />
          </div>

          <div>
            <label style={labelStyle}>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={inputStyle}
              onFocus={e => e.target.style.background = '#eae8e5'}
              onBlur={e => e.target.style.background = '#f5f3f0'}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '0.95rem 1rem', marginTop: '0.5rem',
              background: loading ? '#b07060' : 'linear-gradient(135deg, #884530, #A65D46)',
              border: 'none', borderRadius: '9999px',
              fontFamily: 'Inter, sans-serif', fontSize: '0.9375rem',
              fontWeight: 600, color: '#ffffff',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease',
              boxShadow: '0 4px 20px rgba(136,69,48,0.25)',
            }}
            onMouseEnter={e => { if (!loading) { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.boxShadow = '0 6px 28px rgba(136,69,48,0.35)' } }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(136,69,48,0.25)' }}
          >
            {loading ? 'Updating…' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
