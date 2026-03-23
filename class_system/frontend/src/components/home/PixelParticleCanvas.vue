<template>
  <canvas ref="canvasEl" class="pixel-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useThemeStore } from '@/stores/theme'

const canvasEl = ref(null)
const themeStore = useThemeStore()
let ctx = null, animId = null, ro = null, time = 0

// Grid spacing between dots
const SPACING = 18
// Dot radius base and max scale
const DOT_R_BASE = 1.0
const DOT_R_MAX  = 4.0

// Wave rings: multiple expanding rings from top-right
const rings = []
const RING_SPEED    = 1.4   // px per frame — gap = 1.4×60×2s = 168px > wave width
const RING_MS       = 2000  // ms between rings — 2 seconds
const RING_MAX_R    = 4000  // must exceed max dist from origin to any corner
let lastRingTime = 0

// Origin: top-right area
let originX = 0, originY = 0
let cols = 0, rows = 0, W = 0, H = 0

function spawnRing() {
  rings.push({ r: 0, alpha: 0.9 })
}

function resize() {
  const cv = canvasEl.value
  // Use full viewport so waves span the entire page regardless of container size
  W = cv.width  = window.innerWidth
  H = cv.height = window.innerHeight
  // Origin always at top-right corner of the viewport
  originX = W
  originY = 0
  cols = Math.ceil(W / SPACING) + 2
  rows = Math.ceil(H / SPACING) + 2
}

function distToOrigin(x, y) {
  const dx = x - originX, dy = y - originY
  return Math.sqrt(dx * dx + dy * dy)
}

// Brightness based on proximity to origin (top-right brighter)
function baseBrightness(x, y) {
  const maxDist = Math.sqrt(W * W + H * H)
  const d = distToOrigin(x, y)
  return Math.max(0, 1 - d / (maxDist * 0.65))
}

// Wave influence: how much a ring at radius r affects point at dist d
function waveInfluence(dist, ringR) {
  const diff = Math.abs(dist - ringR)
  const width = 200 + ringR * 0.012
  if (diff > width) return 0
  const t = 1 - diff / width
  // smootherstep (5th-order) — soft edge transition
  return t * t * t * (t * (t * 6 - 15) + 10)
}

function draw() {
  ctx.clearRect(0, 0, W, H)

  // Draw dots
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const x = col * SPACING
      const y = row * SPACING

      const dist = distToOrigin(x, y)
      const base = baseBrightness(x, y)

      // Take max influence across all rings — prevents valleys filling up
      let waveAmp = 0
      for (const ring of rings) {
        const inf = waveInfluence(dist, ring.r) * ring.alpha
        if (inf > waveAmp) waveAmp = inf
      }

      // Subtle ambient oscillation
      const ambient = 0.04 * Math.sin(time * 0.012 + dist * 0.008)

      const brightness = Math.min(1, base * 0.35 + waveAmp * 0.50 + ambient)
      if (brightness < 0.015) continue

      // Color: bright blue in light mode, dim cyan-teal in dark mode
      let r, g, b
      if (themeStore.theme === 'light') {
        r = Math.round(30 + brightness * 60)
        g = Math.round(100 + brightness * 80)
        b = Math.round(220 + brightness * 35)
      } else {
        r = Math.round(brightness * 50)
        g = Math.round(140 + brightness * 60)
        b = Math.round(160 + brightness * 50)
      }
      const a = Math.min(0.8, brightness * 0.9)

      // Size: base + wave pulse + proximity boost
      const dotR = DOT_R_BASE + (DOT_R_MAX - DOT_R_BASE) * Math.min(1, waveAmp * 1.1 + base * 0.35)

      ctx.beginPath()
      ctx.arc(x, y, dotR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${r},${g},${b},${a.toFixed(3)})`
      ctx.fill()
    }
  }

  // Draw coordinate HUD (terminal style)
  drawHUD()
}

function drawHUD() {
  const hudColor = themeStore.theme === 'light' ? '30,120,255' : '0,210,180'
  ctx.font = '10px "JetBrains Mono", monospace'
  ctx.fillStyle = `rgba(${hudColor},0.22)`
  ctx.fillText(`SYS:GRID ${cols}×${rows}`, 14, H - 28)
  ctx.fillStyle = `rgba(${hudColor},0.14)`
  ctx.fillText(`ORIGIN [${Math.round(originX)}, ${Math.round(originY)}]`, 14, H - 14)
}

function update(now) {
  time++
  if (now - lastRingTime >= RING_MS) {
    lastRingTime = now
    spawnRing()
  }

  for (let i = rings.length - 1; i >= 0; i--) {
    const ring = rings[i]
    ring.r += RING_SPEED
    // Fade out slowly — keep visible all the way to the edges
    const t = ring.r / RING_MAX_R
    ring.alpha = Math.max(0, 0.9 * (1 - t * t))
    if (ring.r > RING_MAX_R) rings.splice(i, 1)
  }
}

function loop(now) {
  update(now)
  draw()
  animId = requestAnimationFrame(loop)
}

onMounted(() => {
  ctx = canvasEl.value.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  lastRingTime = performance.now()
  // Seed rings spaced by ~500px so gaps are visible on load
  spawnRing(); rings[0].r = 500
  spawnRing(); rings[1].r = 1000
  spawnRing(); rings[2].r = 1500
  ro = new ResizeObserver(resize)
  ro.observe(canvasEl.value)
  loop()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', resize)
  ro?.disconnect()
})
</script>

<style scoped>
.pixel-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 0;
}
</style>
