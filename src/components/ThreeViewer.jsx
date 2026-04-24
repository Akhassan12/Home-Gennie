import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { Maximize2 } from 'lucide-react'

export const THEMES = {
  Modern: {
    bg: 0x050505,
    floor: 0x111111,
    sofa: 0x2e3a59,   // Indigo
    cushion: 0x944925, // Sienna
    rug: 0x1a1a1a,
    ambient: 0x778899,
    accent: 0xfe9e72,
    fog: 0x050505,
    grid: 0x222222
  },
  Minimalist: {
    bg: 0xfaf9f6,
    floor: 0xefeeeb,
    sofa: 0xd1d1d1,
    cushion: 0x54433e,
    rug: 0xe3e2df,
    ambient: 0xffffff,
    accent: 0x944925,
    fog: 0xfaf9f6,
    grid: 0xdddddd
  },
  Scandinavian: {
    bg: 0xe9e8e5,
    floor: 0xd8d7d4,
    sofa: 0xffffff,
    cushion: 0xfe9e72,
    rug: 0xbac6ec,
    ambient: 0xfff4e6,
    accent: 0xff922b,
    fog: 0xe9e8e5,
    grid: 0xcccccc
  },
  Industrial: {
    bg: 0x1b1c1a,
    floor: 0x252623,
    sofa: 0x45464e,
    cushion: 0x182442,
    rug: 0x3b3b38,
    ambient: 0x4dabf7,
    accent: 0xfe9e72,
    fog: 0x1b1c1a,
    grid: 0x333333
  },
  Classic: {
    bg: 0x1a1a1a,
    floor: 0x0d0d0d,
    sofa: 0x7048e8,
    cushion: 0xfcc419,
    rug: 0x182442,
    ambient: 0xfff9db,
    accent: 0xfcc419,
    fog: 0x1a1a1a,
    grid: 0x2a2a2a
  }
}

export default function ThreeViewer({ style = 'Modern', config = {} }) {
  const containerRef = useRef(null)
  const sceneRef = useRef(null)
  
  const theme = THEMES[style] || THEMES.Modern

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(theme.bg)
    scene.fog = new THREE.Fog(theme.bg, 6, 18)

    // Camera
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100)
    camera.position.set(4, 3, 6)
    camera.lookAt(0, 0.5, 0)

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(container.clientWidth, container.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = config.exposure || 1.2
    container.appendChild(renderer.domElement)

    // Lights
    const ambient = new THREE.AmbientLight(theme.ambient, config.ambientIntensity || 0.4)
    scene.add(ambient)

    const dirLight = new THREE.DirectionalLight(0xffffff, config.dirIntensity || 1.5)
    dirLight.position.set(5, 8, 5)
    dirLight.castShadow = true
    dirLight.shadow.mapSize.width = 1024
    dirLight.shadow.mapSize.height = 1024
    scene.add(dirLight)

    const pointLight = new THREE.PointLight(theme.accent, config.pointIntensity || 0.6, 10)
    pointLight.position.set(-2, 3, 2)
    scene.add(pointLight)

    // Ground
    const floorGeo = new THREE.PlaneGeometry(20, 20)
    const floorMat = new THREE.MeshStandardMaterial({
      color: theme.floor,
      roughness: 0.8,
      metalness: 0.1,
    })
    const floor = new THREE.Mesh(floorGeo, floorMat)
    floor.rotation.x = -Math.PI / 2
    floor.receiveShadow = true
    scene.add(floor)

    // Grid
    const grid = new THREE.GridHelper(20, 40, theme.grid, theme.grid)
    grid.material.opacity = 0.2
    grid.material.transparent = true
    grid.position.y = 0.005
    scene.add(grid)

    // Sofa Group
    const sofaGroup = new THREE.Group()
    const sofaMat = new THREE.MeshStandardMaterial({ color: theme.sofa, roughness: 0.6, metalness: 0.05 })
    const base = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.5, 0.9), sofaMat)
    base.position.set(0, 0.35, 0); base.castShadow = true; sofaGroup.add(base)
    const back = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.5, 0.15), sofaMat)
    back.position.set(0, 0.7, -0.38); back.castShadow = true; sofaGroup.add(back)
    const armL = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.4, 0.9), sofaMat)
    armL.position.set(-1.03, 0.55, 0); armL.castShadow = true; sofaGroup.add(armL)
    const armR = armL.clone(); armR.position.x = 1.03; sofaGroup.add(armR)
    
    const cushionMat = new THREE.MeshStandardMaterial({ color: theme.cushion, roughness: 0.7 })
    const cushion1 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.4, 0.4), cushionMat)
    cushion1.position.set(-0.5, 0.85, -0.15); cushion1.rotation.x = -0.15; cushion1.castShadow = true; sofaGroup.add(cushion1)
    const cushion2 = cushion1.clone(); cushion2.position.x = 0.5; sofaGroup.add(cushion2)

    sofaGroup.position.set(0, 0, -1)
    scene.add(sofaGroup)

    // Orbit controls (manual)
    let isDragging = false, prevX = 0, prevY = 0, theta = Math.PI / 4, phi = Math.PI / 6, radius = 7
    const updateCamera = () => {
      camera.position.x = radius * Math.sin(theta) * Math.cos(phi)
      camera.position.y = radius * Math.sin(phi) + 1
      camera.position.z = radius * Math.cos(theta) * Math.cos(phi)
      camera.lookAt(0, 0.6, 0)
    }
    updateCamera()

    const onPointerDown = (e) => { isDragging = true; prevX = e.clientX; prevY = e.clientY }
    const onPointerUp = () => { isDragging = false }
    const onPointerMove = (e) => {
      if (!isDragging) return
      theta -= (e.clientX - prevX) * 0.005
      phi = Math.max(0.05, Math.min(Math.PI / 2.5, phi + (e.clientY - prevY) * 0.005))
      prevX = e.clientX; prevY = e.clientY; updateCamera()
    }
    const onWheel = (e) => { radius = Math.max(4, Math.min(15, radius + e.deltaY * 0.005)); updateCamera() }

    container.addEventListener('pointerdown', onPointerDown)
    container.addEventListener('pointerup', onPointerUp)
    container.addEventListener('pointermove', onPointerMove)
    container.addEventListener('wheel', onWheel)

    let animationId
    const animate = () => {
      animationId = requestAnimationFrame(animate)
      renderer.render(scene, camera)
    }
    animate()

    const handleResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
    }
    window.addEventListener('resize', handleResize)
    sceneRef.current = { renderer, scene, camera }

    return () => {
      cancelAnimationFrame(animationId); window.removeEventListener('resize', handleResize)
      container.removeEventListener('pointerdown', onPointerDown), container.removeEventListener('pointerup', onPointerUp), container.removeEventListener('pointermove', onPointerMove), container.removeEventListener('wheel', onWheel)
      renderer.dispose(); container.removeChild(renderer.domElement)
    }
  }, [style, config])

  return (
    <div className="relative w-full h-full min-h-[400px] rounded-2xl overflow-hidden">
      <div ref={containerRef} className="w-full h-full" style={{ touchAction: 'none' }} />
      <div className="absolute top-4 right-4 flex gap-2">
        <button onClick={() => containerRef.current?.requestFullscreen?.()} className="w-9 h-9 rounded-lg glass flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 transition">
          <Maximize2 size={16} />
        </button>
      </div>
      <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg bg-black/30 backdrop-blur-md border border-white/5 text-[10px] font-bold uppercase tracking-widest text-white/50 pointer-events-none">
        Drag to orbit · Scroll to zoom
      </div>
    </div>
  )
}
