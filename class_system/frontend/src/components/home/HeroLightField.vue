<template>
  <div
    ref="fieldRef"
    class="hero-light-field"
    :class="{
      'hero-light-field--compact': compactMode,
      'hero-light-field--reduced': reducedMotion
    }"
    @pointermove="handlePointerMove"
    @pointerleave="handlePointerLeave"
  >
    <canvas ref="canvasRef" class="hero-light-field__canvas"></canvas>

    <svg
      class="hero-light-field__overlay"
      viewBox="0 0 640 520"
      role="presentation"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="hero-beam-a" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="rgba(84, 166, 255, 0)" />
          <stop offset="48%" stop-color="#54a6ff" stop-opacity="0.78" />
          <stop offset="100%" stop-color="rgba(84, 166, 255, 0)" />
        </linearGradient>
        <linearGradient id="hero-beam-b" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="rgba(140, 240, 228, 0)" />
          <stop offset="50%" stop-color="#8cf0e4" stop-opacity="0.74" />
          <stop offset="100%" stop-color="rgba(140, 240, 228, 0)" />
        </linearGradient>
        <radialGradient id="hero-core-glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stop-color="#f3fbff" stop-opacity="0.92" />
          <stop offset="30%" stop-color="#8ecdfd" stop-opacity="0.34" />
          <stop offset="100%" stop-color="#0d2349" stop-opacity="0" />
        </radialGradient>
      </defs>

      <g class="hero-overlay__grid">
        <path d="M44 100 H596" />
        <path d="M44 260 H596" />
        <path d="M44 420 H596" />
        <path d="M120 44 V476" />
        <path d="M320 44 V476" />
        <path d="M520 44 V476" />
      </g>

      <g class="hero-overlay__beams" :transform="overlayTransform">
        <path d="M86 410 C188 290 280 220 446 122" class="hero-overlay__beam hero-overlay__beam--a" />
        <path d="M212 438 C302 334 398 286 564 176" class="hero-overlay__beam hero-overlay__beam--b" />
      </g>

      <g class="hero-overlay__core" :transform="coreTransform">
        <circle cx="0" cy="0" r="112" class="hero-overlay__core-glow" />
        <circle cx="0" cy="0" r="26" class="hero-overlay__core-dot" />
      </g>

      <g class="hero-overlay__orbits" :transform="overlayTransform">
        <circle cx="318" cy="258" r="78" class="hero-overlay__orbit" />
        <circle cx="318" cy="258" r="138" class="hero-overlay__orbit hero-overlay__orbit--mid" />
        <circle cx="318" cy="258" r="192" class="hero-overlay__orbit hero-overlay__orbit--outer" />
      </g>
    </svg>

    <div class="hero-light-field__hud">
      <div
        v-for="beacon in beacons"
        :key="beacon.title"
        class="hero-light-field__label"
        :style="getBeaconStyle(beacon)"
      >
        <span>{{ beacon.title }}</span>
        <strong>{{ beacon.value }}</strong>
      </div>
    </div>

    <div class="hero-light-field__scanline"></div>
    <div class="hero-light-field__vignette"></div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const beacons = [
  { title: 'Graph heat', value: '128 links', top: '13%', left: '12%', drift: -14 },
  { title: 'Active source', value: 'Courseware', top: '22%', right: '10%', drift: 12 },
  { title: 'Portrait loop', value: 'Live sync', bottom: '18%', left: '16%', drift: -16 },
  { title: 'Warning pulse', value: '03 risks', bottom: '12%', right: '14%', drift: 18 }
]

const nodes = [
  { x: 0.18, y: 0.24, energy: 0.72 },
  { x: 0.34, y: 0.18, energy: 0.9 },
  { x: 0.52, y: 0.28, energy: 0.86 },
  { x: 0.72, y: 0.22, energy: 0.78 },
  { x: 0.78, y: 0.44, energy: 0.84 },
  { x: 0.58, y: 0.58, energy: 1 },
  { x: 0.4, y: 0.64, energy: 0.82 },
  { x: 0.24, y: 0.54, energy: 0.68 },
  { x: 0.68, y: 0.76, energy: 0.76 }
]

const edges = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [2, 5],
  [5, 6],
  [6, 7],
  [5, 8],
  [1, 7],
  [4, 8]
]

const particles = Array.from({ length: 30 }, (_, index) => ({
  id: index,
  x: (index * 37 % 100) / 100,
  y: (index * 19 % 100) / 100,
  scale: 0.6 + ((index * 17) % 10) / 10,
  speed: 0.15 + ((index * 11) % 8) / 28,
  phase: index * 0.6
}))

const fieldRef = ref(null)
const canvasRef = ref(null)
const pointer = ref({ x: 0, y: 0 })
const compactMode = ref(false)
const reducedMotion = ref(false)

let rafId = 0
let compactQuery
let reducedQuery

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value))

const motionScale = computed(() => {
  if (reducedMotion.value) return 0.18
  if (compactMode.value) return 0.42
  return 1
})

const overlayTransform = computed(() => {
  const x = 318 + pointer.value.x * 12 * motionScale.value
  const y = 258 + pointer.value.y * 10 * motionScale.value
  const scale = 0.98 + motionScale.value * 0.02
  return `translate(${x - 318} ${y - 258}) scale(${scale})`
})

const coreTransform = computed(() => {
  const x = 318 + pointer.value.x * 22 * motionScale.value
  const y = 258 + pointer.value.y * 18 * motionScale.value
  return `translate(${x} ${y})`
})

const syncModes = () => {
  if (typeof window === 'undefined') return

  compactMode.value = compactQuery?.matches ?? window.innerWidth < 768
  reducedMotion.value = reducedQuery?.matches ?? false
}

const resizeCanvas = () => {
  if (!fieldRef.value || !canvasRef.value || typeof window === 'undefined') return

  const rect = fieldRef.value.getBoundingClientRect()
  const ratio = Math.min(window.devicePixelRatio || 1, 2)

  canvasRef.value.width = Math.round(rect.width * ratio)
  canvasRef.value.height = Math.round(rect.height * ratio)
  canvasRef.value.style.width = `${rect.width}px`
  canvasRef.value.style.height = `${rect.height}px`
}

const drawGlow = (ctx, x, y, radius, color, alpha = 1) => {
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
  gradient.addColorStop(0, color.replace('ALPHA', `${0.28 * alpha}`))
  gradient.addColorStop(0.45, color.replace('ALPHA', `${0.1 * alpha}`))
  gradient.addColorStop(1, color.replace('ALPHA', '0'))
  ctx.fillStyle = gradient
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fill()
}

const renderFrame = (time) => {
  if (!canvasRef.value || typeof window === 'undefined') return

  const ctx = canvasRef.value.getContext('2d')
  if (!ctx) return

  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const width = canvasRef.value.width / ratio
  const height = canvasRef.value.height / ratio
  const t = time * 0.00032

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
  ctx.clearRect(0, 0, width, height)
  ctx.globalCompositeOperation = 'lighter'

  const focalX = width * (0.46 + pointer.value.x * 0.03 * motionScale.value)
  const focalY = height * (0.44 + pointer.value.y * 0.03 * motionScale.value)

  drawGlow(ctx, focalX, focalY, width * 0.28, 'rgba(84,166,255,ALPHA)', 1)
  drawGlow(ctx, width * 0.76, height * 0.28, width * 0.18, 'rgba(140,240,228,ALPHA)', 0.9)
  drawGlow(ctx, width * 0.22, height * 0.72, width * 0.16, 'rgba(84,166,255,ALPHA)', 0.65)

  ctx.save()
  ctx.translate(focalX, focalY)
  ctx.rotate(-0.34 + pointer.value.x * 0.06 * motionScale.value)
  const beamA = ctx.createLinearGradient(-width * 0.42, 0, width * 0.42, 0)
  beamA.addColorStop(0, 'rgba(84,166,255,0)')
  beamA.addColorStop(0.42, 'rgba(84,166,255,0.08)')
  beamA.addColorStop(0.5, 'rgba(216,243,255,0.36)')
  beamA.addColorStop(0.58, 'rgba(84,166,255,0.08)')
  beamA.addColorStop(1, 'rgba(84,166,255,0)')
  ctx.fillStyle = beamA
  ctx.fillRect(-width * 0.42, -18, width * 0.84, 36)
  ctx.restore()

  ctx.save()
  ctx.translate(width * 0.66, height * 0.56)
  ctx.rotate(0.54 - pointer.value.y * 0.05 * motionScale.value)
  const beamB = ctx.createLinearGradient(-width * 0.28, 0, width * 0.28, 0)
  beamB.addColorStop(0, 'rgba(140,240,228,0)')
  beamB.addColorStop(0.45, 'rgba(140,240,228,0.08)')
  beamB.addColorStop(0.5, 'rgba(247,252,255,0.28)')
  beamB.addColorStop(0.55, 'rgba(140,240,228,0.08)')
  beamB.addColorStop(1, 'rgba(140,240,228,0)')
  ctx.fillStyle = beamB
  ctx.fillRect(-width * 0.28, -14, width * 0.56, 28)
  ctx.restore()

  ctx.lineWidth = compactMode.value ? 1.2 : 1.5
  edges.forEach(([fromIndex, toIndex], edgeIndex) => {
    const from = nodes[fromIndex]
    const to = nodes[toIndex]
    const wave = 0.5 + Math.sin(t * 4 + edgeIndex * 0.7) * 0.18
    const fromX = width * from.x
    const fromY = height * from.y
    const toX = width * to.x
    const toY = height * to.y

    const gradient = ctx.createLinearGradient(fromX, fromY, toX, toY)
    gradient.addColorStop(0, `rgba(84,166,255,${0.08 + wave * 0.08})`)
    gradient.addColorStop(0.5, `rgba(216,243,255,${0.18 + wave * 0.12})`)
    gradient.addColorStop(1, `rgba(140,240,228,${0.08 + wave * 0.08})`)
    ctx.strokeStyle = gradient
    ctx.beginPath()
    ctx.moveTo(fromX, fromY)
    ctx.lineTo(toX, toY)
    ctx.stroke()
  })

  nodes.forEach((node, nodeIndex) => {
    const x = width * node.x
    const y = height * node.y
    const pulse = 0.7 + Math.sin(t * 5 + nodeIndex) * 0.18

    drawGlow(ctx, x, y, (compactMode.value ? 18 : 24) * node.energy, 'rgba(140,240,228,ALPHA)', pulse)

    ctx.fillStyle = `rgba(244,252,255,${0.86 * pulse})`
    ctx.beginPath()
    ctx.arc(x, y, (compactMode.value ? 3.2 : 4.2) + node.energy, 0, Math.PI * 2)
    ctx.fill()
  })

  const particleCount = compactMode.value ? 16 : particles.length
  for (let index = 0; index < particleCount; index += 1) {
    const particle = particles[index]
    const px = width * (particle.x + Math.sin(t * particle.speed + particle.phase) * 0.03)
    const py = height * (particle.y + Math.cos(t * (particle.speed + 0.08) + particle.phase) * 0.026)
    const alpha = 0.12 + (Math.sin(t * 4 + particle.phase) + 1) * 0.14
    ctx.fillStyle = `rgba(230,243,255,${alpha})`
    ctx.beginPath()
    ctx.arc(px, py, particle.scale * (compactMode.value ? 1.4 : 1.8), 0, Math.PI * 2)
    ctx.fill()
  }

  if (!reducedMotion.value) {
    rafId = window.requestAnimationFrame(renderFrame)
  }
}

const startRender = () => {
  if (typeof window === 'undefined') return

  resizeCanvas()
  if (rafId) window.cancelAnimationFrame(rafId)
  rafId = 0

  if (reducedMotion.value) {
    renderFrame(performance.now())
    return
  }

  rafId = window.requestAnimationFrame(renderFrame)
}

const handlePointerMove = (event) => {
  if (!fieldRef.value || compactMode.value || reducedMotion.value) return

  const rect = fieldRef.value.getBoundingClientRect()
  pointer.value = {
    x: clamp((event.clientX - rect.left) / rect.width, 0, 1) * 2 - 1,
    y: clamp((event.clientY - rect.top) / rect.height, 0, 1) * 2 - 1
  }
}

const handlePointerLeave = () => {
  pointer.value = { x: 0, y: 0 }
}

const getBeaconStyle = (beacon) => ({
  top: beacon.top,
  right: beacon.right,
  bottom: beacon.bottom,
  left: beacon.left,
  transform: `translate3d(${pointer.value.x * beacon.drift * motionScale.value}px, ${pointer.value.y * beacon.drift * 0.8 * motionScale.value}px, 0)`
})

const handleModeChange = () => {
  syncModes()
  startRender()
}

onMounted(() => {
  compactQuery = window.matchMedia('(max-width: 767px)')
  reducedQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  syncModes()
  startRender()
  window.addEventListener('resize', startRender)
  compactQuery.addEventListener('change', handleModeChange)
  reducedQuery.addEventListener('change', handleModeChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', startRender)
  compactQuery?.removeEventListener('change', handleModeChange)
  reducedQuery?.removeEventListener('change', handleModeChange)

  if (rafId && typeof window !== 'undefined') {
    window.cancelAnimationFrame(rafId)
  }
})
</script>

<style scoped>
.hero-light-field {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: auto;
  overflow: hidden;
}

.hero-light-field__canvas,
.hero-light-field__overlay,
.hero-light-field__hud,
.hero-light-field__scanline,
.hero-light-field__vignette {
  position: absolute;
  inset: 0;
}

.hero-light-field__canvas,
.hero-light-field__overlay {
  width: 100%;
  height: 100%;
}

.hero-light-field__overlay {
  opacity: 0.86;
}

.hero-overlay__grid path {
  fill: none;
  stroke: rgba(214, 234, 255, 0.06);
  stroke-width: 1;
  stroke-dasharray: 6 12;
}

.hero-overlay__beam {
  fill: none;
  stroke-linecap: round;
  stroke-width: 2.2;
}

.hero-overlay__beam--a {
  stroke: url(#hero-beam-a);
}

.hero-overlay__beam--b {
  stroke: url(#hero-beam-b);
}

.hero-overlay__core-glow {
  fill: url(#hero-core-glow);
}

.hero-overlay__core-dot {
  fill: #8cf0e4;
}

.hero-overlay__orbit {
  fill: none;
  stroke: rgba(214, 234, 255, 0.1);
  stroke-width: 1;
  stroke-dasharray: 6 10;
}

.hero-overlay__orbit--mid {
  stroke: rgba(214, 234, 255, 0.08);
}

.hero-overlay__orbit--outer {
  stroke: rgba(214, 234, 255, 0.05);
}

.hero-light-field__label {
  position: absolute;
  min-width: 132px;
  padding: 10px 12px;
  border-radius: 18px;
  background: rgba(7, 19, 47, 0.44);
  border: 1px solid rgba(220, 236, 255, 0.1);
  box-shadow: 0 18px 34px rgba(4, 11, 29, 0.22);
  backdrop-filter: blur(14px);
}

.hero-light-field__label span,
.hero-light-field__label strong {
  display: block;
}

.hero-light-field__label span {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(208, 228, 255, 0.58);
}

.hero-light-field__label strong {
  margin-top: 6px;
  color: rgba(246, 251, 255, 0.96);
  font-size: 14px;
}

.hero-light-field__scanline {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.02) 0%, transparent 16%, transparent 84%, rgba(255, 255, 255, 0.02) 100%),
    repeating-linear-gradient(180deg, rgba(255, 255, 255, 0.016) 0 1px, transparent 1px 5px);
  mix-blend-mode: screen;
  opacity: 0.22;
}

.hero-light-field__vignette {
  background:
    radial-gradient(circle at center, transparent 36%, rgba(6, 16, 40, 0.2) 72%, rgba(4, 10, 28, 0.48) 100%),
    linear-gradient(180deg, rgba(6, 14, 34, 0.28), transparent 26%, transparent 72%, rgba(6, 14, 34, 0.42));
}

.hero-light-field--compact .hero-light-field__label {
  min-width: 112px;
  padding: 8px 10px;
}

.hero-light-field--compact .hero-light-field__label span {
  font-size: 10px;
}

.hero-light-field--compact .hero-light-field__label strong {
  font-size: 12px;
}

.hero-light-field--reduced .hero-light-field__label {
  transform: none !important;
}

@media (max-width: 767px) {
  .hero-light-field__label:nth-child(2),
  .hero-light-field__label:nth-child(4) {
    display: none;
  }

  .hero-light-field__overlay {
    opacity: 0.72;
  }

  .hero-light-field__scanline {
    opacity: 0.12;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-light-field__overlay,
  .hero-light-field__scanline {
    animation: none;
  }
}
</style>
