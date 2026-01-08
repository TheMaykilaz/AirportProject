import { useEffect, useRef } from 'react'
import { Paper, Typography, Box } from '@mui/material'

// Simple interactive globe card with animated flight arcs
// No external deps; canvas-based to match black-orange theme
export default function GlobeCard({ title = 'Глобус перельотів' }) {
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const stateRef = useRef({
    rotY: 0.8, // longitude rotation
    rotX: -0.2, // latitude tilt
    vx: 0.003,
    width: 0,
    height: 0,
  })

  // Example routes: [fromLat, fromLon, toLat, toLon]
  const routes = [
    [50.45, 30.52, 40.71, -74.01],  // Kyiv -> New York
    [50.45, 30.52, 51.50, -0.12],   // Kyiv -> London
    [50.45, 30.52, 48.85, 2.35],    // Kyiv -> Paris
    [50.45, 30.52, 25.20, 55.27],   // Kyiv -> Dubai
    [50.45, 30.52, 35.68, 139.69],  // Kyiv -> Tokyo
  ]

  // Extremely simplified coastline/continent polylines (lat, lon arrays)
  // This is a lightweight sketch meant just for visual context, not for accuracy.
  const COASTS = [
    // Europe outline (very rough)
    [
      [71, -25], [70, -10], [65, -5], [60, 5], [58, 10], [55, 15], [52, 20], [45, 20], [40, 30], [45, 35], [42, 40], [38, 27], [36, 20], [35, 10], [40, 0], [45, -5], [50, -10], [55, -15], [60, -15], [65, -20], [68, -20], [71, -25]
    ],
    // Africa west-to-south-to-east (very rough)
    [
      [37, -17], [20, -17], [10, -10], [5, -5], [0, 0], [-5, 5], [-10, 10], [-15, 15], [-20, 20], [-25, 25], [-30, 28], [-35, 30], [-35, 35], [-30, 40], [-20, 45], [-10, 50], [0, 50], [10, 48], [15, 45], [25, 40], [30, 35], [32, 25], [33, 20], [30, 15], [28, 10], [25, 5], [22, 0], [20, -5], [18, -10], [15, -12], [12, -15], [10, -15], [7, -16], [5, -16], [0, -16], [-5, -15], [-10, -14], [-15, -12]
    ],
    // Asia (northern arc and east coast very rough)
    [
      [77, 30], [70, 50], [65, 60], [60, 70], [55, 90], [50, 110], [45, 120], [40, 130], [35, 140], [30, 145], [25, 150], [20, 150], [15, 145], [10, 140], [5, 130], [10, 120], [15, 110], [20, 100], [25, 90], [30, 80], [35, 70], [40, 60], [45, 55], [50, 50], [55, 45], [60, 40], [65, 35], [70, 30]
    ],
    // North America (very rough)
    [
      [72, -170], [65, -160], [60, -150], [55, -140], [50, -130], [48, -125], [45, -120], [40, -125], [35, -120], [30, -115], [25, -110], [20, -105], [20, -100], [25, -95], [30, -90], [35, -85], [40, -80], [45, -75], [50, -70], [55, -65], [60, -80], [65, -100], [68, -120], [70, -140], [72, -160], [72, -170]
    ],
    // South America (very rough)
    [
      [10, -80], [5, -78], [0, -78], [-5, -78], [-10, -75], [-15, -70], [-20, -65], [-25, -60], [-30, -58], [-35, -58], [-45, -63], [-50, -70], [-50, -73], [-45, -75], [-40, -75], [-35, -70], [-30, -65], [-25, -60], [-20, -55], [-15, -55], [-10, -55], [-5, -60], [0, -65], [5, -70], [10, -75]
    ],
    // Australia (very rough)
    [
      [-10, 130], [-15, 130], [-20, 135], [-25, 138], [-30, 140], [-35, 145], [-38, 150], [-35, 155], [-30, 155], [-25, 152], [-20, 148], [-15, 142], [-12, 137], [-10, 132]
    ]
  ]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const resize = () => {
      const parent = canvas.parentElement
      const w = parent.clientWidth
      const h = Math.min(420, Math.max(280, Math.round(w * 0.5)))
      canvas.width = w * devicePixelRatio
      canvas.height = h * devicePixelRatio
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0)
      stateRef.current.width = w
      stateRef.current.height = h
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas.parentElement)

    const toRad = (d) => (d * Math.PI) / 180

    const project = (lat, lon) => {
      const { rotY, rotX } = stateRef.current
      // convert to 3D unit vector
      const latR = toRad(lat)
      const lonR = toRad(lon)
      let x = Math.cos(latR) * Math.cos(lonR)
      let y = Math.sin(latR)
      let z = Math.cos(latR) * Math.sin(lonR)
      // rotate around Y (lon)
      const cosy = Math.cos(rotY), siny = Math.sin(rotY)
      let x1 = cosy * x + siny * z
      let z1 = -siny * x + cosy * z
      // rotate around X (lat)
      const cosx = Math.cos(rotX), sinx = Math.sin(rotX)
      let y2 = cosx * y - sinx * z1
      let z2 = sinx * y + cosx * z1
      // perspective (orthographic)
      return { x: x1, y: y2, z: z2 }
    }

    const draw = () => {
      const { width: w, height: h } = stateRef.current
      ctx.clearRect(0, 0, w, h)
      const r = Math.min(w, h) * 0.42
      const cx = w / 2
      const cy = h / 2

      // background glow
      const glow = ctx.createRadialGradient(cx, cy, r * 0.2, cx, cy, r * 1.3)
      glow.addColorStop(0, 'rgba(255,153,0,0.08)')
      glow.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = glow
      ctx.fillRect(0, 0, w, h)

      // sphere
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.fillStyle = '#0e0e0e'
      ctx.fill()
      ctx.strokeStyle = 'rgba(255,153,0,0.25)'
      ctx.lineWidth = 1
      ctx.stroke()

      // graticule
      ctx.lineWidth = 0.5
      ctx.strokeStyle = 'rgba(255,153,0,0.18)'
      for (let lat = -60; lat <= 60; lat += 30) {
        ctx.beginPath()
        let started = false
        for (let lon = -180; lon <= 180; lon += 5) {
          const p = project(lat, lon)
          if (p.z < 0) continue
          const px = cx + p.x * r
          const py = cy - p.y * r
          if (!started) {
            ctx.moveTo(px, py)
            started = true
          } else {
            ctx.lineTo(px, py)
          }
        }
        ctx.stroke()
      }
      for (let lon = -150; lon <= 150; lon += 30) {
        ctx.beginPath()
        let started = false
        for (let lat = -80; lat <= 80; lat += 5) {
          const p = project(lat, lon)
          if (p.z < 0) continue
          const px = cx + p.x * r
          const py = cy - p.y * r
          if (!started) { ctx.moveTo(px, py); started = true } else { ctx.lineTo(px, py) }
        }
        ctx.stroke()
      }

      // coastlines (front hemisphere only)
      ctx.lineWidth = 1
      ctx.strokeStyle = 'rgba(255,153,0,0.35)'
      ctx.fillStyle = 'rgba(255,153,0,0.05)'
      COASTS.forEach(poly => {
        ctx.beginPath()
        let started = false
        for (let i = 0; i < poly.length; i++) {
          const [la, lo] = poly[i]
          const p = project(la, lo)
          if (p.z < 0) { started = false; continue }
          const px = cx + p.x * r
          const py = cy - p.y * r
          if (!started) { ctx.moveTo(px, py); started = true } else { ctx.lineTo(px, py) }
        }
        ctx.closePath()
        ctx.stroke()
        ctx.fill()
      })

      // flight arcs
      routes.forEach(([la1, lo1, la2, lo2], i) => {
        const steps = 60
        ctx.beginPath()
        let started = false
        for (let t = 0; t <= steps; t++) {
          const a = t / steps
          // slerp between two points on sphere
          const A = project(la1, lo1)
          const B = project(la2, lo2)
          // use unprojected 3D vectors for smoother arcs
          const toVec = (lat, lon) => {
            const latR = toRad(lat), lonR = toRad(lon)
            return [Math.cos(latR) * Math.cos(lonR), Math.sin(latR), Math.cos(latR) * Math.sin(lonR)]
          }
          const v1 = toVec(la1, lo1)
          const v2 = toVec(la2, lo2)
          const dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
          const omega = Math.acos(Math.max(-1, Math.min(1, dot)))
          const sinO = Math.sin(omega) || 1
          const k1 = Math.sin((1 - a) * omega) / sinO
          const k2 = Math.sin(a * omega) / sinO
          const vx = v1[0]*k1 + v2[0]*k2
          const vy = v1[1]*k1 + v2[1]*k2
          const vz = v1[2]*k1 + v2[2]*k2
          // add a small arc height
          const scale = 1 + 0.08 * Math.sin(Math.PI * a)
          const p3 = { x: vx * scale, y: vy * scale, z: vz * scale }
          // rotate like project()
          const { rotY, rotX } = stateRef.current
          const cosy = Math.cos(rotY), siny = Math.sin(rotY)
          const x1 = cosy * p3.x + siny * p3.z
          const z1 = -siny * p3.x + cosy * p3.z
          const cosx = Math.cos(rotX), sinx = Math.sin(rotX)
          const y2 = cosx * p3.y - sinx * z1
          const z2 = sinx * p3.y + cosx * z1
          if (z2 < 0) continue // back side hidden
          const px = cx + x1 * r
          const py = cy - y2 * r
          if (!started) { ctx.moveTo(px, py); started = true } else { ctx.lineTo(px, py) }
        }
        ctx.strokeStyle = `rgba(255, ${160 + (i*15)%80}, 0, 0.85)`
        ctx.lineWidth = 1.6
        ctx.shadowColor = 'rgba(255,153,0,0.35)'
        ctx.shadowBlur = 6
        ctx.stroke()
        ctx.shadowBlur = 0
      })
    }

    const tick = () => {
      const s = stateRef.current
      s.rotY += s.vx
      draw()
      animRef.current = requestAnimationFrame(tick)
    }
    tick()

    const onPointerMove = (e) => {
      const rect = canvas.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width - 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5
      stateRef.current.rotX = -y * 0.8
      stateRef.current.vx = 0.003 + x * 0.01
    }
    canvas.addEventListener('pointermove', onPointerMove)

    return () => {
      cancelAnimationFrame(animRef.current)
      canvas.removeEventListener('pointermove', onPointerMove)
      ro.disconnect()
    }
  }, [])

  return (
    <Paper elevation={3} sx={{ p: 2, bgcolor: '#0f0f0f', border: '1px solid rgba(255,153,0,0.2)', borderRadius: 2 }}>
      <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>{title}</Typography>
      <Box sx={{ width: '100%' }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: 320, display: 'block', borderRadius: 12 }} />
      </Box>
    </Paper>
  )
}
