import { useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { Smartphone, Monitor, AlertCircle, ExternalLink, RotateCcw } from 'lucide-react'

/**
 * ARViewer
 * ────────
 * Given a GLB blob (exported from ImageRoomViewer), shows:
 *   1. A <model-viewer> web component with full 3D + AR support
 *      - Android Chrome  → WebXR / Scene Viewer (tap to place on floor)
 *      - iOS Safari      → AR Quick Look (native ARKit)
 *   2. A QR code on desktop so the user can open the AR view on their phone
 *
 * model-viewer is loaded as a CDN <script> in index.html.
 */
export default function ARViewer({ glbBlob, onClose }) {
  const [blobUrl, setBlobUrl] = useState(null)
  const [qrDataUrl, setQrDataUrl] = useState(null)
  const [isMobile, setIsMobile] = useState(false)
  const [arSupported, setArSupported] = useState(false)
  const [modelReady, setModelReady] = useState(false)
  const mvRef = useRef(null)
  const mvContainerRef = useRef(null)

  /* ── Detect mobile + WebXR AR support ── */
  useEffect(() => {
    const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
    setIsMobile(mobile)

    if (navigator.xr) {
      navigator.xr.isSessionSupported('immersive-ar')
        .then(supported => setArSupported(supported))
        .catch(() => setArSupported(false))
    }
  }, [])

  /* ── model-viewer load event (custom element requires addEventListener) ── */
  useEffect(() => {
    const mv = mvRef.current
    if (!mv) return
    const onLoad = () => setModelReady(true)
    mv.addEventListener('load', onLoad)
    return () => mv.removeEventListener('load', onLoad)
  }, [blobUrl])

  /* ── Create object URL from blob + generate QR ── */
  useEffect(() => {
    if (!glbBlob) return
    const url = URL.createObjectURL(glbBlob)
    setBlobUrl(url)

    // On desktop, generate a QR code containing the full viewer URL + glbUrl
    // (glbUrl is passed as a query param so the phone can load it directly)
    if (!isMobile) {
      const arUrl = `${window.location.origin}/viewer?glbUrl=${encodeURIComponent(url)}`
      QRCode.toDataURL(arUrl, {
        width: 220,
        margin: 2,
        color: { dark: '#ffffff', light: '#0d1117' },
        errorCorrectionLevel: 'M'
      }).then(setQrDataUrl).catch(console.error)
    }

    return () => URL.revokeObjectURL(url)
  }, [glbBlob, isMobile])

  /* ── Trigger AR session programmatically ── */
  const launchAR = () => {
    if (mvRef.current) {
      mvRef.current.activateAR()
    }
  }

  if (!glbBlob) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-12 text-center gap-4">
        <AlertCircle size={40} className="text-surface-600" />
        <p className="text-surface-500 text-sm">Export the 3D scene first to launch AR.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full gap-4">
      {/* model-viewer */}
      <div className="relative flex-1 rounded-2xl overflow-hidden border border-white/10 bg-[#0d1117] min-h-[420px]">
        {/* loading state */}
        {!modelReady && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10">
            <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-surface-500 text-xs uppercase tracking-widest">Preparing 3D model…</p>
          </div>
        )}

        {blobUrl && (
          /* @ts-ignore — model-viewer is a custom element registered via CDN */
          <model-viewer
            ref={mvRef}
            src={blobUrl}
            alt="AI-generated interior design room"
            ar
            ar-modes="webxr scene-viewer quick-look"
            ar-scale="auto"
            camera-controls
            auto-rotate
            auto-rotate-delay="500"
            rotation-per-second="10deg"
            shadow-intensity="1.2"
            shadow-softness="0.8"
            environment-image="neutral"
            exposure="1.1"
            style={{
              width: '100%',
              height: '100%',
              minHeight: '420px',
              '--poster-color': '#0d1117',
            }}
          >
            {/* Custom AR button slot inside model-viewer */}
            <button
              slot="ar-button"
              style={{
                position: 'absolute',
                bottom: '16px',
                right: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                background: 'linear-gradient(135deg, #4c6ef5, #364fc7)',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 4px 20px rgba(76,110,245,0.45)',
              }}
            >
              📱 View in AR
            </button>
          </model-viewer>
        )}

        {/* Orbit hint */}
        <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg glass text-xs text-white/40 pointer-events-none">
          🖱️ Drag to orbit · Scroll to zoom
        </div>
      </div>

      {/* Bottom: mobile AR button OR desktop QR */}
      {isMobile ? (
        /* Mobile: direct AR launch */
        <div className="flex gap-3">
          <button
            onClick={launchAR}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            <Smartphone size={16} />
            {arSupported ? 'Launch AR (Point at floor)' : 'View in AR'}
          </button>
          {!arSupported && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/4 border border-white/10 text-xs text-surface-500">
              <AlertCircle size={13} />
              WebXR not supported — try Chrome on Android or Safari on iOS
            </div>
          )}
        </div>
      ) : (
        /* Desktop: QR code to open on phone */
        <div className="glass-card p-5 flex items-center gap-6">
          <div className="shrink-0">
            {qrDataUrl ? (
              <img src={qrDataUrl} alt="QR code" className="w-[90px] h-[90px] rounded-xl" />
            ) : (
              <div className="w-[90px] h-[90px] rounded-xl bg-surface-900 animate-pulse" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Monitor size={14} className="text-primary-400" />
              <span className="text-sm font-semibold text-white">Open on your phone</span>
            </div>
            <p className="text-xs text-surface-500 mb-3 max-w-xs">
              Scan the QR code with your phone (on the same Wi-Fi) to launch this room in AR using your camera.
            </p>
            <div className="flex items-center gap-3 flex-wrap">
              <span className="px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20 text-[10px] font-bold text-green-400 uppercase tracking-widest">
                Android → ARCore
              </span>
              <span className="px-2 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-[10px] font-bold text-blue-400 uppercase tracking-widest">
                iOS → AR Quick Look
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
