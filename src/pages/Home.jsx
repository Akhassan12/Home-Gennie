/**
 * Home Gennie — Premium Landing Page
 * Design System: ui-ux-pro-max → "Scroll-Triggered Storytelling"
 * Palette: Warm Stone #1C1917 + Amber Gold #CA8A04
 * Fonts: Cinzel (headings) + Josefin Sans (body) — already loaded in index.css
 * Animations: Framer Motion — clip-path reveals, scroll-triggered fades, mouse parallax
 * UX Rules: ease-out enter, max 2 animations/view, prefers-reduced-motion respected
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  motion, AnimatePresence,
  useMotionValue, useSpring, useScroll, useTransform,
  useInView
} from 'framer-motion'
import {
  ArrowUpRight, ArrowRight, Upload, Wand2,
  Eye, Star, Users, Layers, ChevronDown
} from 'lucide-react'

/* ─────────────────────────────────────────────────────────
   DESIGN TOKENS (from ui-ux-pro-max output)
───────────────────────────────────────────────────────── */
const C = {
  // Stone darks
  stone950: '#0C0A09',
  stone900: '#1C1917',
  stone800: '#292524',
  stone700: '#44403C',
  stone500: '#78716C',
  stone300: '#D6D3D1',
  stone100: '#F5F5F4',
  stone50:  '#FAFAF9',
  // Gold accent
  gold:     '#CA8A04',
  goldLight:'#FEF3C7',
  goldDark: '#92400E',
  // White
  white:    '#FFFFFF',
}

/* ─────────────────────────────────────────────────────────
   ANIMATION PRESETS
───────────────────────────────────────────────────────── */
const EASE_OUT   = [0.23, 1, 0.32, 1]
const EASE_FLUID = [0.76, 0, 0.24, 1]

// Detects prefers-reduced-motion
const prefersReducedMotion =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const fadeUp = {
  hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 40 },
  visible: (delay = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.9, ease: EASE_OUT, delay }
  }),
}

/* ─────────────────────────────────────────────────────────
   HERO IMAGES — room-only photos
───────────────────────────────────────────────────────── */
const HERO_CARDS = [
  { src: 'https://images.unsplash.com/photo-1689263131806-e18b11a17993?q=80&w=1298', style: { top: '15%', left: '3.5%', width: '210px', height: '175px' }, px: -16, py: -10 },
  { src: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?q=80&w=1200', style: { top: '5%', right: '3%', width: '340px', height: '215px' }, px: 18, py: -8 },
  { src: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=800', style: { top: '37%', right: '9%', width: '200px', height: '240px' }, px: 20, py: 16 },
  { src: 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?q=80&w=800', style: { top: '50%', left: '10%', width: '230px', height: '270px' }, px: -18, py: 18 },
  { src: 'https://images.unsplash.com/photo-1593696140826-c58b021acf8b?q=80&w=1200', style: { bottom: '2%', left: '53%', transform: 'translateX(-50%)', width: '270px', height: '205px' }, px: 0, py: 22 },
  { src: '/indian_traditional_room.png', style: { bottom: '2%', right: '5%', width: 'clamp(130px, 13vw, 195px)', height: 'clamp(120px, 13vw, 180px)' }, px: 16, py: 20 },
]

const MARQUEE_ITEMS = [
  'Mid-Century Modern', 'Scandinavian Minimal', 'Indian Traditional',
  'Bohemian Eclectic', 'Industrial Chic', 'Coastal Modern',
  'Mediterranean', 'Art Deco Revival', 'Wabi-Sabi',
]

const STATS = [
  { value: 12000, suffix: '+', label: 'Designs Generated' },
  { value: 98,    suffix: '%', label: 'Satisfaction Rate' },
  { value: 9,     suffix: '',  label: 'Unique Styles' },
]

const STYLES = [
  { num: '01', title: 'Mid-Century Modern',      img: 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?q=80&w=900' },
  { num: '02', title: 'Scandinavian Minimalist', img: 'https://images.unsplash.com/photo-1593696140826-c58b021acf8b?q=80&w=900' },
  { num: '03', title: 'Indian Traditional',      img: '/indian_traditional_room.png' },
]

const HOW_STEPS = [
  { icon: Upload, num: '01', title: 'Upload your room', desc: 'Snap or upload any wide-angle photo of your existing space. Works with any phone camera.' },
  { icon: Wand2,  num: '02', title: 'Choose a style',  desc: 'Browse 9 curated AI aesthetics. From serene Japandi to bold Art Deco revival.' },
  { icon: Eye,    num: '03', title: 'See it live',     desc: 'Your AI-redesigned room appears in seconds. Explore in 3D and AR instantly.' },
]

/* ─────────────────────────────────────────────────────────
   ANIMATED COUNTER
───────────────────────────────────────────────────────── */
function Counter({ to, suffix }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })

  useEffect(() => {
    if (!isInView || prefersReducedMotion) { setCount(to); return }
    let start = 0
    const duration = 1600
    const tick = 16
    const step = to / (duration / tick)
    const timer = setInterval(() => {
      start = Math.min(start + step, to)
      setCount(Math.round(start))
      if (start >= to) clearInterval(timer)
    }, tick)
    return () => clearInterval(timer)
  }, [isInView, to])

  return (
    <span ref={ref} style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: 'clamp(2.2rem, 4vw, 3.5rem)', color: C.gold, letterSpacing: '-0.02em', lineHeight: 1 }}>
      {count.toLocaleString()}{suffix}
    </span>
  )
}

/* ─────────────────────────────────────────────────────────
   MARQUEE STRIP
───────────────────────────────────────────────────────── */
function Marquee() {
  const doubled = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS]
  return (
    <div style={{ overflow: 'hidden', background: C.stone900, borderTop: `1px solid rgba(255,255,255,0.05)`, borderBottom: `1px solid rgba(255,255,255,0.05)`, padding: '14px 0' }}>
      <motion.div
        style={{ display: 'flex', gap: '2.5rem', width: 'max-content' }}
        animate={prefersReducedMotion ? {} : { x: ['0%', '-50%'] }}
        transition={{ repeat: Infinity, duration: 32, ease: 'linear' }}
      >
        {doubled.map((s, i) => (
          <span key={i} style={{
            fontFamily: 'Josefin Sans, sans-serif',
            fontWeight: 300,
            fontSize: '0.8rem',
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: i % 2 === 0 ? 'rgba(255,255,255,0.35)' : C.gold,
            whiteSpace: 'nowrap',
          }}>
            {s} <span style={{ color: 'rgba(255,255,255,0.1)', margin: '0 0.5rem' }}>✦</span>
          </span>
        ))}
      </motion.div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────
   PRELOADER
   - Cinzel brand name top-left
   - Central image blooms from 4% → 100%
   - Count-up bottom-right
   - Panel slides UP on exit
───────────────────────────────────────────────────────── */
function Preloader({ onComplete }) {
  const [count, setCount]       = useState(0)
  const [scale, setScale]       = useState(0.04)
  const [done, setDone]         = useState(false)

  useEffect(() => {
    if (prefersReducedMotion) { setCount(100); setScale(1); setDone(true); return }
    const total = 2600
    const tick  = 16
    let elapsed = 0
    const t = setInterval(() => {
      elapsed += tick
      const p = Math.min(elapsed / total, 1)
      const e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
      setCount(Math.round(e * 100))
      const sp = Math.max(0, (p - 0.68) / 0.32)
      const se = sp < 0.5 ? 2 * sp * sp : 1 - Math.pow(-2 * sp + 2, 2) / 2
      setScale(0.04 + se * 0.96)
      if (p >= 1) { clearInterval(t); setTimeout(() => setDone(true), 150) }
    }, tick)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (done) setTimeout(onComplete, 1100)
  }, [done, onComplete])

  return (
    <motion.div
      style={{ position: 'fixed', inset: 0, zIndex: 200, background: C.stone950, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}
      animate={done ? { y: '-100%' } : { y: 0 }}
      transition={done ? { duration: 1.05, ease: EASE_FLUID } : { duration: 0 }}
    >
      {/* Expanding image WITH center animated text */}
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
        <div style={{ 
          position: 'relative', 
          width: '100%', 
          height: '100%', 
          overflow: 'hidden', 
          transform: `scale(${scale})`,
          transition: 'transform 0.1s linear, border-radius 0.1s linear', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderRadius: `${(1 - scale) * 40}vh`
        }}>
          <img src="https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?q=80&w=2400" alt=""
            style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', opacity: scale < 0.1 ? scale * 10 : 0.85 }} />
          
          {/* Brand Name natively zooms perfectly in sync with the container */}
          <span 
            style={{ position: 'relative', zIndex: 3, fontFamily: 'Cinzel, serif', fontWeight: 600, fontSize: 'clamp(4rem, 12vw, 10rem)', letterSpacing: '0.15em', color: '#fff', textTransform: 'uppercase', textShadow: '0 8px 30px rgba(0,0,0,0.8)', whiteSpace: 'nowrap' }}
          >
            Home Gennie
          </span>
        </div>
      </div>

      {/* Gold dot + caption bottom left */}
      <motion.div
        style={{ position: 'absolute', bottom: 28, left: 36, zIndex: 10, display: 'flex', alignItems: 'center', gap: 10 }}
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.5 }}
      >
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.gold, flexShrink: 0 }} />
        <span style={{ fontFamily: 'Josefin Sans, sans-serif', fontSize: '0.65rem', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)' }}>
          AI Interior Design
        </span>
      </motion.div>

      {/* Counter — bottom right */}
      <div style={{ position: 'absolute', bottom: 20, right: 32, zIndex: 10, lineHeight: 1, textAlign: 'right' }}>
        <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 400, fontSize: 'clamp(3rem, 8vw, 6rem)', color: '#fff', letterSpacing: '-0.02em', opacity: 0.85 }}>
          {String(count).padStart(2, '0')}
        </span>
        <span style={{ fontFamily: 'Josefin Sans', fontSize: '0.9rem', color: '#fff', opacity: 0.4, marginLeft: 2, verticalAlign: 'super' }}>%</span>
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────────────────
   CLIP REVEAL — text slides up from a mask
   Pass `animate` prop to control animation externally
───────────────────────────────────────────────────────── */
function Reveal({ children, delay = 0, style = {}, className = '', animate = 'visible' }) {
  return (
    <div style={{ overflow: 'hidden', ...style }} className={className}>
      <motion.div
        initial={{ y: prefersReducedMotion ? 0 : '108%' }}
        animate={prefersReducedMotion ? {} : {
          y: animate === 'visible' ? 0 : '108%',
          transition: { duration: 1.05, ease: EASE_OUT, delay }
        }}
      >
        {children}
      </motion.div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────
   CURSOR — ambient warm glow
───────────────────────────────────────────────────────── */
function CursorGlow() {
  const x = useMotionValue(-400)
  const y = useMotionValue(-400)
  const sx = useSpring(x, { stiffness: 55, damping: 18 })
  const sy = useSpring(y, { stiffness: 55, damping: 18 })

  useEffect(() => {
    if (prefersReducedMotion) return
    const move = (e) => { x.set(e.clientX); y.set(e.clientY) }
    window.addEventListener('mousemove', move)
    return () => window.removeEventListener('mousemove', move)
  }, [x, y])

  return (
    <motion.div style={{
      position: 'fixed', zIndex: 4, pointerEvents: 'none',
      width: 440, height: 440,
      background: `radial-gradient(circle, rgba(202,138,4,0.06) 0%, transparent 70%)`,
      borderRadius: '50%', left: sx, top: sy,
      translateX: '-50%', translateY: '-50%',
    }} />
  )
}

/* ─────────────────────────────────────────────────────────
   SECTION WRAPPER — fade + slide up on scroll entry
───────────────────────────────────────────────────────── */
function Section({ children, style = {}, id }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.section
      id={id}
      ref={ref}
      style={style}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
    >
      {children}
    </motion.section>
  )
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function Home() {
  const [loading, setLoading]         = useState(true)
  const [heroReady, setHeroReady]     = useState(false)
  const [mouse, setMouse]             = useState({ x: 0, y: 0 })
  const heroRef = useRef(null)

  const handleDone = useCallback(() => {
    setLoading(false)
    setTimeout(() => setHeroReady(true), 60)
  }, [])

  // Mouse parallax for hero cards
  useEffect(() => {
    if (prefersReducedMotion) return
    const hero = heroRef.current
    if (!hero) return
    const onMove = (e) => {
      const r = hero.getBoundingClientRect()
      setMouse({ x: (e.clientX - r.left - r.width / 2) / (r.width / 2), y: (e.clientY - r.top - r.height / 2) / (r.height / 2) })
    }
    hero.addEventListener('mousemove', onMove)
    return () => hero.removeEventListener('mousemove', onMove)
  }, [])

  return (
    <>
      <AnimatePresence>{loading && <Preloader key="pl" onComplete={handleDone} />}</AnimatePresence>
      {!loading && <CursorGlow />}

      {/* ══════════════════════════════════════
          CHAPTER 1 — HERO
          Dark stone #1C1917, gold accents
      ══════════════════════════════════════ */}
      <section
        ref={heroRef}
        style={{
          position: 'relative', width: '100%', minHeight: '100vh',
          background: C.stone900, overflow: 'hidden',
          marginTop: '-80px', paddingTop: 0,
        }}
      >
        {/* Vignette top */}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,0,0,0.6), transparent)', zIndex: 2, pointerEvents: 'none' }} />

        {/* Film grain */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 2, pointerEvents: 'none', opacity: 0.4,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E")`
        }} />

        {/* Ambient gold glow center */}
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 700, height: 500, background: `radial-gradient(ellipse, rgba(202,138,4,0.06) 0%, transparent 70%)`, zIndex: 1, pointerEvents: 'none' }} />

        {/* Text Readability Backdrop layer (above cards z:3, below text z:10) */}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at center, rgba(28,25,23,0.85) 0%, rgba(28,25,23,0) 50%)', zIndex: 4, pointerEvents: 'none' }} />

        {/* ── Floating nav ── */}
        <motion.nav
          style={{
            position: 'absolute', top: 20, left: 20, right: 20, zIndex: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'rgba(28,25,23,0.75)', backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 14, padding: '14px 28px',
          }}
          initial={{ opacity: 0, y: -16 }}
          animate={heroReady ? { opacity: 1, y: 0 } : { opacity: 0, y: -16 }}
          transition={{ duration: 0.8, ease: EASE_OUT, delay: 0.1 }}
        >
          <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 400, fontSize: '0.85rem', letterSpacing: '0.18em', color: '#fff', textTransform: 'uppercase' }}>
            Home Gennie
          </span>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            {[['Home', '/'], ['Gallery', '/gallery'], ['Design', '/upload'], ['Dashboard', '/dashboard']].map(([l, to]) => (
              <Link key={to} to={to} style={{ fontFamily: 'Josefin Sans, sans-serif', fontSize: '0.75rem', fontWeight: 300, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={e => e.target.style.color = '#fff'}
                onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,0.45)'}
              >
                {l}
              </Link>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <Link to="/login" style={{ fontFamily: 'Josefin Sans', fontSize: '0.75rem', fontWeight: 300, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)', textDecoration: 'none' }}>
              Sign In
            </Link>
            <Link to="/signup" style={{ fontFamily: 'Josefin Sans', fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: C.stone950, background: C.gold, textDecoration: 'none', padding: '8px 20px', borderRadius: 8, transition: 'opacity 0.2s', cursor: 'pointer' }}
              onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
              onMouseLeave={e => e.currentTarget.style.opacity = '1'}
            >
              Get Started
            </Link>
          </div>
        </motion.nav>

        {/* ── Hero Room Cards (parallax) ── */}
        {HERO_CARDS.map((card, i) => (
          <motion.div
            key={i}
            style={{
              position: 'absolute', overflow: 'hidden', zIndex: 3,
              borderRadius: 10, boxShadow: '0 16px 60px rgba(0,0,0,0.8)',
              ...card.style,
            }}
            initial={{ opacity: 0, scale: 1.18, y: 20 }}
            animate={heroReady
              ? { opacity: 1, scale: 1, y: 0, x: mouse.x * card.px }
              : { opacity: 0, scale: 1.18, y: 20 }}
            transition={heroReady
              ? { duration: 1.3, ease: EASE_OUT, delay: i * 0.07 }
              : { duration: 0 }}
          >
            <motion.img src={card.src} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              whileHover={{ scale: 1.07 }} transition={{ duration: 1.4, ease: EASE_OUT }}
            />
            <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.08)' }} />
          </motion.div>
        ))}

        {/* ── Center text ── */}
        <motion.div
          style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, textAlign: 'center', padding: '0 1rem' }}
          initial="hidden"
          animate={heroReady ? 'visible' : 'hidden'}
        >
          {/* Eyebrow */}
          <motion.div
            variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { delay: 0.05 } } }}
            style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}
          >
            <div style={{ width: 28, height: 1, background: C.gold, opacity: 0.6 }} />
            <span style={{ fontFamily: 'Josefin Sans, sans-serif', fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)' }}>
              AI-Powered Interior Design
            </span>
            <div style={{ width: 28, height: 1, background: C.gold, opacity: 0.6 }} />
          </motion.div>

          {/* Headline L1 — bold slab */}
          <Reveal delay={heroReady ? 0.12 : 0} animate={heroReady ? 'visible' : 'hidden'}>
            <h1 style={{
              fontFamily: 'Cinzel, serif', fontWeight: 700,
              fontSize: 'clamp(2.2rem, 5.8vw, 6.5rem)',
              lineHeight: 0.95, letterSpacing: '0.04em',
              color: '#fff', textTransform: 'uppercase', margin: 0,
            }}>
              Design That
            </h1>
          </Reveal>

          {/* Headline L2 — italic gold contrast */}
          <Reveal delay={heroReady ? 0.22 : 0} style={{ marginBottom: 28 }} animate={heroReady ? 'visible' : 'hidden'}>
            <h1 style={{
              fontFamily: 'Cinzel, serif', fontWeight: 400,
              fontStyle: 'italic',
              fontSize: 'clamp(2rem, 5.4vw, 6rem)',
              lineHeight: 0.95, letterSpacing: '0.02em',
              color: C.gold, margin: 0,
            }}>
              Belongs to You.
            </h1>
          </Reveal>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            custom={0.38}
            style={{
              fontFamily: 'Josefin Sans, sans-serif', fontWeight: 300,
              fontSize: 'clamp(0.8rem, 1.2vw, 1rem)',
              color: 'rgba(255,255,255,0.38)', maxWidth: 460, lineHeight: 1.9,
              letterSpacing: '0.06em', margin: '0 auto 40px',
            }}
          >
            Upload a photo of your room. Choose a style. Watch AI preserve every wall, window, and corner — and reinvent its soul.
          </motion.p>

          {/* CTA pair */}
          <motion.div variants={fadeUp} custom={0.48} style={{ display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Link to="/upload"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: C.gold, color: C.stone950,
                fontFamily: 'Josefin Sans', fontWeight: 700, fontSize: '0.8rem',
                letterSpacing: '0.1em', textTransform: 'uppercase', textDecoration: 'none',
                padding: '14px 32px', borderRadius: 9, cursor: 'pointer',
                boxShadow: `0 8px 28px rgba(202,138,4,0.35)`,
                transition: 'transform 0.25s ease, box-shadow 0.25s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 12px 36px rgba(202,138,4,0.5)` }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = `0 8px 28px rgba(202,138,4,0.35)` }}
            >
              Start Designing <ArrowUpRight size={14} strokeWidth={2.5} />
            </Link>
            <Link to="/gallery"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.7)',
                fontFamily: 'Josefin Sans', fontWeight: 400, fontSize: '0.8rem',
                letterSpacing: '0.1em', textTransform: 'uppercase', textDecoration: 'none',
                padding: '14px 28px', borderRadius: 9, cursor: 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                transition: 'background 0.25s ease, color 0.25s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#fff' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)' }}
            >
              View Gallery
            </Link>
          </motion.div>

          {/* Scroll hint */}
          <motion.div
            variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { delay: 1.4 } } }}
            style={{ position: 'absolute', bottom: 28, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}
          >
            <motion.div
              style={{ width: 1, height: 40, background: 'rgba(255,255,255,0.15)' }}
              animate={prefersReducedMotion ? {} : { scaleY: [1, 0.45, 1] }}
              transition={{ repeat: Infinity, duration: 2.4, ease: 'easeInOut' }}
            />
            <ChevronDown size={12} color="rgba(255,255,255,0.2)" />
          </motion.div>
        </motion.div>
      </section>

      {/* ── Marquee strip ── */}
      <Marquee />

      {/* ══════════════════════════════════════
          CHAPTER 2 — STATS / VALUE PROP
          Light stone #FAFAF9
      ══════════════════════════════════════ */}
      <Section style={{ background: C.stone50, padding: '100px 0' }} id="stats">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1px', background: C.stone300, borderRadius: 16, overflow: 'hidden', border: `1px solid ${C.stone300}` }}>
            {STATS.map((s, i) => (
              <motion.div
                key={i}
                variants={fadeUp}
                custom={i * 0.1}
                style={{ background: C.stone50, padding: '56px 48px', textAlign: 'center' }}
              >
                <Counter to={s.value} suffix={s.suffix} />
                <p style={{ fontFamily: 'Josefin Sans', fontWeight: 300, fontSize: '0.8rem', letterSpacing: '0.14em', textTransform: 'uppercase', color: C.stone500, marginTop: 12 }}>
                  {s.label}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Pull quote */}
          <motion.div variants={fadeUp} custom={0.2} style={{ textAlign: 'center', marginTop: 80 }}>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 4, marginBottom: 20 }}>
              {[...Array(5)].map((_, i) => <Star key={i} size={16} fill={C.gold} color={C.gold} />)}
            </div>
            <blockquote style={{ fontFamily: 'Cinzel, serif', fontStyle: 'italic', fontWeight: 400, fontSize: 'clamp(1.2rem, 2.5vw, 1.75rem)', color: C.stone900, maxWidth: 640, margin: '0 auto', lineHeight: 1.55, letterSpacing: '0.01em' }}>
              "It preserved every wall and window in my room, then transformed it into a Japandi sanctuary."
            </blockquote>
            <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.75rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: C.stone500, marginTop: 18 }}>
              — Ayesha R., Lahore — Home Gennie User
            </p>
          </motion.div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          CHAPTER 3 — HOW IT WORKS
          Dark stone #1C1917
      ══════════════════════════════════════ */}
      <Section style={{ background: C.stone900, padding: '110px 0' }} id="how">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2.5rem' }}>
          <motion.div variants={fadeUp} custom={0} style={{ marginBottom: 72, textAlign: 'center' }}>
            <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.gold, marginBottom: 16, opacity: 0.8 }}>
              The Process
            </p>
            <h2 style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: 'clamp(1.7rem, 3vw, 2.8rem)', color: '#fff', marginBottom: 14, lineHeight: 1.1, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Three Steps to Perfection
            </h2>
            <p style={{ fontFamily: 'Josefin Sans', fontWeight: 300, fontSize: '0.95rem', color: 'rgba(255,255,255,0.35)', maxWidth: 400, margin: '0 auto', lineHeight: 1.8, letterSpacing: '0.04em' }}>
              From photo to photorealistic redesign in seconds.
            </p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2px' }}>
            {HOW_STEPS.map((step, i) => {
              const Icon = step.icon
              const isCenter = i === 1
              return (
                <motion.div
                  key={i}
                  variants={fadeUp}
                  custom={i * 0.12}
                  style={{
                    padding: '52px 44px',
                    background: isCenter ? C.gold : `rgba(255,255,255,0.03)`,
                    borderRadius: 14, position: 'relative', overflow: 'hidden',
                    border: isCenter ? 'none' : '1px solid rgba(255,255,255,0.06)',
                    cursor: 'default',
                  }}
                  whileHover={prefersReducedMotion ? {} : { y: -6 }}
                  transition={{ duration: 0.35, ease: EASE_OUT }}
                >
                  {/* BG number */}
                  <span style={{ position: 'absolute', top: -8, right: 16, fontFamily: 'Cinzel, serif', fontWeight: 900, fontSize: '6.5rem', color: isCenter ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.03)', lineHeight: 1, userSelect: 'none', letterSpacing: '-0.04em' }}>
                    {step.num}
                  </span>
                  <div style={{ width: 44, height: 44, borderRadius: 10, background: isCenter ? 'rgba(0,0,0,0.12)' : 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 28 }}>
                    <Icon size={20} color={isCenter ? C.stone950 : 'rgba(255,255,255,0.5)'} strokeWidth={1.5} />
                  </div>
                  <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', color: isCenter ? C.stone800 : C.gold, marginBottom: 14, opacity: isCenter ? 0.7 : 0.8 }}>
                    Step {step.num}
                  </p>
                  <h3 style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: '1.25rem', color: isCenter ? C.stone950 : '#fff', marginBottom: 14, lineHeight: 1.2, letterSpacing: '0.03em' }}>
                    {step.title}
                  </h3>
                  <p style={{ fontFamily: 'Josefin Sans', fontWeight: 300, fontSize: '0.88rem', color: isCenter ? C.stone700 : 'rgba(255,255,255,0.35)', lineHeight: 1.8, letterSpacing: '0.03em' }}>
                    {step.desc}
                  </p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          CHAPTER 4 — STYLE GALLERY
          Light stone #FAFAF9
      ══════════════════════════════════════ */}
      <Section style={{ background: C.stone50, padding: '110px 0' }} id="styles">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2.5rem' }}>
          <motion.div variants={fadeUp} custom={0} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 56, flexWrap: 'wrap', gap: '1.5rem' }}>
            <div>
              <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.gold, marginBottom: 14 }}>
                Curated Aesthetics
              </p>
              <h2 style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: 'clamp(1.7rem, 3vw, 2.8rem)', color: C.stone900, lineHeight: 1.05, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 14 }}>
                9 Signature Styles
              </h2>
              <p style={{ fontFamily: 'Josefin Sans', fontWeight: 300, fontSize: '0.88rem', color: C.stone500, lineHeight: 1.8, letterSpacing: '0.04em', maxWidth: 380 }}>
                Each style is precision-tuned to preserve your room's geometry while transforming its personality.
              </p>
            </div>
            <motion.div whileHover={prefersReducedMotion ? {} : { x: 5 }} transition={{ duration: 0.3 }}>
              <Link to="/gallery" style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                fontFamily: 'Josefin Sans', fontSize: '0.72rem', fontWeight: 600,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                color: C.stone900, textDecoration: 'none',
                border: `1px solid ${C.stone300}`, padding: '12px 24px', borderRadius: 8,
                transition: 'border-color 0.2s, background 0.2s', cursor: 'pointer',
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.background = C.goldLight }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = C.stone300; e.currentTarget.style.background = 'transparent' }}
              >
                Browse All <ArrowRight size={13} />
              </Link>
            </motion.div>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
            {STYLES.map((s, i) => (
              <motion.div
                key={i}
                variants={fadeUp}
                custom={i * 0.12}
                style={{ position: 'relative', borderRadius: 14, overflow: 'hidden', aspectRatio: '4/5', cursor: 'pointer', boxShadow: '0 4px 28px rgba(0,0,0,0.08)' }}
                whileHover={prefersReducedMotion ? {} : { y: -8 }}
                transition={{ duration: 0.4, ease: EASE_OUT }}
              >
                <motion.img
                  src={s.img} alt={s.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  whileHover={{ scale: 1.07 }}
                  transition={{ duration: 1.4, ease: EASE_OUT }}
                />
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(12,10,9,0.85) 0%, transparent 55%)' }} />
                <div style={{ position: 'absolute', bottom: 0, left: 0, padding: '28px 28px 32px' }}>
                  <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: C.gold, marginBottom: 8, opacity: 0.85 }}>
                    {s.num}
                  </p>
                  <h3 style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: '1.2rem', color: '#fff', letterSpacing: '0.03em', lineHeight: 1.2 }}>
                    {s.title}
                  </h3>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          CHAPTER 5 — CLIMAX CTA
          Dark stone, gold CTA
      ══════════════════════════════════════ */}
      <Section style={{ padding: '0 2rem 6rem', background: C.stone50 }} id="cta">
        <motion.div
          variants={fadeUp}
          custom={0}
          style={{
            position: 'relative', overflow: 'hidden',
            background: C.stone900, borderRadius: 20,
            padding: 'clamp(72px, 9vw, 110px) clamp(40px, 6vw, 80px)',
            textAlign: 'center', maxWidth: 1200, margin: '0 auto',
          }}
        >
          {/* BG room image */}
          <img
            src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?q=80&w=2000"
            alt="" aria-hidden="true"
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.12 }}
          />
          <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at center, rgba(202,138,4,0.08) 0%, transparent 65%)` }} />

          <div style={{ position: 'relative', zIndex: 2 }}>
            <motion.div variants={fadeUp} custom={0.1} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(202,138,4,0.1)', border: '1px solid rgba(202,138,4,0.2)', borderRadius: 100, padding: '6px 18px', marginBottom: 28 }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.gold }} />
              <span style={{ fontFamily: 'Josefin Sans', fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.16em', textTransform: 'uppercase', color: C.gold }}>
                Start Free Today
              </span>
            </motion.div>

            <motion.h2
              variants={fadeUp} custom={0.18}
              style={{ fontFamily: 'Cinzel, serif', fontWeight: 700, fontSize: 'clamp(1.8rem, 4vw, 3.8rem)', color: '#fff', marginBottom: 18, lineHeight: 1.05, letterSpacing: '0.04em', textTransform: 'uppercase' }}
            >
              Ready to{' '}
              <em style={{ fontStyle: 'italic', fontWeight: 400, color: C.gold }}>Elevate</em>{' '}
              Your Space?
            </motion.h2>

            <motion.p
              variants={fadeUp} custom={0.26}
              style={{ fontFamily: 'Josefin Sans', fontWeight: 300, fontSize: '0.92rem', color: 'rgba(255,255,255,0.35)', maxWidth: 480, margin: '0 auto 48px', lineHeight: 1.85, letterSpacing: '0.05em' }}
            >
              No design skills needed. Just your room, your vision, and our AI — together in seconds.
            </motion.p>

            <motion.div variants={fadeUp} custom={0.34} style={{ display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Link to="/signup" style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: C.gold, color: C.stone950,
                fontFamily: 'Josefin Sans', fontWeight: 700, fontSize: '0.8rem',
                letterSpacing: '0.1em', textTransform: 'uppercase', textDecoration: 'none',
                padding: '16px 40px', borderRadius: 10, cursor: 'pointer',
                boxShadow: `0 10px 36px rgba(202,138,4,0.4)`,
                transition: 'transform 0.25s ease, box-shadow 0.25s ease',
              }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 16px 44px rgba(202,138,4,0.55)` }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = `0 10px 36px rgba(202,138,4,0.4)` }}
              >
                Create My Design <ArrowRight size={15} strokeWidth={2.5} />
              </Link>
              <Link to="/gallery" style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.6)',
                fontFamily: 'Josefin Sans', fontWeight: 400, fontSize: '0.8rem',
                letterSpacing: '0.1em', textTransform: 'uppercase', textDecoration: 'none',
                padding: '16px 32px', borderRadius: 10, cursor: 'pointer',
                border: '1px solid rgba(255,255,255,0.1)',
                transition: 'background 0.25s, color 0.25s',
              }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#fff' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.6)' }}
              >
                View Gallery <Eye size={14} />
              </Link>
            </motion.div>

            {/* Trust signals */}
            <motion.div variants={fadeUp} custom={0.42} style={{ marginTop: 48, display: 'flex', gap: '2.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {[{ icon: Users, label: '12,000+ Designs' }, { icon: Star, label: '4.9 / 5 Rating' }, { icon: Layers, label: '9 Unique Styles' }].map(({ icon: Icon, label }, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon size={14} color={C.gold} strokeWidth={1.5} />
                  <span style={{ fontFamily: 'Josefin Sans', fontSize: '0.72rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.28)' }}>
                    {label}
                  </span>
                </div>
              ))}
            </motion.div>
          </div>
        </motion.div>
      </Section>

      {/* ══════════════ FOOTER ══════════════ */}
      <footer style={{ background: C.stone900, borderTop: `1px solid rgba(255,255,255,0.05)`, padding: '2.5rem 3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 400, fontSize: '0.8rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)' }}>
          Home Gennie
        </span>
        <p style={{ fontFamily: 'Josefin Sans', fontSize: '0.7rem', letterSpacing: '0.08em', color: 'rgba(255,255,255,0.2)' }}>
          © {new Date().getFullYear()} Home Gennie · AI Interior Design Platform
        </p>
        <div style={{ display: 'flex', gap: '2rem' }}>
          {[['Gallery', '/gallery'], ['Design', '/upload'], ['Sign In', '/login']].map(([l, to]) => (
            <Link key={to} to={to} style={{ fontFamily: 'Josefin Sans', fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.25)', textDecoration: 'none', transition: 'color 0.2s', cursor: 'pointer' }}
              onMouseEnter={e => e.target.style.color = C.gold}
              onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,0.25)'}
            >
              {l}
            </Link>
          ))}
        </div>
      </footer>
    </>
  )
}
