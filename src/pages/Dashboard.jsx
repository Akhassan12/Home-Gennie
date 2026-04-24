import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Sparkles, Box, Plus, ArrowRight, Palette, LogOut, User, ChevronDown, TrendingUp } from 'lucide-react'
import { useAuth } from '../services/auth'
import { supabase } from '../services/supabase'

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

const QUICK_ACTIONS = [
  { icon: Sparkles, label: 'Generate Palette',  desc: 'Extract harmonic color tones from any inspiration image.', color: '#fff4f1', iconColor: '#884530', to: '/upload' },
  { icon: Box,      label: 'Space Scan',         desc: 'Convert your real-world room into a 3D digital twin.',     color: '#f5f3f0', iconColor: '#6b5c4c', to: '/viewer' },
  { icon: Palette,  label: 'Curate Moodboard',  desc: 'Combine textures and furniture for your next project.',    color: '#f4dfcb', iconColor: '#6b5c4c', to: '/gallery' },
]

// Fallback demo images for new users with no designs yet
const DEMO_RECENT = [
  { id: 'd1', title: 'My First Plan', style: 'Modern', img: 'https://images.unsplash.com/photo-1513694203232-719a280e022f?q=80&w=600' },
]

// Real-Time Trending Designs
const TRENDING_DESIGNS = [
  { id: 't1', title: 'Japandi Fusion', style: 'Serene · Minimal', img: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=600' },
  { id: 't2', title: 'Biophilic Oasis', style: 'Nature · Greenery', img: 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?q=80&w=600' },
  { id: 't3', title: 'Industrial Chic', style: 'Urban · Exposed', img: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=600' },
]

export default function Dashboard() {
  const { user, signOut }  = useAuth()
  const location           = useLocation()
  const navigate           = useNavigate()
  const dropdownRef        = useRef(null)

  const [stats, setStats]         = useState({ total: 0, ai: 0, week: 0 })
  const [recentDesigns, setRecent]= useState([])
  const [dropdownOpen, setDropdown] = useState(false)

  // Derive display name from current user's metadata
  const username  = user?.user_metadata?.display_name
                  || user?.user_metadata?.full_name
                  || user?.email?.split('@')[0]
                  || 'Designer'
  const initials  = username.slice(0, 2).toUpperCase()
  const userEmail = user?.email || ''

  // ── Fetch data scoped to the current user ──────────────────
  useEffect(() => {
    // Reset state immediately so stale data from a previous user never shows
    setStats({ total: 0, ai: 0, week: 0 })
    setRecent([])

    if (!user?.id) return

    const fetchData = async () => {
      const { data, error } = await supabase
        .from('designs')
        .select('id, created_at, room_type, style, original_image_url, generated_image_url')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(20)

      if (error) {
        console.warn('[Dashboard] designs fetch error:', error.message)
        return
      }

      if (data) {
        const weekAgo = new Date(Date.now() - 7 * 86400000)
        setStats({
          total: data.length,
          ai:    data.length,
          week:  data.filter(d => new Date(d.created_at) > weekAgo).length,
        })
        setRecent(data.slice(0, 3))
      }
    }

    fetchData()
  }, [user?.id]) // ← key: re-runs when the user ID changes, not just the user object

  // ── Close dropdown on outside click ───────────────────────
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  // ── Sign out ───────────────────────────────────────────────
  const handleSignOut = async () => {
    setDropdown(false)
    await signOut()
    navigate('/login')
  }

  const STAT_CARDS = [
    { label: 'Total Designs', value: stats.total },
    { label: 'AI Generated',  value: stats.ai    },
    { label: 'This Week',     value: stats.week  },
    { label: 'Rooms Done',    value: stats.total },
  ]

  // Use real designs if available, otherwise fall back to demo
  const displayRecent = recentDesigns.length > 0
    ? recentDesigns.map(d => ({
        id:    d.id,
        title: `${d.style || 'My'} ${d.room_type || 'Room'}`,
        style: d.style || 'Custom',
        img:   d.generated_image_url || d.original_image_url || DEMO_RECENT[0].img,
      }))
    : DEMO_RECENT

  return (
    <div style={{ minHeight: '100vh', background: T.bg, fontFamily: 'Inter, sans-serif' }}>

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

      {/* ── Main Content ── */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2.5rem 2.5rem 5rem' }}>

        {/* Welcome Banner */}
        <div style={{ background: 'linear-gradient(135deg, #884530 0%, #A65D46 100%)', borderRadius: '20px', padding: '2.5rem 3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', boxShadow: '0 8px 32px rgba(136,69,48,0.2)' }}>
          <div>
            <h1 style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: 'clamp(1.6rem, 3vw, 2.2rem)', fontWeight: 700, color: '#ffffff', margin: '0 0 0.5rem', lineHeight: 1.2 }}>
              Welcome back, <em style={{ fontStyle: 'italic', fontWeight: 400 }}>{username}</em>
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.95rem', margin: 0, lineHeight: 1.6 }}>
              Your studio is ready. Continue your journey through curated intelligence and spatial harmony.
            </p>
          </div>
          <Link to="/upload"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.18)', color: '#ffffff', textDecoration: 'none', padding: '0.75rem 1.5rem', borderRadius: '9999px', fontSize: '0.875rem', fontWeight: 600, backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', whiteSpace: 'nowrap', transition: 'background 0.2s' }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.28)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.18)'}
          >
            <Plus size={16} /> Create New Design
          </Link>
        </div>

        {/* Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2.5rem' }}>
          {STAT_CARDS.map((s, i) => (
            <div key={i} style={{ background: T.surface, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 2px 16px rgba(27,28,26,0.05)' }}>
              <div style={{ height: '3px', background: 'linear-gradient(90deg, #884530, #A65D46)' }} />
              <div style={{ padding: '1.5rem' }}>
                <p style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '2.5rem', fontWeight: 700, color: T.text, margin: '0 0 0.25rem', lineHeight: 1 }}>
                  {s.value}
                </p>
                <p style={{ fontSize: '0.8rem', color: T.muted, margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: 500 }}>
                  {s.label}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <h2 style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '1.4rem', fontWeight: 700, color: T.text, marginBottom: '1.25rem' }}>
          Quick Actions
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem', marginBottom: '3rem' }}>
          {QUICK_ACTIONS.map((a, i) => (
            <Link key={i} to={a.to} style={{ textDecoration: 'none' }}>
              <div
                style={{ background: a.color, borderRadius: '16px', padding: '1.75rem', transition: 'transform 0.25s ease, box-shadow 0.25s ease', cursor: 'pointer' }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(27,28,26,0.09)' }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
              >
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: T.surface, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem', boxShadow: '0 2px 8px rgba(27,28,26,0.06)' }}>
                  <a.icon size={22} strokeWidth={1.5} style={{ color: a.iconColor }} />
                </div>
                <h3 style={{ fontFamily: 'Inter, sans-serif', fontSize: '1rem', fontWeight: 700, color: T.text, margin: '0 0 0.4rem' }}>{a.label}</h3>
                <p style={{ fontSize: '0.85rem', color: T.muted, margin: 0, lineHeight: 1.6 }}>{a.desc}</p>
              </div>
            </Link>
          ))}
        </div>

        {/* ── Trending Designs (Real-Time Trends) ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '1.4rem', fontWeight: 700, color: T.text, margin: '0 0 0.25rem' }}>
              Trending Right Now
            </h2>
            <p style={{ margin: 0, fontSize: '0.85rem', color: T.muted }}>Discover popular styles to inspire your next room makeover.</p>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem', marginBottom: '3rem' }}>
          {TRENDING_DESIGNS.map((d) => (
            <div key={d.id}
              style={{ background: T.surface, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 2px 16px rgba(27,28,26,0.06)', transition: 'transform 0.25s ease', cursor: 'pointer' }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ aspectRatio: '16/9', overflow: 'hidden', position: 'relative' }}>
                <img
                  src={d.img} alt={d.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 1.2s ease' }}
                  onMouseEnter={e => e.target.style.transform = 'scale(1.06)'}
                  onMouseLeave={e => e.target.style.transform = 'scale(1)'}
                />
                <span style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(8px)', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.7rem', fontWeight: 600, color: '#10b981', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <TrendingUp size={12} /> Trending
                </span>
              </div>
              <div style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '1rem', fontWeight: 700, fontStyle: 'italic', color: T.text, margin: '0 0 0.15rem' }}>{d.title}</p>
                  <p style={{ fontSize: '0.75rem', color: T.muted, margin: 0 }}>{d.style}</p>
                </div>
                <Link to="/upload" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'linear-gradient(135deg, #884530, #A65D46)', color: '#fff', textDecoration: 'none', padding: '0.4rem 1rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 600, boxShadow: '0 2px 8px rgba(136,69,48,0.2)' }}>
                  Try Style
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* ── Recent Designs ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h2 style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '1.4rem', fontWeight: 700, color: T.text, margin: 0 }}>
            {recentDesigns.length > 0 ? 'Recent Designs' : 'Inspiration Gallery'}
          </h2>
          <Link to="/gallery" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: T.primary, textDecoration: 'none', fontSize: '0.875rem', fontWeight: 600 }}>
            {recentDesigns.length > 0 ? 'View All' : 'Start Creating'} <ArrowRight size={15} />
          </Link>
        </div>

        {/* New user call-to-action OR real designs */}
        {recentDesigns.length === 0 && (
          <div style={{ background: T.container, borderRadius: '16px', padding: '1.5rem 2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg, #884530, #A65D46)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Sparkles size={20} style={{ color: '#fff' }} />
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: '0 0 0.25rem', fontWeight: 700, fontSize: '0.95rem', color: T.text }}>You haven't created any designs yet</p>
              <p style={{ margin: 0, fontSize: '0.85rem', color: T.muted }}>Upload a room photo and let AI transform it. Your first design is just a click away.</p>
            </div>
            <Link to="/upload" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'linear-gradient(135deg,#884530,#A65D46)', color: '#fff', textDecoration: 'none', padding: '0.6rem 1.25rem', borderRadius: '9999px', fontSize: '0.825rem', fontWeight: 700, whiteSpace: 'nowrap', boxShadow: '0 4px 16px rgba(136,69,48,0.25)' }}>
              <Plus size={14} /> Create First Design
            </Link>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
          {displayRecent.map((d) => (
            <div key={d.id}
              style={{ background: T.surface, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 2px 16px rgba(27,28,26,0.06)', transition: 'transform 0.25s ease', cursor: 'pointer' }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ aspectRatio: '4/3', overflow: 'hidden', position: 'relative' }}>
                <img
                  src={d.img} alt={d.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 1.2s ease' }}
                  onMouseEnter={e => e.target.style.transform = 'scale(1.06)'}
                  onMouseLeave={e => e.target.style.transform = 'scale(1)'}
                />
                <span style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(8px)', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.7rem', fontWeight: 600, color: T.secondary, letterSpacing: '0.05em' }}>
                  {d.style}
                </span>
              </div>
              <div style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <p style={{ fontFamily: '"Noto Serif", Georgia, serif', fontSize: '1rem', fontWeight: 700, fontStyle: 'italic', color: T.text, margin: 0 }}>{d.title}</p>
                <Link to="/gallery" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: T.container, color: T.text, textDecoration: 'none', padding: '0.4rem 1rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 600 }}>
                  View
                </Link>
              </div>
            </div>
          ))}
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
