import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Sparkles, RefreshCw, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../services/auth'
import { supabase } from '../services/supabase'

const T = {
  bg: '#fbf9f6', surface: '#ffffff', container: '#efeeeb',
  low: '#f5f3f0', text: '#1b1c1a', muted: '#54433e',
  primary: '#884530', secondary: '#6b5c4c', accent: '#f4dfcb'
}

const FILTERS = ['All', 'Living Room', 'Bedroom', 'Kitchen', 'Dining', 'Outdoor']

const DEMO_ITEMS = [
  { id: 'd1', title: 'The Japandi Suite',    style: 'Japandi',      room: 'Living Room', img: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=800', status: 'done' },
  { id: 'd2', title: 'Terra Cotta Kitchen',  style: 'Mediterranean',room: 'Kitchen',     img: 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?q=80&w=800', status: 'done' },
  { id: 'd3', title: 'Velvet Night Suite',   style: 'Modern',       room: 'Bedroom',     img: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=800', status: 'done' },
  { id: 'd4', title: 'The Nordic Study',     style: 'Scandinavian', room: 'Living Room', img: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=800', status: 'done' },
  { id: 'd5', title: 'Bohemian Dining Loft', style: 'Bohemian',     room: 'Dining',      img: 'https://images.unsplash.com/photo-1617806118233-18e1de247200?q=80&w=800', status: 'done' },
  { id: 'd6', title: 'The Minimalist Den',   style: 'Minimalist',   room: 'Bedroom',     img: 'https://images.unsplash.com/photo-1585128791500-5f6e8be73f5d?q=80&w=800', status: 'done' },
]

const EASE = [0.23, 1, 0.32, 1]

function mapDesign(d) {
  // Determine which image to display:
  // - 'pending' → spinner
  // - 'failed'  → show original image with a warning badge
  // - valid URL → show generated image
  const status = d.generated_image_url === 'pending'
    ? 'pending'
    : d.generated_image_url === 'failed'
    ? 'failed'
    : 'done'

  const displayImg = status === 'done'
    ? d.generated_image_url
    : d.original_image_url   // Always fall back to the original photo

  return {
    id: d.id,
    title: `${d.style} ${d.room_type}`,
    style: d.style,
    room: d.room_type,
    img: displayImg,
    originalImg: d.original_image_url,
    glbUrl: d.glb_url || null,   // ← 3D model URL (if already generated)
    status,
    createdAt: d.created_at,
  }
}

export default function Gallery() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [filter, setFilter]   = useState('All')
  const [designs, setDesigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [hovered, setHovered] = useState(null)

  // ─── Fetch from Supabase ─────────────────────────────────────
  const fetchDesigns = useCallback(async () => {
    if (!user) { setDesigns(DEMO_ITEMS); setLoading(false); return }
    try {
      // Try fetching with glb_url (exists after the DB migration is run)
      let { data, error } = await supabase
        .from('designs')
        .select('id, original_image_url, generated_image_url, room_type, style, created_at, glb_url')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      // If the glb_url column does not exist yet, fall back to query without it
      if (error && error.message?.includes('glb_url')) {
        console.warn('[Gallery] glb_url column not found, retrying without it.')
        const fallback = await supabase
          .from('designs')
          .select('id, original_image_url, generated_image_url, room_type, style, created_at')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
        data = fallback.data
        error = fallback.error
      }

      if (error) throw error

      if (data && data.length > 0) {
        setDesigns(data.map(mapDesign))
      } else {
        setDesigns(DEMO_ITEMS)
      }
    } catch (e) {
      console.error('Gallery fetch error:', e)
      setDesigns(DEMO_ITEMS)
    } finally {
      setLoading(false)
    }
  }, [user])

  // ─── Initial fetch ───────────────────────────────────────────
  useEffect(() => {
    fetchDesigns()
  }, [fetchDesigns])

  // ─── Polling — only while any design is "pending" ────────────
  useEffect(() => {
    const hasPending = designs.some(d => d.status === 'pending')
    if (!hasPending) return

    const interval = setInterval(fetchDesigns, 10000) // poll every 10s
    return () => clearInterval(interval)
  }, [designs, fetchDesigns])

  const filtered = filter === 'All' ? designs : designs.filter(d => d.room === filter)
  const pendingCount = designs.filter(d => d.status === 'pending').length

  return (
    <div style={{ minHeight: '100vh', background: T.bg, fontFamily: 'Inter, sans-serif' }}>

      {/* ── Sticky Nav ── */}
      <nav style={{
        background: T.surface, boxShadow: '0 1px 20px rgba(27,28,26,0.06)',
        position: 'sticky', top: 0, zIndex: 50, height: '72px',
        display: 'flex', alignItems: 'center', padding: '0 2.5rem', gap: '2rem'
      }}>
        <Link to="/dashboard" style={{ fontFamily: '"Noto Serif",Georgia,serif', fontWeight: 700, fontSize: '1.1rem', color: T.text, textDecoration: 'none', flexShrink: 0 }}>
          Home Gennie
        </Link>
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '2rem' }}>
          {[['Dashboard','/dashboard'],['Create','/upload'],['Gallery','/gallery'],['3D Viewer','/viewer']].map(([l,to]) => (
            <Link key={to} to={to} style={{ fontSize: '0.875rem', color: to === '/gallery' ? T.primary : T.muted, textDecoration: 'none', fontWeight: to === '/gallery' ? 600 : 400 }}>{l}</Link>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Refresh button */}
          <motion.button
            onClick={fetchDesigns}
            whileHover={{ rotate: 180 }}
            transition={{ duration: 0.4 }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: T.muted, display: 'flex', alignItems: 'center' }}
            title="Refresh gallery"
          >
            <RefreshCw size={17} />
          </motion.button>
          <Link to="/upload" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: `linear-gradient(135deg,${T.primary},#A65D46)`, color: '#fff', textDecoration: 'none', padding: '0.55rem 1.25rem', borderRadius: '9999px', fontSize: '0.825rem', fontWeight: 700, boxShadow: '0 2px 12px rgba(136,69,48,0.25)', flexShrink: 0 }}>
            <Plus size={15} /> Create
          </Link>
        </div>
      </nav>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 2.5rem 5rem' }}>

        {/* ── Page Header ── */}
        <motion.div
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: EASE }}
        >
          <div>
            <h1 style={{ fontFamily: '"Noto Serif",Georgia,serif', fontSize: 'clamp(2.2rem,4vw,3rem)', fontWeight: 700, color: T.text, margin: '0 0 0.5rem', lineHeight: 1.1 }}>
              Your <em style={{ fontStyle: 'italic', fontWeight: 400 }}>Curated</em> Designs
            </h1>
            <p style={{ color: T.muted, fontSize: '1rem', margin: 0 }}>
              A collection of spaces reimagined by AI. Your designs persist across sessions.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
            <span style={{ background: T.container, color: T.muted, padding: '0.4rem 1rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 600, whiteSpace: 'nowrap' }}>
              {designs.length} design{designs.length !== 1 ? 's' : ''}
            </span>
            {/* Pending indicator */}
            <AnimatePresence>
              {pendingCount > 0 && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  style={{ background: '#f4dfcb', color: T.secondary, padding: '0.3rem 0.85rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}
                >
                  <Sparkles size={11} style={{ animation: 'pulse 2s infinite' }} />
                  {pendingCount} generating… (auto-refreshes)
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* ── Filter Row ── */}
        <motion.div
          style={{ display: 'flex', gap: '0.625rem', flexWrap: 'wrap', marginBottom: '2.5rem' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.15 }}
        >
          {FILTERS.map(f => (
            <motion.button
              key={f}
              onClick={() => setFilter(f)}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              style={{ padding: '0.5rem 1.25rem', borderRadius: '9999px', border: 'none', fontFamily: 'Inter, sans-serif', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer', background: filter === f ? T.accent : 'transparent', color: filter === f ? T.secondary : T.muted, transition: 'background 0.2s, color 0.2s' }}
            >
              {f}
            </motion.button>
          ))}
        </motion.div>

        {/* ── Grid ── */}
        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {[1,2,3,4,5,6].map(i => (
              <div key={i} style={{ aspectRatio: '4/5', background: T.container, borderRadius: '16px', animation: 'pulse 1.5s infinite' }} />
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <motion.div
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          >
            {filtered.map((d) => (
              <motion.div
                key={d.id}
                variants={{
                  hidden: { opacity: 0, y: 40, scale: 0.96 },
                  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.7, ease: EASE } }
                }}
                onHoverStart={() => setHovered(d.id)}
                onHoverEnd={() => setHovered(null)}
                onClick={() => {
                  if (d.status === 'done') {
                    // If this design already has a saved 3D model, pass it directly — no re-generation needed
                    const params = new URLSearchParams({
                      imageUrl: d.img,
                      style: d.style,
                      designId: d.id,   // ← so backend can save glb_url back to this row
                    })
                    if (d.glbUrl) {
                      params.set('glbUrl', d.glbUrl)   // ← load saved model instantly
                    } else {
                      params.set('autoGenerate', 'true') // ← no model yet, trigger generation
                    }
                    navigate(`/viewer?${params.toString()}`)
                  }
                }}
                style={{
                  position: 'relative', aspectRatio: '4/5',
                  borderRadius: '16px', overflow: 'hidden',
                  cursor: d.status === 'done' ? 'pointer' : 'default',
                  boxShadow: hovered === d.id ? '0 20px 50px rgba(27,28,26,0.18)' : '0 4px 24px rgba(27,28,26,0.08)',
                  transition: 'box-shadow 0.4s ease',
                }}
                whileHover={{ y: -8 }}
                transition={{ duration: 0.4, ease: EASE }}
              >
                {/* ── Image (always the original photo minimum) ── */}
                <motion.img
                  src={d.img}
                  alt={d.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  animate={{ scale: hovered === d.id ? 1.06 : 1 }}
                  transition={{ duration: 1.2, ease: EASE }}
                />

                {/* ── Gradient overlay ── */}
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '65%', background: 'linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 100%)' }} />

                {/* ── Status badge — top right ── */}
                {d.status === 'pending' && (
                  <motion.div
                    animate={{ opacity: [0.7, 1, 0.7] }}
                    transition={{ repeat: Infinity, duration: 1.8 }}
                    style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)', padding: '0.3rem 0.75rem', borderRadius: '9999px', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.7rem', fontWeight: 700, color: '#fff' }}
                  >
                    <Sparkles size={10} /> Generating…
                  </motion.div>
                )}
                {d.status === 'failed' && (
                  <div style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'rgba(147,0,10,0.75)', backdropFilter: 'blur(8px)', padding: '0.3rem 0.75rem', borderRadius: '9999px', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.7rem', fontWeight: 700, color: '#fff' }}>
                    <AlertCircle size={10} /> AI Unavailable
                  </div>
                )}
                {d.status === 'done' && (
                  <span style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.7rem', fontWeight: 700, color: T.secondary, letterSpacing: '0.04em' }}>
                    {d.style}
                  </span>
                )}

                {/* ── Room name + subtitle ── */}
                <div style={{ position: 'absolute', bottom: '1.25rem', left: '1.25rem', right: '1.25rem' }}>
                  <p style={{ fontFamily: '"Noto Serif",Georgia,serif', fontStyle: 'italic', fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0 0 4px', lineHeight: 1.3 }}>
                    {d.title}
                  </p>
                  {d.status === 'failed' && (
                    <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.65)', margin: 0 }}>
                      Showing your original photo
                    </p>
                  )}
                </div>

                {/* ── Hover CTA (only for completed designs) ── */}
                {d.status === 'done' && (
                  <motion.div
                    style={{ position: 'absolute', inset: 0, background: 'rgba(27,28,26,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: hovered === d.id ? 1 : 0 }}
                    transition={{ duration: 0.25 }}
                  >
                    <span style={{ background: `linear-gradient(135deg,${T.primary},#A65D46)`, color: '#fff', padding: '0.65rem 1.5rem', borderRadius: '9999px', fontSize: '0.875rem', fontWeight: 700, boxShadow: '0 4px 16px rgba(136,69,48,0.4)' }}>
                      View in 3D
                    </span>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            style={{ textAlign: 'center', padding: '5rem 2rem' }}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: EASE }}
          >
            <div style={{ width: '72px', height: '72px', background: T.accent, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem' }}>
              <Sparkles size={32} style={{ color: T.secondary }} />
            </div>
            <h2 style={{ fontFamily: '"Noto Serif",Georgia,serif', fontSize: '1.75rem', fontWeight: 700, color: T.text, marginBottom: '0.75rem' }}>Your collection awaits.</h2>
            <p style={{ color: T.muted, fontSize: '1rem', marginBottom: '2rem', lineHeight: 1.6 }}>
              Begin by uploading a room photo and letting AI reimagine the space.
            </p>
            <Link to="/upload" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: `linear-gradient(135deg,${T.primary},#A65D46)`, color: '#fff', textDecoration: 'none', padding: '0.875rem 2rem', borderRadius: '9999px', fontSize: '0.95rem', fontWeight: 700, boxShadow: '0 6px 24px rgba(136,69,48,0.3)' }}>
              <Plus size={18} /> Create Your First Design
            </Link>
          </motion.div>
        )}

        {/* ── Bottom CTA ── */}
        {filtered.length > 0 && (
          <motion.div
            style={{ marginTop: '5rem', textAlign: 'center' }}
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h3 style={{ fontFamily: '"Noto Serif",Georgia,serif', fontSize: '1.5rem', fontWeight: 700, color: T.text, marginBottom: '0.75rem' }}>
              Ready to create <em style={{ fontStyle: 'italic', fontWeight: 400 }}>more</em>?
            </h3>
            <p style={{ color: T.muted, marginBottom: '1.5rem', fontSize: '0.95rem' }}>Your next masterpiece is one photo away.</p>
            <Link to="/upload" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: `linear-gradient(135deg,${T.primary},#A65D46)`, color: '#fff', textDecoration: 'none', padding: '0.875rem 2rem', borderRadius: '9999px', fontSize: '0.95rem', fontWeight: 700, boxShadow: '0 6px 24px rgba(136,69,48,0.28)' }}>
              <Plus size={18} /> Create New Design
            </Link>
          </motion.div>
        )}
      </div>
    </div>
  )
}
