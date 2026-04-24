import { useState, useRef } from 'react'
import { Upload, X, Image as ImageIcon, CheckCircle } from 'lucide-react'

export default function ImageUploader({ onImageSelected }) {
  const [preview, setPreview] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
  const MAX_SIZE = 10 * 1024 * 1024

  const processFile = (file) => {
    setError(null)
    if (!ACCEPTED.includes(file.type)) {
      setError('Please upload a JPG, PNG, or WebP image.')
      return
    }
    if (file.size > MAX_SIZE) {
      setError('File size exceeds 10 MB limit.')
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    onImageSelected?.(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) processFile(file)
  }

  const clearImage = () => {
    setPreview(null)
    setError(null)
    onImageSelected?.(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="w-full">
      {error && (
        <div className="mb-3 px-4 py-3 rounded-xl text-sm font-medium"
          style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.18)', color: '#dc2626' }}>
          ⚠️ {error}
        </div>
      )}

      {preview ? (
        <div className="relative rounded-2xl overflow-hidden group"
          style={{ border: '2px solid rgba(99,102,241,0.25)', boxShadow: '0 4px 20px rgba(99,102,241,0.1)' }}>
          <img src={preview} alt="Room preview" className="w-full object-cover" style={{ maxHeight: '280px' }} />

          {/* Hover overlay */}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center"
            style={{ background: 'rgba(0,0,0,0.45)' }}>
            <button
              onClick={clearImage}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm text-white"
              style={{ background: 'rgba(239,68,68,0.85)', backdropFilter: 'blur(8px)' }}
            >
              <X size={16} /> Remove Image
            </button>
          </div>

          {/* Ready badge */}
          <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold"
            style={{ background: 'rgba(16,185,129,0.9)', color: '#fff', backdropFilter: 'blur(8px)' }}>
            <CheckCircle size={12} /> Ready to generate
          </div>
        </div>
      ) : (
        <label
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className="flex flex-col items-center justify-center w-full cursor-pointer transition-all duration-300"
          style={{
            minHeight: '220px',
            borderRadius: '20px',
            border: `2px dashed ${dragOver ? 'var(--color-primary-400)' : 'var(--border-strong)'}`,
            background: dragOver ? 'rgba(99,102,241,0.06)' : 'var(--bg-subtle)',
            padding: '3rem 2rem',
          }}
        >
          <input type="file" ref={inputRef} className="hidden" accept=".jpg,.jpeg,.png,.webp" onChange={handleChange} />

          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 transition-all"
            style={{ background: dragOver ? 'rgba(99,102,241,0.12)' : 'var(--bg-muted)', border: '1.5px solid var(--border-color)' }}>
            {dragOver
              ? <Upload size={28} style={{ color: 'var(--color-primary-500)' }} />
              : <ImageIcon size={28} style={{ color: 'var(--text-faint)' }} />
            }
          </div>

          <p className="text-base font-semibold mb-2" style={{ color: dragOver ? 'var(--color-primary-600)' : 'var(--text-primary)' }}>
            {dragOver ? 'Drop your image here' : 'Drag & drop your room photo'}
          </p>
          <p className="text-sm mb-4" style={{ color: 'var(--text-faint)' }}>
            or <span style={{ color: 'var(--color-primary-600)', fontWeight: 600 }}>click to browse</span>
          </p>
          <div className="flex items-center gap-3">
            {['JPG', 'PNG', 'WebP'].map(f => (
              <span key={f} className="px-2.5 py-1 rounded-lg text-xs font-semibold"
                style={{ background: 'var(--bg-muted)', color: 'var(--text-faint)', border: '1px solid var(--border-color)' }}>
                {f}
              </span>
            ))}
            <span className="text-xs" style={{ color: 'var(--text-faint)' }}>· Max 10 MB</span>
          </div>
        </label>
      )}
    </div>
  )
}
