import { useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { Smartphone, Monitor, AlertCircle, Sparkles, Loader, Box } from 'lucide-react'

export default function True3DViewer({ glbUrl, isGenerating, onGenerate, transform = { scale: 1, rotation: 0 } }) {
  const [qrDataUrl, setQrDataUrl] = useState(null)
  const [isMobile, setIsMobile] = useState(false)
  const [arSupported, setArSupported] = useState(false)
  const [modelReady, setModelReady] = useState(false)
  const mvRef = useRef(null)

  useEffect(() => {
    const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
    setIsMobile(mobile)
    if (navigator.xr) {
      navigator.xr.isSessionSupported('immersive-ar').then(setArSupported).catch(() => setArSupported(false))
    }
  }, [])

  useEffect(() => {
    const mv = mvRef.current
    if (!mv) return
    const onLoad = () => setModelReady(true)
    mv.addEventListener('load', onLoad)
    return () => mv.removeEventListener('load', onLoad)
  }, [glbUrl])

  useEffect(() => {
    if (isMobile) return
    // QR Code for desktop -> Mobile AR URL
    const arUrl = glbUrl 
      ? `${window.location.origin}/viewer?ar=1&glbUrl=${encodeURIComponent(glbUrl)}`
      : `${window.location.origin}/viewer` // Fallback placeholder URL

    QRCode.toDataURL(arUrl, {
      width: 220,
      margin: 2,
      color: { dark: '#ffffff', light: '#0d1117' },
      errorCorrectionLevel: 'M'
    }).then(setQrDataUrl).catch(console.error)
  }, [glbUrl, isMobile])

  if (isGenerating) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', background: '#0d1117', color: '#fff', padding: '3rem', textAlign: 'center', gap: '2rem' }}>
        <div style={{ position: 'relative', width: '80px', height: '80px' }}>
          <div style={{ position: 'absolute', inset: 0, border: '4px solid rgba(76,110,245,0.2)', borderRadius: '50%', animation: 'ping 2s infinite' }} />
          <div style={{ position: 'absolute', inset: 0, border: '4px solid #4c6ef5', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1.5s linear infinite' }} />
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={24} style={{ color: '#4c6ef5', animation: 'pulse 1s infinite' }} />
          </div>
        </div>
        <div>
          <h3 style={{ fontFamily: '"Noto Serif", serif', fontSize: '1.4rem', fontWeight: 700, margin: '0 0 0.5rem' }}>Analyzing Geometry</h3>
          <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.5)', maxWidth: '280px', lineHeight: 1.6 }}>AI is reconstructing the physical 3D mesh from your room design. This takes ~30 seconds.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      
      {/* 3D Canvas / Model-Viewer */}
      <div style={{ flex: 1, position: 'relative', background: '#0d1117' }}>
        {glbUrl ? (
          <>
            {!modelReady && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem', background: '#0d1117', zIndex: 10 }}>
                <Loader size={24} className="animate-spin" style={{ color: '#4c6ef5' }} />
                <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#4c6ef5', textTransform: 'uppercase', letterSpacing: '0.15em' }}>Downloading Textures</span>
              </div>
            )}
            {/* @ts-ignore */}
            <model-viewer
              ref={mvRef}
              src={glbUrl}
              alt="AI-generated 3D interior design"
              ar
              ar-modes="webxr scene-viewer quick-look"
              ar-scale="auto"
              camera-controls
              auto-rotate={false} // USER REQUESTED NO AUTO-ROTATE
              orientation={`0 ${transform.rotation}deg 0`}
              scale={`${transform.scale} ${transform.scale} ${transform.scale}`}
              shadow-intensity="1.5"
              environment-image="neutral"
              exposure="1.0"
              style={{ width: '100%', height: '100%', '--poster-color': 'transparent' }}
            >
              <button slot="ar-button" style={{ 
                position: 'absolute', bottom: '1.5rem', right: '1.5rem', padding: '0.8rem 1.5rem', borderRadius: '12px', background: 'linear-gradient(135deg, #182442, #2e3a59)', color: '#fff', border: 'none', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', boxShadow: '0 8px 20px rgba(0,0,0,0.3)'
              }}>
                📱 Open in AR
              </button>
            </model-viewer>
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'rgba(255,255,255,0.4)', gap: '1rem', padding: '3rem', textAlign: 'center' }}>
            <Box size={40} strokeWidth={1.5} />
            <div>
              <p style={{ margin: '0 0 0.25rem', color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>No Model Generated</p>
              <p style={{ margin: 0, fontSize: '0.8rem' }}>Click the button below to start AI reconstruction.</p>
            </div>
            <button 
              onClick={onGenerate}
              style={{ padding: '0.6rem 1.5rem', background: 'rgba(255,255,255,0.08)', borderRadius: '9999px', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer', marginTop: '0.5rem' }}
            >
              Generate 3D Model
            </button>
          </div>
        )}

        <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', padding: '0.4rem 0.8rem', borderRadius: '8px', background: 'rgba(0,0,0,0.35)', backdropFilter: 'blur(8px)', fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.5)', pointerEvents: 'none' }}>
          Drag to orbit · Scroll to zoom
        </div>
      </div>

      {/* AR QR Section - USER REQUESTED VISIBLE RIGHT AWAY */}
      <div style={{ height: '140px', background: 'rgba(255,255,255,0.03)', borderTop: '1px solid rgba(255,255,255,0.05)', padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div style={{ width: '92px', height: '92px', background: '#fff', borderRadius: '12px', padding: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          {qrDataUrl ? (
            <img src={qrDataUrl} alt="AR QR Code" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          ) : (
             <Loader size={24} className="animate-spin" style={{ color: '#0d1117' }} />
          )}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Smartphone size={16} style={{ color: '#4c6ef5' }} />
            <span style={{ fontFamily: '"Space Grotesk", sans-serif', fontSize: '0.85rem', fontWeight: 700, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Beam to AR Mode</span>
          </div>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', lineHeight: 1.5, maxWidth: '280px' }}>
            Scan with your phone to project this model in your real room using WebXR and ARCore technologies.
          </p>
          <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
            <span style={{ fontSize: '9px', fontWeight: 800, background: 'rgba(61,220,132,0.15)', color: '#3ddc84', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(61,220,132,0.3)' }}>ARCORE</span>
            <span style={{ fontSize: '9px', fontWeight: 800, background: 'rgba(0,122,255,0.15)', color: '#007aff', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(0,122,255,0.3)' }}>ARKIT</span>
          </div>
        </div>
      </div>

    </div>
  )
}
