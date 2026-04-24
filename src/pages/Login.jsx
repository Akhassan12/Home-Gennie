import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { supabase } from '../services/supabase'

const PHOTO = 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=1400'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState('')   // 'email' | 'google' | ''
  const [error, setError]       = useState('')
  const [message, setMessage]   = useState('')
  const [isForgot, setIsForgot] = useState(false)
  const { signIn, signInWithGoogle } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading('email')
    try {
      const { error: err } = await signIn(email, password)
      if (err) throw err
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Sign-in failed. Please try again.')
    } finally {
      setLoading('')
    }
  }

  const handleGoogle = async () => {
    setError('')
    setLoading('google')
    try {
      const { error: err } = await signInWithGoogle()
      if (err) throw err
    } catch (err) {
      setError(err.message || 'Google sign-in failed.')
      setLoading('')
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    if (!email) {
      setError('Please enter your email address to reset password.')
      return
    }
    setError('')
    setMessage('')
    setLoading('email')
    try {
      const { error: err } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/update-password',
      })
      if (err) throw err
      setMessage('Password reset email sent! Check your inbox.')
    } catch (err) {
      setError(err.message || 'Failed to send password reset email.')
    } finally {
      setLoading('')
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100%', overflow: 'hidden' }}>

      {/* ── LEFT: Editorial Photo ── */}
      <div style={{ flex: '0 0 50%', position: 'relative', overflow: 'hidden' }}>
        <img
          src={PHOTO}
          alt="Interior design inspiration"
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
        {/* Bottom scrim + quote */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          background: 'linear-gradient(to top, rgba(0,0,0,0.65) 0%, transparent 60%)',
          padding: '2.5rem',
        }}>
          <p style={{
            fontFamily: '"Noto Serif", Georgia, serif',
            fontStyle: 'italic',
            fontSize: '1rem',
            color: 'rgba(255,255,255,0.9)',
            lineHeight: 1.6,
            margin: 0,
          }}>
            "Design is intelligence made <em>visible</em>."
          </p>
        </div>
      </div>

      {/* ── RIGHT: Auth Form ── */}
      <div style={{
        flex: '0 0 50%',
        background: '#fbf9f6',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem',
        overflowY: 'auto',
      }}>
        <div style={{ width: '100%', maxWidth: '380px' }}>

          {/* Brand */}
          <p style={{
            fontFamily: '"Noto Serif", Georgia, serif',
            fontWeight: 700,
            fontSize: '1.05rem',
            letterSpacing: '0.04em',
            color: '#1b1c1a',
            marginBottom: '2.5rem',
          }}>
            Home Gennie
          </p>

          {/* Headline */}
          <h1 style={{
            fontFamily: '"Noto Serif", Georgia, serif',
            fontWeight: 700,
            fontSize: 'clamp(2rem, 3.5vw, 2.75rem)',
            letterSpacing: '-0.02em',
            color: '#1b1c1a',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}>
            {isForgot ? 'Reset password' : <>Welcome <em style={{ fontStyle: 'italic', fontWeight: 400 }}>back</em>.</>}
          </h1>
          <p style={{ fontFamily: 'Inter, sans-serif', color: '#6b5c4c', fontSize: '0.95rem', marginBottom: '2.5rem' }}>
            {isForgot ? 'Enter your email to receive a secure reset link.' : 'Sign in to your design studio.'}
          </p>

          {/* Feedback */}
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

          {/* Form */}
          <form onSubmit={isForgot ? handleResetPassword : handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

            {/* Email */}
            <div>
              <label style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#54433e', display: 'block', marginBottom: '0.5rem' }}>
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="name@studio.com"
                required
                style={{
                  width: '100%', padding: '0.875rem 1rem',
                  background: '#f5f3f0', border: 'none', outline: 'none',
                  borderRadius: '10px', fontFamily: 'Inter, sans-serif',
                  fontSize: '0.9375rem', color: '#1b1c1a', boxSizing: 'border-box',
                  transition: 'background 0.2s',
                }}
                onFocus={e => e.target.style.background = '#eae8e5'}
                onBlur={e => e.target.style.background = '#f5f3f0'}
              />
            </div>

            {/* Password */}
            {!isForgot && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <label style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#54433e' }}>
                    Password
                  </label>
                  <button type="button" onClick={() => { setIsForgot(true); setError(''); setMessage(''); }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'Inter, sans-serif', fontSize: '0.75rem', color: '#884530', textDecoration: 'none', letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: 600 }}>
                    Forgot?
                  </button>
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%', padding: '0.875rem 1rem',
                    background: '#f5f3f0', border: 'none', outline: 'none',
                    borderRadius: '10px', fontFamily: 'Inter, sans-serif',
                    fontSize: '0.9375rem', color: '#1b1c1a', boxSizing: 'border-box',
                    transition: 'background 0.2s',
                  }}
                  onFocus={e => e.target.style.background = '#eae8e5'}
                  onBlur={e => e.target.style.background = '#f5f3f0'}
                />
              </div>
            )}

            {/* Google */}
            {!isForgot && (
              <button
                type="button"
                onClick={handleGoogle}
                disabled={!!loading}
                style={{
                  width: '100%', padding: '0.875rem 1rem',
                  background: '#ffffff', border: '1.5px solid #d9c1bb',
                  borderRadius: '9999px', fontFamily: 'Inter, sans-serif',
                  fontSize: '0.9375rem', fontWeight: 500, color: '#1b1c1a',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.625rem',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.background = '#f5f3f0' }}
                onMouseLeave={e => e.currentTarget.style.background = '#ffffff'}
              >
                {/* Google icon */}
                <svg width="18" height="18" viewBox="0 0 18 18"><path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/><path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/><path fill="#FBBC05" d="M3.964 10.706c-.18-.54-.282-1.117-.282-1.706s.102-1.166.282-1.706V4.962H.957C.347 6.175 0 7.55 0 9s.348 2.825.957 4.038l3.007-2.332z"/><path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.962L3.964 7.294C4.672 5.167 6.656 3.58 9 3.58z"/></svg>
                {loading === 'google' ? 'Signing in…' : 'Continue with Google'}
              </button>
            )}

            {/* CTAs */}
            <button
              type="submit"
              disabled={!!loading}
              style={{
                width: '100%', padding: '0.95rem 1rem',
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
              {loading === 'email' ? 'Please wait…' : isForgot ? 'Send reset link' : 'Sign In'}
            </button>
          </form>

          {isForgot && (
            <p style={{ textAlign: 'center', marginTop: '1.5rem', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', color: '#54433e' }}>
              <button type="button" onClick={() => { setIsForgot(false); setError(''); setMessage(''); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#884530', fontWeight: 600, textDecoration: 'none' }}>
                ← Back to sign in
              </button>
            </p>
          )}

          {/* Sign-up link */}
          {!isForgot && (
            <p style={{ textAlign: 'center', marginTop: '1.75rem', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', color: '#54433e' }}>
              No account?{' '}
              <Link to="/signup" style={{ color: '#884530', fontWeight: 600, textDecoration: 'none' }}>
                Create one →
              </Link>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
