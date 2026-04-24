import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { UploadCloud, CheckCircle, Circle, Clock, ArrowRight, Sparkles } from 'lucide-react'
import { useAuth } from '../services/auth'
import { supabase } from '../services/supabase'
import { generateDesign } from '../services/api'

const T = { bg: '#fbf9f6', surface: '#ffffff', container: '#efeeeb', low: '#f5f3f0', text: '#1b1c1a', muted: '#54433e', primary: '#884530', secondary: '#6b5c4c', outline: '#d9c1bb' }

const ROOM_TYPES   = ['Living Room','Bedroom','Kitchen','Dining','Bathroom','Office']
const STYLES       = ['Modern','Minimalist','Classic','Industrial','Bohemian','Scandinavian']
const PALETTES     = [
  { name: 'Natural Earth',  swatches: ['#c4a882','#8c6e52','#6d4c41','#3e2723'] },
  { name: 'Ocean Breeze',   swatches: ['#b2dfdb','#80cbc4','#26a69a','#004d40'] },
  { name: 'Urban Grey',     swatches: ['#f5f5f5','#bdbdbd','#757575','#212121'] },
  { name: 'Blush Rose',     swatches: ['#f8bbd0','#f48fb1','#e91e63','#880e4f'] },
]
const BUDGET_LABELS = ['Budget','Standard','Premium','Luxury']

export default function Upload() {
  const { user }   = useAuth()
  const navigate   = useNavigate()
  const fileRef    = useRef()

  const [file, setFile]           = useState(null)
  const [preview, setPreview]     = useState(null)
  const [roomType, setRoomType]   = useState('')
  const [style, setStyle]         = useState('')
  const [palette, setPalette]     = useState('')
  const [budget, setBudget]       = useState(1)     // 0‒3
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')
  const [dragging, setDragging]   = useState(false)
  const [isMobile, setIsMobile]   = useState(window.innerWidth < 900)
  const location = useLocation()

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleFile = (f) => {
    if (!f || !f.type.startsWith('image/')) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const steps = [
    { label: 'Room Photo Uploaded',    done: !!file       },
    { label: 'Style Parameters Set',   done: !!style      },
    { label: 'Color Palette Selected', done: !!palette    },
    { label: 'AI Generation',          done: false        },
  ]
  const readyToGenerate = !!file && !!roomType && !!style && !!palette

  const handleGenerate = async () => {
    if (!readyToGenerate) { setError('Please complete all steps first.'); return }
    setLoading(true); setError('')
    try {
      const ext  = file.name.split('.').pop()
      const path = `${user.id}/${Date.now()}.${ext}`
      const { error: upErr } = await supabase.storage.from('uploads').upload(path, file)
      if (upErr) throw upErr
      const { data: { publicUrl } } = supabase.storage.from('uploads').getPublicUrl(path)
      
      // Send to FastAPI backend for Generation and DB Insertion
      // The backend returns immediately since it processes in the background
      await generateDesign({
        userId: user.id,
        originalImageUrl: publicUrl,
        roomType: roomType,
        style: style,
      })
      
      // Navigate to gallery immediately where the user can see the "Generating..." placeholder
      setTimeout(() => navigate('/gallery'), 400)
    } catch (e) {
      setError(e.message || 'Generation failed.'); setLoading(false)
    }
  }

  const ChipBtn = ({ label, active, onClick }) => (
    <button onClick={onClick} style={{ padding: '0.5rem 1.25rem', borderRadius: '9999px', border: 'none', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer', background: active ? T.primary : T.container, color: active ? '#ffffff' : T.muted, transition: 'all 0.18s ease' }}>
      {label}
    </button>
  )

  const Section = ({ title, children }) => (
    <div style={{ background: T.surface, borderRadius: '16px', padding: '1.75rem', boxShadow: '0 2px 16px rgba(27,28,26,0.04)', marginBottom: '1.25rem' }}>
      <h3 style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.muted, margin: '0 0 1.25rem' }}>{title}</h3>
      {children}
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: T.bg, fontFamily: 'Inter, sans-serif' }}>

      {/* Nav */}
      <nav style={{ background: T.surface, boxShadow: '0 1px 20px rgba(27,28,26,0.06)', position: 'sticky', top: 0, zIndex: 50, height: '72px', display: 'flex', alignItems: 'center', padding: '0 2.5rem', gap: '2rem' }}>
        <Link to="/dashboard" style={{ fontFamily: '"Noto Serif",Georgia,serif', fontWeight: 700, fontSize: '1.1rem', color: T.text, textDecoration: 'none' }}>Home Gennie</Link>
        <div style={{ flex: 1, display: isMobile ? 'none' : 'flex', justifyContent: 'center', gap: '2rem' }}>
          {[['Dashboard','/dashboard'],['Create','/upload'],['Gallery','/gallery'],['3D Viewer','/viewer']].map(([l,to]) => (
            <Link key={to} to={to} style={{ fontSize: '0.875rem', color: location.pathname === to ? T.primary : T.muted, textDecoration: 'none', fontWeight: location.pathname === to ? 600 : 400 }}>{l}</Link>
          ))}
        </div>
      </nav>

      {/* Page Header */}
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: isMobile ? '2rem 1.5rem 0' : '3rem 2.5rem 0' }}>
        <h1 style={{ fontFamily: '"Noto Serif",Georgia,serif', fontSize: 'clamp(2rem,4vw,3rem)', fontWeight: 700, color: T.text, margin: '0 0 0.5rem', lineHeight: 1.1 }}>
          Design Your Room with <em style={{ color: T.primary, fontStyle: 'italic', fontWeight: 400 }}>AI</em>
        </h1>
        <p style={{ color: T.muted, fontSize: '1.0rem', marginBottom: '2.5rem', lineHeight: 1.6 }}>
          Transform your living spaces into architectural masterpieces using our high-fidelity generative engine.
        </p>
      </div>

      {/* Two-column Body */}
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: isMobile ? '1.5rem 1.5rem 5rem' : '0 2.5rem 5rem', display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 360px', gap: '1.75rem', alignItems: 'start' }}>

        {/* ── LEFT: Wizard ── */}
        <div>
          {/* Step 1 — Upload */}
          <Section title="Step 1 — Upload Room Photo">
            <div
              onClick={() => fileRef.current.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
              style={{ border: `2px dashed ${dragging ? T.primary : T.outline}`, borderRadius: '14px', padding: '3rem 2rem', textAlign: 'center', cursor: 'pointer', background: dragging ? '#fff4f1' : T.low, transition: 'all 0.2s' }}
            >
              {preview ? (
                <img src={preview} alt="Preview" style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '10px', objectFit: 'cover' }} />
              ) : (
                <>
                  <UploadCloud size={40} style={{ color: T.outline, marginBottom: '1rem' }} />
                  <p style={{ fontSize: '1rem', fontWeight: 600, color: T.text, margin: '0 0 0.4rem' }}>Drop your room photo here</p>
                  <p style={{ fontSize: '0.85rem', color: T.muted, margin: 0 }}>or <span style={{ color: T.primary, fontWeight: 600 }}>Browse files</span> — JPG, PNG, WEBP</p>
                </>
              )}
              <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
            </div>
          </Section>

          {/* Step 2 — Room Type */}
          <Section title="Step 2 — Room Type">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.625rem' }}>
              {ROOM_TYPES.map(r => <ChipBtn key={r} label={r} active={roomType === r} onClick={() => setRoomType(r)} />)}
            </div>
          </Section>

          {/* Step 3 — Style */}
          <Section title="Step 3 — Design Style">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.625rem' }}>
              {STYLES.map(s => (
                <button key={s} onClick={() => setStyle(s)} style={{ padding: '0.5rem 1.25rem', borderRadius: '9999px', border: 'none', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer', background: style === s ? '#f4dfcb' : T.container, color: style === s ? T.secondary : T.muted, transition: 'all 0.18s ease' }}>
                  {s}
                </button>
              ))}
            </div>
          </Section>

          {/* Step 4 — Palette */}
          <Section title="Step 4 — Color Palette">
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: '1rem' }}>
              {PALETTES.map(p => (
                <div key={p.name} onClick={() => setPalette(p.name)} style={{ cursor: 'pointer', borderRadius: '12px', overflow: 'hidden', border: `2px solid ${palette === p.name ? T.primary : 'transparent'}`, transition: 'all 0.2s', boxShadow: palette === p.name ? '0 0 0 2px #88453040' : 'none' }}>
                  <div style={{ display: 'flex' }}>
                    {p.swatches.map((c, i) => <div key={i} style={{ flex: 1, height: '48px', background: c }} />)}
                  </div>
                  <p style={{ margin: 0, padding: '0.625rem 0.75rem', fontSize: '0.78rem', fontWeight: 600, color: T.muted, background: T.surface }}>{p.name}</p>
                </div>
              ))}
            </div>
          </Section>

          {/* Step 5 — Budget */}
          <Section title="Step 5 — Budget Range">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              {BUDGET_LABELS.map((l, i) => <span key={i} style={{ fontSize: '0.78rem', fontWeight: budget === i ? 700 : 400, color: budget === i ? T.primary : T.muted }}>{l}</span>)}
            </div>
            <input type="range" min={0} max={3} step={1} value={budget} onChange={e => setBudget(+e.target.value)}
              style={{ width: '100%', accentColor: T.primary, cursor: 'pointer', height: '4px' }} />
          </Section>

          {error && <p style={{ color: '#ba1a1a', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', marginTop: '0.5rem' }}>{error}</p>}
        </div>

        {/* ── RIGHT: Sticky Plan Card ── */}
        <div style={{ position: isMobile ? 'relative' : 'sticky', top: isMobile ? 0 : '90px' }}>
          <div style={{ background: T.surface, borderRadius: '20px', padding: '2rem', boxShadow: '0 4px 32px rgba(27,28,26,0.08)' }}>
            <h2 style={{ fontFamily: '"Noto Serif",Georgia,serif', fontSize: '1.35rem', fontWeight: 700, color: T.text, margin: '0 0 1.75rem' }}>Your Design Plan</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
              {steps.map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {s.done
                    ? <CheckCircle size={20} style={{ color: '#10b981', flexShrink: 0 }} />
                    : i === 3
                      ? <Clock size={20} style={{ color: T.outline, flexShrink: 0 }} />
                      : <Circle size={20} style={{ color: T.outline, flexShrink: 0 }} />
                  }
                  <span style={{ fontSize: '0.9rem', fontWeight: s.done ? 600 : 400, color: s.done ? T.text : T.muted }}>{s.label}</span>
                </div>
              ))}
            </div>
            {readyToGenerate && (
              <p style={{ fontSize: '0.8rem', color: T.muted, marginBottom: '1.25rem', fontStyle: 'italic' }}>
                Estimated processing: ~45 seconds
              </p>
            )}
            <button onClick={handleGenerate} disabled={loading || !readyToGenerate}
              style={{ width: '100%', padding: '1rem', background: readyToGenerate ? 'linear-gradient(135deg,#884530,#A65D46)' : T.container, border: 'none', borderRadius: '9999px', fontFamily: 'Inter, sans-serif', fontSize: '0.95rem', fontWeight: 700, color: readyToGenerate ? '#ffffff' : T.muted, cursor: readyToGenerate ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', boxShadow: readyToGenerate ? '0 6px 24px rgba(136,69,48,0.28)' : 'none', transition: 'all 0.2s' }}
              onMouseEnter={e => { if (readyToGenerate) { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(136,69,48,0.38)' } }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = readyToGenerate ? '0 6px 24px rgba(136,69,48,0.28)' : 'none' }}
            >
              {loading ? 'Generating…' : <><Sparkles size={18} /> Generate AI Designs ✦</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
