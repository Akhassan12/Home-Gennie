import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import * as THREE from 'three'
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js'
import { Maximize2 } from 'lucide-react'
import { THEMES } from './ThreeViewer'

/**
 * ImageRoomViewer
 * ───────────────
 * • Renders the room photo on the inside walls of a Three.js box (cube-projection).
 * • Overlays styled 3D furniture.
 * • Exposes exportGLB() via ref — exports only the furniture (AR-placeable).
 *
 * Fix notes:
 *   - GLTFExporter: we rebuild a *fresh* export scene from scratch (same THREE import)
 *     to avoid the "multiple instances of Three.js" hang.
 *   - Image texture: loaded via an <img> element and drawn to a Canvas to work around
 *     cross-origin restrictions that THREE.TextureLoader can hit with some hosts.
 */
const ImageRoomViewer = forwardRef(function ImageRoomViewer(
  { imageUrl, style = 'Modern', onExportReady },
  ref
) {
  const containerRef = useRef(null)
  const internalsRef = useRef(null)
  const theme = THEMES[style] || THEMES.Modern

  /* ── Expose exportGLB ── */
  useImperativeHandle(ref, () => ({
    exportGLB: () => {
      exportFurnitureGLB(theme, onExportReady)
    }
  }), [theme, onExportReady])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let animId

    /* ── Renderer ── */
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
    renderer.setSize(container.clientWidth, container.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.1
    container.appendChild(renderer.domElement)

    /* ── Scene + Camera ── */
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(theme.bg)

    const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.05, 100)
    camera.position.set(0, 1.6, 3)

    /* ── Lights ── */
    scene.add(new THREE.AmbientLight(0xffffff, 0.65))
    const sun = new THREE.DirectionalLight(0xfff5e0, 1.4)
    sun.position.set(3, 6, 4); sun.castShadow = true
    sun.shadow.mapSize.set(1024, 1024)
    scene.add(sun)
    const fill = new THREE.PointLight(theme.accent, 0.5, 15)
    fill.position.set(-3, 3, 2); scene.add(fill)

    /* ── Room box: load image via canvas to avoid CORS TextureLoader issues ── */
    const addRoomBox = (texture) => {
      if (texture) texture.colorSpace = THREE.SRGBColorSpace
      const roomGeo = new THREE.BoxGeometry(8, 4, 10)
      const tint = new THREE.MeshStandardMaterial({
        color: new THREE.Color(theme.floor).lerp(new THREE.Color(0xb0b0b0), 0.3),
        roughness: 0.9, side: THREE.BackSide,
      })
      const photoMat = texture
        ? new THREE.MeshStandardMaterial({ map: texture, roughness: 0.85, side: THREE.BackSide })
        : tint
      const room = new THREE.Mesh(roomGeo, [tint, tint, tint, tint, photoMat, tint])
      room.position.set(0, 2, 0)
      scene.add(room)
    }

    if (imageUrl) {
      // Load via Image element painted onto an offscreen canvas — bypasses CORS on CDN images
      const img = new window.Image()
      img.crossOrigin = 'anonymous'
      img.onload = () => {
        const canvas = document.createElement('canvas')
        canvas.width = img.naturalWidth || 1024
        canvas.height = img.naturalHeight || 768
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0)
        const texture = new THREE.CanvasTexture(canvas)
        addRoomBox(texture)
      }
      img.onerror = () => addRoomBox(null)
      img.src = imageUrl
    } else {
      addRoomBox(null)
    }

    /* ── Floor ── */
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(8, 10),
      new THREE.MeshStandardMaterial({ color: theme.floor, roughness: 0.85 })
    )
    floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true
    scene.add(floor)

    /* ── Furniture ── */
    const sofaMat = new THREE.MeshStandardMaterial({ color: theme.sofa, roughness: 0.6 })
    const cushionMat = new THREE.MeshStandardMaterial({ color: theme.cushion, roughness: 0.7 })

    // Sofa
    const sofaGroup = new THREE.Group()
    const base = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.5, 0.9), sofaMat)
    base.position.set(0, 0.35, 0); base.castShadow = true; sofaGroup.add(base)
    const back = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.55, 0.15), sofaMat)
    back.position.set(0, 0.72, -0.38); back.castShadow = true; sofaGroup.add(back)
    const armL = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.35, 0.9), sofaMat)
    armL.position.set(-1.03, 0.52, 0); armL.castShadow = true; sofaGroup.add(armL)
    const armR = armL.clone(); armR.position.x = 1.03; sofaGroup.add(armR)
    const c1 = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.4, 0.45), cushionMat)
    c1.position.set(-0.5, 0.78, -0.13); c1.rotation.x = -0.12; c1.castShadow = true; sofaGroup.add(c1)
    const c2 = c1.clone(); c2.position.x = 0.5; sofaGroup.add(c2)
    sofaGroup.position.set(0, 0, -2.5); scene.add(sofaGroup)

    // Coffee table
    const tableGroup = new THREE.Group()
    const tableMat = new THREE.MeshStandardMaterial({ color: 0x2c2c2c, roughness: 0.3, metalness: 0.7 })
    const legMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, roughness: 0.3, metalness: 0.9 })
    const top = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.04, 32), tableMat)
    top.position.y = 0.45; top.castShadow = true; tableGroup.add(top)
    for (let i = 0; i < 3; i++) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.45, 10), legMat)
      const a = (i / 3) * Math.PI * 2
      leg.position.set(Math.cos(a) * 0.32, 0.225, Math.sin(a) * 0.32)
      leg.castShadow = true; tableGroup.add(leg)
    }
    tableGroup.position.set(0, 0, 0); scene.add(tableGroup)

    // Floor lamp
    const lampGroup = new THREE.Group()
    const metalMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.85, roughness: 0.2 })
    const shadeMat = new THREE.MeshStandardMaterial({ color: theme.accent, roughness: 0.6, side: THREE.DoubleSide, emissive: theme.accent, emissiveIntensity: 0.4 })
    lampGroup.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.5, 10), metalMat), { position: { x: 0, y: 0.75, z: 0 } }))
    lampGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 0.06, 24), metalMat))
    const shade = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.35, 24, 1, true), shadeMat)
    shade.position.y = 1.62; lampGroup.add(shade)
    const glow = new THREE.PointLight(theme.accent, 0.6, 5); glow.position.y = 1.55; lampGroup.add(glow)
    lampGroup.position.set(2.5, 0, -2.2); scene.add(lampGroup)

    // Plant
    const plantGroup = new THREE.Group()
    const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.1, 0.28, 16), new THREE.MeshStandardMaterial({ color: 0x8B4513, roughness: 0.85 }))
    pot.position.y = 0.14; plantGroup.add(pot)
    const leaves = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 10), new THREE.MeshStandardMaterial({ color: 0x2d8a4e, roughness: 0.7 }))
    leaves.position.y = 0.5; leaves.scale.set(1, 1.4, 1); plantGroup.add(leaves)
    plantGroup.position.set(-2.2, 0, 0.5); scene.add(plantGroup)

    // Bookshelf
    const shelfMat = new THREE.MeshStandardMaterial({ color: 0x5c4021, roughness: 0.85 })
    const shelfGroup = new THREE.Group()
    shelfGroup.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.3), shelfMat), { position: { x: 0, y: 1, z: 0 } }))
    const bColors = [0xe63946, 0x457b9d, 0x2a9d8f, 0xe9c46a, 0xf4a261]
    for (let i = 0; i < 3; i++) {
      let bx = -0.3
      bColors.forEach(col => {
        const b = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.22, 0.22), new THREE.MeshStandardMaterial({ color: col, roughness: 0.7 }))
        b.position.set(bx, 0.48 + i * 0.55, 0); bx += 0.11; shelfGroup.add(b)
      })
    }
    shelfGroup.position.set(-2.8, 0, -2.5); scene.add(shelfGroup)

    // Rug
    const rug = new THREE.Mesh(new THREE.PlaneGeometry(3, 2.5), new THREE.MeshStandardMaterial({ color: theme.rug, roughness: 0.95 }))
    rug.rotation.x = -Math.PI / 2; rug.position.y = 0.004; scene.add(rug)

    internalsRef.current = { renderer, scene, camera, glow, fill }

    /* ── Manual orbit ── */
    let isDrag = false, px = 0, py = 0, theta = 0, phi = 0.22, radius = 4

    const updateCam = () => {
      camera.position.set(
        Math.sin(theta) * Math.cos(phi) * radius,
        Math.sin(phi) * radius + 1.2,
        Math.cos(theta) * Math.cos(phi) * radius
      )
      camera.lookAt(0, 1.0, -1)
    }
    updateCam()

    const onDown = (e) => { isDrag = true; px = e.clientX ?? e.touches?.[0]?.clientX; py = e.clientY ?? e.touches?.[0]?.clientY }
    const onUp = () => { isDrag = false }
    const onMove = (e) => {
      if (!isDrag) return
      const cx = e.clientX ?? e.touches?.[0]?.clientX
      const cy = e.clientY ?? e.touches?.[0]?.clientY
      theta -= (cx - px) * 0.004
      phi = Math.max(-0.08, Math.min(Math.PI / 2.4, phi + (cy - py) * 0.004))
      px = cx; py = cy; updateCam()
    }
    const onWheel = (e) => { radius = Math.max(1.5, Math.min(7, radius + e.deltaY * 0.005)); updateCam() }

    const el = renderer.domElement
    el.addEventListener('mousedown', onDown)
    el.addEventListener('mouseup', onUp)
    el.addEventListener('mousemove', onMove)
    el.addEventListener('touchstart', onDown, { passive: true })
    el.addEventListener('touchend', onUp)
    el.addEventListener('touchmove', onMove, { passive: true })
    el.addEventListener('wheel', onWheel, { passive: true })

    /* ── Animation ── */
    const clock = new THREE.Clock()
    const animate = () => {
      animId = requestAnimationFrame(animate)
      const t = clock.getElapsedTime()
      if (internalsRef.current) {
        internalsRef.current.glow.intensity = 0.5 + Math.sin(t * 2.5) * 0.1
        internalsRef.current.fill.intensity = 0.4 + Math.sin(t * 1.2) * 0.1
      }
      renderer.render(scene, camera)
    }
    animate()

    /* ── Resize ── */
    const onResize = () => {
      if (!container) return
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', onResize)
      el.removeEventListener('mousedown', onDown)
      el.removeEventListener('mouseup', onUp)
      el.removeEventListener('mousemove', onMove)
      el.removeEventListener('touchstart', onDown)
      el.removeEventListener('touchend', onUp)
      el.removeEventListener('touchmove', onMove)
      el.removeEventListener('wheel', onWheel)
      renderer.dispose()
      if (container.contains(el)) container.removeChild(el)
      internalsRef.current = null
    }
  }, [imageUrl, style])

  return (
    <div className="relative w-full h-full min-h-[450px] rounded-2xl overflow-hidden border border-white/10 bg-[#0d1117]">
      <div ref={containerRef} className="w-full h-full" style={{ touchAction: 'none' }} />
      <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg glass text-xs text-white/50 pointer-events-none">
        🖱️ Drag to orbit · Scroll to zoom
      </div>
      <button
        onClick={() => containerRef.current?.requestFullscreen?.()}
        className="absolute top-4 right-4 w-9 h-9 rounded-xl glass flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-all"
      >
        <Maximize2 size={15} />
      </button>
    </div>
  )
})

export default ImageRoomViewer

/* ─────────────────────────────────────────────────────────────────────────────
 * exportFurnitureGLB
 * ──────────────────
 * Builds a clean, self-contained THREE scene with only the furniture (no room box,
 * no image texture) so the GLB exports fast and renders well in AR.
 * Using a fresh scene avoids the "multiple THREE instances" hang.
 * ───────────────────────────────────────────────────────────────────────────── */
function exportFurnitureGLB(theme, onExportReady) {
  const scene = new THREE.Scene()

  const sofaMat = new THREE.MeshStandardMaterial({ color: theme.sofa, roughness: 0.6 })
  const cushionMat = new THREE.MeshStandardMaterial({ color: theme.cushion, roughness: 0.7 })
  const tableMat = new THREE.MeshStandardMaterial({ color: 0x2c2c2c, roughness: 0.3, metalness: 0.7 })
  const legMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, roughness: 0.3, metalness: 0.9 })
  const metalMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.85, roughness: 0.2 })
  const shadeMat = new THREE.MeshStandardMaterial({ color: theme.accent, roughness: 0.6 })
  const shelfMat = new THREE.MeshStandardMaterial({ color: 0x5c4021, roughness: 0.85 })
  const rugMat = new THREE.MeshStandardMaterial({ color: theme.rug, roughness: 0.95 })

  // Sofa group
  const sg = new THREE.Group()
  const addBox = (g, w, h, d, mat, x, y, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat)
    m.position.set(x, y, z); g.add(m)
  }
  addBox(sg, 2.2, 0.5, 0.9, sofaMat, 0, 0.35, 0)
  addBox(sg, 2.2, 0.55, 0.15, sofaMat, 0, 0.72, -0.38)
  addBox(sg, 0.15, 0.35, 0.9, sofaMat, -1.03, 0.52, 0)
  addBox(sg, 0.15, 0.35, 0.9, sofaMat, 1.03, 0.52, 0)
  addBox(sg, 0.55, 0.4, 0.45, cushionMat, -0.5, 0.78, -0.13)
  addBox(sg, 0.55, 0.4, 0.45, cushionMat, 0.5, 0.78, -0.13)
  sg.position.set(0, 0, -1); scene.add(sg)

  // Coffee table
  const tg = new THREE.Group()
  tg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.04, 32), tableMat), { position: new THREE.Vector3(0, 0.45, 0) }))
  for (let i = 0; i < 3; i++) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.45, 10), legMat)
    const a = (i / 3) * Math.PI * 2; leg.position.set(Math.cos(a) * 0.32, 0.225, Math.sin(a) * 0.32); tg.add(leg)
  }
  scene.add(tg)

  // Lamp
  const lg = new THREE.Group()
  lg.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.5, 10), metalMat), { position: new THREE.Vector3(0, 0.75, 0) }))
  lg.add(new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 0.06, 24), metalMat))
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.35, 24, 1, true), shadeMat)
  shade.position.y = 1.62; lg.add(shade)
  lg.position.set(1.8, 0, -0.8); scene.add(lg)

  // Plant
  const pg = new THREE.Group()
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.1, 0.28, 16), new THREE.MeshStandardMaterial({ color: 0x8B4513, roughness: 0.85 }))
  pot.position.y = 0.14; pg.add(pot)
  const lv = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 10), new THREE.MeshStandardMaterial({ color: 0x2d8a4e, roughness: 0.7 }))
  lv.position.y = 0.5; lv.scale.set(1, 1.4, 1); pg.add(lv)
  pg.position.set(-1.5, 0, 0.5); scene.add(pg)

  // Bookshelf
  const bsg = new THREE.Group()
  bsg.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.3), shelfMat), { position: new THREE.Vector3(0, 1, 0) }))
  const bColors = [0xe63946, 0x457b9d, 0x2a9d8f, 0xe9c46a, 0xf4a261]
  for (let i = 0; i < 3; i++) {
    let bx = -0.3; bColors.forEach(col => {
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.22, 0.22), new THREE.MeshStandardMaterial({ color: col, roughness: 0.7 }))
      b.position.set(bx, 0.48 + i * 0.55, 0); bx += 0.11; bsg.add(b)
    })
  }
  bsg.position.set(-2, 0, -1); scene.add(bsg)

  // Rug
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(3, 2.5), rugMat)
  rug.rotation.x = -Math.PI / 2; rug.position.y = 0.002; scene.add(rug)

  // Export
  const exporter = new GLTFExporter()
  exporter.parse(
    scene,
    (buffer) => {
      const blob = new Blob([buffer], { type: 'model/gltf-binary' })
      onExportReady?.(blob)
    },
    (err) => { console.error('GLB export error:', err); onExportReady?.(null) },
    { binary: true }
  )
}
