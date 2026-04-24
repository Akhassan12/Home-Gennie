import { X, Share2, Box, Target, Calendar, Layers, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import ComparisonSlider from './ComparisonSlider'

export default function DesignDetailModal({ design, onClose }) {
  if (!design) return null

  const originalUrl  = design.original_image_url || design.originalUrl
  const generatedUrl = design.generated_image_url || design.imageUrl
  const roomType     = (design.room_type || 'Space').replace(/_/g, ' ')
  const score        = Math.round((design.score || 0.95) * 100)
  const dateStr      = design.created_at
    ? new Date(design.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Today'

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 animate-fade-in"
      style={{ background: 'rgba(0,0,0,0.82)', backdropFilter: 'blur(16px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-5 right-5 z-[110] flex items-center justify-center transition-all"
        style={{
          width: '40px', height: '40px', borderRadius: '12px',
          background: 'rgba(255,255,255,0.1)',
          border: '1.5px solid rgba(255,255,255,0.15)',
          color: '#fff', cursor: 'pointer',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.18)'}
        onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
      >
        <X size={18} />
      </button>

      {/* Modal card */}
      <div
        className="w-full flex flex-col md:flex-row animate-fade-up overflow-hidden"
        style={{
          maxWidth: '1000px',
          maxHeight: '90vh',
          borderRadius: '28px',
          background: 'var(--bg-card)',
          border: '1.5px solid var(--border-color)',
          boxShadow: '0 32px 80px rgba(0,0,0,0.5), 0 8px 24px rgba(0,0,0,0.3)',
        }}
      >
        {/* LEFT — Comparison Slider */}
        <div
          className="flex-1 flex items-center justify-center overflow-hidden"
          style={{
            background: 'var(--bg-muted)',
            borderRight: '1.5px solid var(--border-color)',
            minHeight: '320px',
          }}
        >
          <ComparisonSlider before={originalUrl} after={generatedUrl} />
        </div>

        {/* RIGHT — Info panel */}
        <div
          className="flex flex-col"
          style={{
            width: '360px',
            flexShrink: 0,
            padding: '2.25rem 2rem',
            overflowY: 'auto',
          }}
        >
          {/* Style + Room chips */}
          <div className="flex items-center gap-2 mb-5 flex-wrap">
            <span
              className="px-3 py-1 rounded-xl text-[11px] font-bold uppercase tracking-widest"
              style={{
                background: 'rgba(99,102,241,0.1)',
                color: 'var(--color-primary-600)',
                border: '1.5px solid rgba(99,102,241,0.2)',
              }}
            >
              {design.style} Style
            </span>
            <span
              className="px-3 py-1 rounded-xl text-[11px] font-bold uppercase tracking-widest capitalize"
              style={{
                background: 'var(--bg-subtle)',
                color: 'var(--text-muted)',
                border: '1.5px solid var(--border-color)',
              }}
            >
              {roomType}
            </span>
          </div>

          {/* Title + desc */}
          <h2
            className="font-display font-extrabold tracking-tight mb-3"
            style={{ fontSize: '1.65rem', color: 'var(--text-primary)', lineHeight: 1.2 }}
          >
            Design<br />Transformation
          </h2>
          <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--text-muted)' }}>
            A professional‑grade {design.style?.toLowerCase()} interior transformation.
            Every element has been optimised for aesthetics and spatial balance.
          </p>

          {/* Stats grid */}
          <div className="flex flex-col gap-3 mb-6">
            {/* Match accuracy */}
            <div
              className="flex items-center justify-between rounded-2xl"
              style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', border: '1.5px solid var(--border-color)' }}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(16,185,129,0.1)', border: '1.5px solid rgba(16,185,129,0.2)' }}>
                  <Target size={15} style={{ color: '#10b981' }} />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>
                  Match Accuracy
                </span>
              </div>
              <span
                className="font-extrabold text-sm px-3 py-1 rounded-xl"
                style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1.5px solid rgba(16,185,129,0.2)' }}
              >
                {score}%
              </span>
            </div>

            {/* Date generated */}
            <div
              className="flex items-center justify-between rounded-2xl"
              style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', border: '1.5px solid var(--border-color)' }}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(99,102,241,0.1)', border: '1.5px solid rgba(99,102,241,0.2)' }}>
                  <Calendar size={15} style={{ color: 'var(--color-primary-500)' }} />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>
                  Date Generated
                </span>
              </div>
              <span className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>{dateStr}</span>
            </div>

            {/* Room type */}
            <div
              className="flex items-center justify-between rounded-2xl"
              style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', border: '1.5px solid var(--border-color)' }}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(245,158,11,0.1)', border: '1.5px solid rgba(245,158,11,0.2)' }}>
                  <Layers size={15} style={{ color: '#f59e0b' }} />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>
                  Room Type
                </span>
              </div>
              <span className="text-xs font-semibold capitalize" style={{ color: 'var(--text-secondary)' }}>{roomType}</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col gap-3 mt-auto">
            <Link
              to={`/viewer?imageUrl=${encodeURIComponent(generatedUrl || '')}&style=${encodeURIComponent(design.style || 'Modern')}`}
              className="flex items-center justify-center gap-2.5 rounded-2xl font-bold text-white no-underline"
              style={{
                padding: '0.95rem',
                fontSize: '0.9rem',
                background: 'linear-gradient(135deg, var(--color-primary-600), #7c3aed)',
                boxShadow: '0 6px 20px rgba(79,70,229,0.3)',
              }}
              onClick={onClose}
            >
              <Box size={18} /> Explore in 3D + AR
            </Link>
            <button
              className="flex items-center justify-center gap-2.5 rounded-2xl font-bold transition-all"
              style={{
                padding: '0.95rem',
                fontSize: '0.9rem',
                background: 'var(--bg-subtle)',
                color: 'var(--text-secondary)',
                border: '1.5px solid var(--border-color)',
                cursor: 'pointer',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--color-primary-300)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-color)'}
            >
              <Share2 size={18} /> Share Design
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
