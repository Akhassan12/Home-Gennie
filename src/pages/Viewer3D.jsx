import { useState, useCallback, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { THEMES } from '../components/ThreeViewer'
import ThreeViewer from '../components/ThreeViewer'
import True3DViewer from '../components/True3DViewer'
import { generate3DRoom as apiGenerate3DRoom } from '../services/api'
import { useAuth } from '../services/auth'
import {
  Box, Palette, Sun, Eye, Sliders,
  Sparkles, Download, ChevronRight, Loader, AlertCircle, Info,
  LayoutDashboard, Plus, Image as ImageIcon, BoxSelect, Moon, User,
  Maximize, Minimize, LogOut, ChevronDown
} from 'lucide-react'


const T = {
  bg: '#f8f9fa',
  surface: 'rgba(255, 255, 255, 0.8)',
  container: '#efeeeb',
  low: '#f4f3f0',
  text: '#1b1c1a',
  muted: '#6b7280',
  primary: '#182442',   // Deep Indigo
  secondary: '#944925', // Rustic Sienna
  accent: '#fe9e72',
  outline: '#e5e7eb',
  glass: 'glass-box'
}


export default function Viewer3D() {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  
  const rawImageUrl = searchParams.get('imageUrl')
  const imageUrl = rawImageUrl ? decodeURIComponent(rawImageUrl) : null
  const initialStyle = searchParams.get('style') || 'Modern'
  const directGlbUrl = searchParams.get('glbUrl')
  const designId = searchParams.get('designId') || ''  // for saving glb_url back to DB

  const [style, setStyle] = useState(initialStyle)
  const [config, setConfig] = useState({ exposure: 1.2, ambientIntensity: 0.4, dirIntensity: 1.5, pointIntensity: 0.6 })
  const [isGenerating3D, setIsGenerating3D] = useState(false)
  // Initialize from URL param so Gallery can pass a pre-generated model directly
  const [glbUrl, setGlbUrl] = useState(directGlbUrl ? decodeURIComponent(directGlbUrl) : null)
  const [generationError, setGenerationError] = useState(null)
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [modelTransform, setModelTransform] = useState({ scale: 1, rotation: 0 })
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)

  const navigate = useNavigate()
  const dropdownRef = useRef(null)
  const [dropdownOpen, setDropdown] = useState(false)
  
  const username = user?.user_metadata?.display_name || user?.email?.split('@')[0] || 'User'
  const userEmail = user?.email || ''
  const initials = username.slice(0, 2).toUpperCase()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  // Handle outside click for dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setDropdown(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // ── Reset viewer state whenever the user switches to a different design ──
  // Without this, clicking a different image from Gallery keeps the old model loaded.
  useEffect(() => {
    const newGlbFromUrl = searchParams.get('glbUrl')
    if (newGlbFromUrl) {
      // Gallery passed a pre-existing 3D model — load it directly, no generation needed
      setGlbUrl(decodeURIComponent(newGlbFromUrl))
      setGenerationError(null)
      setIsGenerating3D(false)
    } else {
      // New image with no model yet — clear the old model so it doesn't show
      setGlbUrl(null)
      setGenerationError(null)
    }
  }, [imageUrl])  // ← runs every time the image changes

  // Auto-generate 3D model if flag is present (only when no glbUrl already in URL)
  useEffect(() => {
    const autoGen = searchParams.get('autoGenerate') === 'true'
    const hasGlb   = !!searchParams.get('glbUrl')
    // Only auto-generate when explicitly requested and no model URL is already provided
    if (autoGen && imageUrl && !hasGlb) {
      setIsGenerating3D(true)
      // Small timeout to allow state to settle
      setTimeout(() => {
        handleGenerate3D()
        setSearchParams(prev => { prev.delete('autoGenerate'); return prev })
      }, 500)
    }
  }, [searchParams])


  const handleStyleChange = (s) => {
    setStyle(s)
    setSearchParams(prev => { prev.set('style', s); return prev })
  }

  const updateConfig = (key, val) => setConfig(prev => ({ ...prev, [key]: parseFloat(val) }))

  // ── GLB Cache (localStorage) ────────────────────────────────────
  // Stores imageUrl → glbUrl so re-visiting the same design never
  // re-generates (no API call, no cost, instant load).
  //
  // KEY FIX: All Supabase URLs share a long common prefix like:
  //   https://xxx.supabase.co/storage/v1/object/public/designs/USER_ID/...
  // Slicing the FIRST 48 base64 chars made every URL hash to the same key!
  // We now take the LAST 60 chars of the base64 where the unique
  // timestamp/filename lives, guaranteeing a unique key per image.
  const GLB_CACHE_PREFIX = 'hg_glb_v3_'  // bumped to flush all stale/corrupted entries

  const _cacheKey = (url) => {
    const b64 = btoa(unescape(encodeURIComponent(url))).replace(/[^a-z0-9]/gi, '')
    // Take the LAST 60 chars — this is where the unique part of the URL lives
    return GLB_CACHE_PREFIX + b64.slice(-60)
  }

  const getCachedGlb = (url) => {
    try   { return localStorage.getItem(_cacheKey(url)) || null }
    catch { return null }
  }

  const setCachedGlb = (url, glbUrl) => {
    try   { localStorage.setItem(_cacheKey(url), glbUrl) }
    catch {}
  }

  const clearCachedGlb = (url) => {
    try   { localStorage.removeItem(_cacheKey(url)) }
    catch {}
  }

  // Auto-load from cache whenever imageUrl changes (e.g. navigating back)
  useEffect(() => {
    if (!imageUrl) return
    const cached = getCachedGlb(imageUrl)
    if (cached) {
      console.log('[3D Cache] HIT — loading from localStorage, skipping API call')
      setGlbUrl(cached)
      setGenerationError(null)
    }
  }, [imageUrl])

  // Generate: checks cache first — skips API if model already exists
  const handleGenerate3D = async () => {
    if (!imageUrl) return
    const cached = getCachedGlb(imageUrl)
    if (cached) {
      console.log('[3D Cache] HIT — reusing cached GLB')
      setGlbUrl(cached)
      setGenerationError(null)
      return   // ← No API call, no cost, instant
    }
    await _runGeneration()
  }

  // Regenerate: bypasses cache, forces fresh depth pipeline run
  const handleRegenerate3D = async () => {
    if (!imageUrl) return
    clearCachedGlb(imageUrl)
    setGlbUrl(null)
    await _runGeneration()
  }

  // Internal: actual API call + cache write
  const _runGeneration = async () => {
    setIsGenerating3D(true)
    setGenerationError(null)
    setGlbUrl(null)
    try {
      const data = await apiGenerate3DRoom(imageUrl, user?.id || '', designId)
      if (data.success && data.glbUrl) {
        setGlbUrl(data.glbUrl)
        setCachedGlb(imageUrl, data.glbUrl)  // Save for next visit
        console.log('[3D Cache] SAVED to localStorage')
      } else {
        throw new Error('No GLB URL returned from backend')
      }
    } catch (err) {
      setGenerationError(err.message)
    } finally {
      setIsGenerating3D(false)
    }
  }

  const downloadGLB = async () => {
    if (!glbUrl) return
    try {
      const res = await fetch(glbUrl)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `room-3d-${style.toLowerCase()}.glb`; a.click()
      URL.revokeObjectURL(url)
    } catch { window.open(glbUrl, '_blank') }
  }

  const sliders = [
    { label: 'Exposure', key: 'exposure', min: 0.1, max: 2, step: 0.1, icon: Eye },
    { label: 'Ambient Light', key: 'ambientIntensity', min: 0, max: 1, step: 0.05, icon: Sun },
    { label: 'Sunlight', key: 'dirIntensity', min: 0, max: 3, step: 0.1, icon: Box },
    { label: 'Accent', key: 'pointIntensity', min: 0, max: 2, step: 0.1, icon: Palette },
  ]

  const navLinks = [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Create', to: '/upload', icon: Plus },
    { label: 'Gallery', to: '/gallery', icon: ImageIcon },
    { label: '3D Viewer', to: '/viewer', icon: BoxSelect },
  ]

  return (
    <div style={{ minHeight: '100vh', background: T.bg, color: T.text, fontFamily: '"Josefin Sans", sans-serif' }}>

      

      {/* ── Top Nav ── */}
      <nav style={{
        background: T.surface, boxShadow: '0 1px 20px rgba(27,28,26,0.06)',
        position: 'sticky', top: 0, zIndex: 100,
        height: '72px', display: 'flex', alignItems: 'center',
        padding: '0 2.5rem', gap: '2rem',
      }}>
        {/* Brand */}
        <span style={{ fontFamily: '"Noto Serif", Georgia, serif', fontWeight: 700, fontSize: '1.1rem', color: T.text, letterSpacing: '0.02em', flexShrink: 0 }}>
          Home Gennie
        </span>

        {/* Nav links */}
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

        {/* ── User Avatar + Dropdown ── */}
        <div ref={dropdownRef} style={{ position: 'relative', flexShrink: 0 }}>
          {/* Trigger pill */}
          <button
            id="user-menu-button"
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
            {/* Avatar circle */}
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

          {/* Dropdown menu */}
          {dropdownOpen && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 10px)', right: 0,
              background: T.surface, borderRadius: '14px',
              boxShadow: '0 8px 32px rgba(27,28,26,0.12)',
              minWidth: '220px', overflow: 'hidden',
              animation: 'fadeInDown 0.15s ease',
              zIndex: 200,
            }}>
              {/* User info header */}
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

              {/* Menu items */}
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

                {/* Divider */}
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

      {/* ── Main Content Area ── */}
      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '3.5rem 4rem' }}>
        
        {/* Header Section */}
        <div style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontFamily: '"Cinzel", serif', fontSize: '2.75rem', fontWeight: 900, margin: '0 0 0.5rem', color: T.text, letterSpacing: '-0.02em' }}>
            Live <span style={{ color: T.secondary, fontStyle: 'italic', fontWeight: 400 }}>Room</span> Viewer
          </h1>

          <p style={{ color: T.muted, fontSize: '0.95rem', maxWidth: '600px' }}>
            {imageUrl 
              ? 'Analyze and reconstruct your 2D design into a physical 3D environment.' 
              : 'Explore design style atmospheres in real-time. Upload an image to start 3D reconstruction.'}
          </p>
        </div>

        {/* Two Column Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 340px', gap: '2.5rem', alignItems: 'start' }}>
          
          {/* Left: Viewer Canvas */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {generationError && (
              <div style={{ background: '#fff1f0', border: '1px solid #ffccc7', padding: '1rem 1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '12px', color: '#cf1322', fontSize: '0.875rem' }}>
                <AlertCircle size={18} />
                <span><strong>Generation Error:</strong> {generationError}</span>
              </div>
            )}

            <div style={{ 
              height: isFullscreen ? '100vh' : '70vh', 
              minHeight: isFullscreen ? '100vh' : '520px', 
              width: isFullscreen ? '100vw' : 'auto',
              position: isFullscreen ? 'fixed' : 'relative',
              top: isFullscreen ? 0 : 'auto',
              left: isFullscreen ? 0 : 'auto',
              zIndex: isFullscreen ? 1000 : 1,
              background: '#0d1117', 
              borderRadius: isFullscreen ? 0 : '24px', 
              overflow: 'hidden', 
              boxShadow: isFullscreen ? 'none' : '0 20px 50px rgba(0,0,0,0.15)',
              border: isFullscreen ? 'none' : '1px solid rgba(255,255,255,0.05)',
              transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
            }}>
              {(imageUrl || glbUrl) 
                ? <True3DViewer glbUrl={glbUrl} isGenerating={isGenerating3D} onGenerate={handleGenerate3D} transform={modelTransform} />
                : <ThreeViewer style={style} config={config} />
              }

              {/* Fullscreen Toggle */}
              <button 
                onClick={() => setIsFullscreen(!isFullscreen)}
                style={{
                  position: 'absolute',
                  top: '20px',
                  right: '20px',
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  cursor: 'pointer',
                  zIndex: 1010,
                  transition: 'all 0.3s'
                }}
              >
                {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
              </button>
            </div>


            {/* Action Bar (below viewer) */}
            {imageUrl && !isGenerating3D && (
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>

                {/* Primary button — uses cache if available, no re-generation cost */}
                <button
                  onClick={handleGenerate3D}
                  style={{
                    flex: 1,
                    padding: '1.1rem',
                    borderRadius: '16px',
                    background: 'linear-gradient(135deg, #182442, #30447a)',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    cursor: 'pointer',
                    boxShadow: '0 8px 16px rgba(24,36,66,0.2)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                  onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <Sparkles size={18} />
                  {glbUrl ? 'View Room 3D' : 'Generate Full Room 3D'}
                </button>

                {/* Regenerate — forces fresh generation, bypasses cache */}
                {glbUrl && (
                  <button
                    onClick={handleRegenerate3D}
                    title="Force regenerate (clears cache)"
                    style={{
                      padding: '1.05rem 1.1rem',
                      borderRadius: '16px',
                      background: 'rgba(255,255,255,0.08)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'rgba(255,255,255,0.7)',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      whiteSpace: 'nowrap'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)'; e.currentTarget.style.color = '#fff' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)' }}
                  >
                    🔄 New
                  </button>
                )}

                {/* Download GLB */}
                {glbUrl && (
                  <button
                    onClick={downloadGLB}
                    style={{
                      padding: '1rem 1.75rem',
                      borderRadius: '16px',
                      background: 'rgba(255, 255, 255, 0.8)',
                      backdropFilter: 'blur(12px)',
                      color: T.text,
                      border: '1px solid rgba(0,0,0,0.05)',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.3s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#fff'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.8)'}
                  >
                    <Download size={18} />
                    .GLB
                  </button>
                )}
              </div>
            )}

          </div>

          {/* Right: Sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Design Style Card */}
            <div className="glass-box" style={{ padding: '1.75rem', borderRadius: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem' }}>
                <Palette size={18} style={{ color: T.secondary }} />
                <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.15em', color: T.muted }}>Design Style</h3>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {Object.keys(THEMES).map(s => (
                  <button 
                    key={s}
                    onClick={() => handleStyleChange(s)}
                    style={{
                      padding: '0.6rem 1.25rem',
                      borderRadius: '12px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      border: 'none',
                      background: style === s ? T.low : T.surface,
                      color: style === s ? T.primary : T.muted,
                      boxShadow: style === s ? '0 0 0 1.5px ' + T.primary : '0 0 0 1px ' + T.container,
                      transition: 'all 0.2s'
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Scene Settings Card (only for preview) */}
            {!imageUrl && (
              <div className="glass-box" style={{ padding: '1.75rem', borderRadius: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem' }}>
                  <Sliders size={18} style={{ color: T.primary }} />
                  <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.15em', color: T.muted }}>Scene Settings</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {sliders.map(({ label, key, min, max, step, icon: Icon }) => (
                    <div key={key}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: T.text, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Icon size={12} style={{ color: T.muted }} /> {label}
                        </span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: T.primary, tabularNums: true }}>{config[key]}</span>
                      </div>
                      <input 
                        type="range" min={min} max={max} step={step} 
                        value={config[key]} 
                        onChange={e => updateConfig(key, e.target.value)}
                        className="premium-slider"
                        style={{ width: '100%', accentColor: T.primary, cursor: 'pointer' }}
                      />

                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3D Adjustment Settings Card (only for generated 3D Model) */}
            {glbUrl && (
              <div className="glass-box" style={{ padding: '1.75rem', borderRadius: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem' }}>
                  <Sliders size={18} style={{ color: T.primary }} />
                  <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.15em', color: T.muted }}>Adjust 3D Model</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Scale Slider */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: T.text, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Maximize size={12} style={{ color: T.muted }} /> Scale / Size
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: T.primary, tabularNums: true }}>{modelTransform.scale}x</span>
                    </div>
                    <input 
                      type="range" min="0.5" max="3" step="0.1" 
                      value={modelTransform.scale} 
                      onChange={e => setModelTransform(prev => ({...prev, scale: parseFloat(e.target.value)}))}
                      className="premium-slider"
                      style={{ width: '100%', accentColor: T.primary, cursor: 'pointer' }}
                    />
                  </div>
                  {/* Rotation Slider */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: T.text, display: 'flex', alignItems: 'center', gap: '6px' }}>
                         <Box size={12} style={{ color: T.muted }} /> Initial Rotation
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: T.primary, tabularNums: true }}>{modelTransform.rotation}°</span>
                    </div>
                    <input 
                      type="range" min="0" max="360" step="15" 
                      value={modelTransform.rotation} 
                      onChange={e => setModelTransform(prev => ({...prev, rotation: parseInt(e.target.value)}))}
                      className="premium-slider"
                      style={{ width: '100%', accentColor: T.primary, cursor: 'pointer' }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* How It Works Card */}
            <div className="glass-box" style={{ padding: '1.75rem', borderRadius: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem' }}>
                <Info size={18} style={{ color: T.secondary }} />
                <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.15em', color: T.muted }}>How It Works</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                 {[
                   { n: '1', t: 'Click Generate 3D Model to run your design through our AI reconstruction pipeline.' },
                   { n: '2', t: 'Orbit, zoom, and explore the generated 3D geometry of your room.' },
                   { n: '3', t: 'Scan the QR code to project the model into your real space using AR.' }
                 ].map(item => (
                   <div key={item.n} style={{ display: 'flex', gap: '12px' }}>
                     <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: T.secondary, color: '#fff', fontSize: '0.75rem', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{item.n}</div>
                     <p style={{ margin: 0, fontSize: '0.8rem', lineHeight: 1.5, color: T.muted }}>{item.t}</p>
                   </div>
                 ))}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  )
}
