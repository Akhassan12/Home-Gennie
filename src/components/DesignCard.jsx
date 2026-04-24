import { Heart, Trash2, Box, Image, Clock, Layers } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function DesignCard({ design, onSave, onDelete, onView }) {
  const navigate = useNavigate()

  const imageUrl = design.generated_image_url || design.imageUrl
  const isPending = !imageUrl || imageUrl === 'pending' || imageUrl === ''
  const roomType = design.room_type || design.roomType || 'Room'
  const style    = design.style || 'Custom'
  const score    = design.score || design.match_score || 0.95
  const createdAt = design.created_at || design.generatedAt

  const timeAgo = (dateStr) => {
    if (!dateStr) return ''
    const diff = Date.now() - new Date(dateStr).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    return `${Math.floor(h / 24)}d ago`
  }

  const handleView3D = (e) => {
    e.stopPropagation()
    const params = new URLSearchParams()
    if (imageUrl && !isPending) params.set('imageUrl', imageUrl)
    params.set('style', style)
    params.set('autoGenerate', 'true')
    navigate(`/viewer?${params.toString()}`)
  }

  return (
    <div
      className="design-card group animate-fade-up"
      onClick={() => onView?.(design)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onView?.(design)}
    >
      {/* ── Image Area — taller aspect ratio ── */}
      <div
        className="relative overflow-hidden"
        style={{
          aspectRatio: '16/11',     /* wider, taller — was 4/3 which made it short */
          background: 'var(--bg-muted)',
        }}
      >
        {/* Shimmer while pending */}
        {isPending && <div className="absolute inset-0 animate-shimmer" />}

        {/* Actual image */}
        {!isPending && (
          <img
            src={imageUrl}
            alt={`${style} ${roomType} design`}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            onError={(e) => {
              e.target.style.display = 'none'
              e.target.parentElement.querySelector('.img-fallback').style.display = 'flex'
            }}
          />
        )}

        {/* Fallback for broken URLs */}
        <div
          className="img-fallback absolute inset-0 items-center justify-center flex-col gap-3"
          style={{ display: 'none', background: 'var(--bg-muted)' }}
        >
          <Image size={32} style={{ color: 'var(--text-faint)', opacity: 0.35 }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--text-faint)' }}>Image unavailable</span>
        </div>

        {/* Pending state overlay */}
        {isPending && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3"
            style={{ background: 'var(--bg-muted)' }}>
            <div className="w-9 h-9 border-[2.5px] border-t-transparent rounded-full animate-spin"
              style={{ borderColor: 'var(--color-primary-300)', borderTopColor: 'transparent' }} />
            <span className="text-xs font-semibold" style={{ color: 'var(--text-faint)' }}>Generating…</span>
          </div>
        )}

        {/* Match badge — top left */}
        {!isPending && (
          <div className="absolute top-3.5 left-3.5">
            <div className="badge-success" style={{ fontSize: '0.72rem', padding: '4px 10px' }}>
              {Math.round(score * 100)}% Match
            </div>
          </div>
        )}

        {/* Style chip — top right */}
        <div
          className="absolute top-3.5 right-3.5 px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider"
          style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(8px)', color: '#fff' }}
        >
          {style}
        </div>

        {/* Hover gradient + CTA */}
        {!isPending && (
          <div
            className="absolute inset-0 flex items-end pb-4 px-4 opacity-0 group-hover:opacity-100 transition-all duration-300"
            style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.72) 0%, transparent 55%)' }}
          >
            <button
              onClick={handleView3D}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-xs text-white w-full justify-center"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', boxShadow: '0 4px 16px rgba(79,70,229,0.5)' }}
            >
              <Box size={14} /> Generate 3D Model
            </button>
          </div>
        )}
      </div>

      {/* ── Info Section — more breathing room ── */}
      <div style={{ padding: '1.25rem 1.25rem 1rem' }}>

        {/* Title row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            <h3
              className="font-bold truncate"
              style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: '1.3' }}
            >
              {style} {roomType.replace(/_/g, ' ')}
            </h3>
            {createdAt && (
              <div className="flex items-center gap-1.5 mt-1">
                <Clock size={11} style={{ color: 'var(--text-faint)' }} />
                <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>{timeAgo(createdAt)}</span>
              </div>
            )}
          </div>
          <div
            className="flex items-center gap-1 shrink-0 px-2.5 py-1 rounded-lg"
            style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}
          >
            <Layers size={11} style={{ color: 'var(--color-primary-500)' }} />
            <span className="text-[11px] font-semibold capitalize" style={{ color: 'var(--color-primary-600)' }}>
              {roomType.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        {/* Action bar */}
        <div
          className="flex items-center gap-2 pt-3"
          style={{ borderTop: '1px solid var(--border-color)' }}
        >
          {/* 3D/AR primary action */}
          <button
            onClick={handleView3D}
            className="flex-1 flex items-center justify-center gap-2 rounded-xl font-semibold transition-all"
            style={{
              padding: '0.6rem 0.75rem',
              fontSize: '0.8rem',
              background: 'rgba(79,70,229,0.08)',
              color: 'var(--color-primary-600)',
              border: '1.5px solid rgba(79,70,229,0.15)',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(79,70,229,0.15)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(79,70,229,0.08)'}
          >
            <Box size={14} /> Generate 3D
          </button>

          {/* Save */}
          <button
            onClick={e => { e.stopPropagation(); onSave?.(design) }}
            className="p-2.5 rounded-xl transition-all"
            style={{ color: 'var(--text-faint)', border: '1.5px solid var(--border-color)' }}
            onMouseEnter={e => { e.currentTarget.style.color = '#f43f5e'; e.currentTarget.style.background = 'rgba(244,63,94,0.07)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-faint)'; e.currentTarget.style.background = 'transparent' }}
            title="Save to favorites"
          >
            <Heart size={15} />
          </button>

          {/* Delete */}
          <button
            onClick={e => { e.stopPropagation(); onDelete?.(design) }}
            className="p-2.5 rounded-xl transition-all"
            style={{ color: 'var(--text-faint)', border: '1.5px solid var(--border-color)' }}
            onMouseEnter={e => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.background = 'rgba(239,68,68,0.07)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-faint)'; e.currentTarget.style.background = 'transparent' }}
            title="Delete design"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>
    </div>
  )
}
