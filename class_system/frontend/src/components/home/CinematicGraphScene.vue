<template>
  <section
    id="graph"
    ref="sectionRef"
    class="cinematic-graph"
    :class="{
      'cinematic-graph--compact': compactMode,
      'cinematic-graph--reduced': reducedMotion
    }"
    :style="sceneStyle"
  >
    <div class="cinematic-graph__sticky">
      <div class="cinematic-graph__noise"></div>

      <div class="cinematic-graph__copy">
        <p class="section-label section-label--light">
          Knowledge Graph Theater
        </p>
        <h2>把知识图谱做成会呼吸的学习引擎。</h2>
        <p class="cinematic-graph__lead">
          往下滚动时，基础知识、关系推理和教学动作会依次点亮。页面不只是展示一个“图”，而是把课程先修、知识迁移、作业批注、画像回流和教师预警串成一条电影级叙事链。
        </p>

        <div class="cinematic-graph__chapters">
          <button
            v-for="(chapter, index) in chapters"
            :key="chapter.title"
            type="button"
            class="chapter-card"
            :class="{ 'chapter-card--active': activeChapter === index }"
            @click="jumpToChapter(index)"
          >
            <div class="chapter-card__header">
              <span>{{ chapter.eyebrow }}</span>
              <strong>{{ chapter.signal }}</strong>
            </div>
            <h3>{{ chapter.title }}</h3>
            <p>{{ chapter.description }}</p>
            <div class="chapter-card__meter">
              <i :style="{ width: `${Math.round(getChapterProgress(index) * 100)}%` }"></i>
            </div>
          </button>
        </div>

        <div class="cinematic-graph__summary">
          <span>Active chapter</span>
          <strong>{{ currentChapter.title }}</strong>
          <p>{{ currentChapter.description }}</p>
        </div>
      </div>

      <div class="cinematic-graph__stage">
        <div
          ref="stageRef"
          class="cinematic-graph__viewport"
          @pointermove="handlePointerMove"
          @pointerleave="handlePointerLeave"
        >
          <div class="cinematic-graph__headline">
            <span>Live relation engine</span>
            <strong>{{ Math.round(progress * 100) }}%</strong>
          </div>

          <svg
            class="graph-canvas"
            viewBox="0 0 1000 720"
            role="img"
            aria-label="Animated knowledge graph scene"
          >
            <defs>
              <linearGradient id="graph-line-foundation" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#8cf0e4" stop-opacity="0.12" />
                <stop offset="45%" stop-color="#54a6ff" stop-opacity="0.9" />
                <stop offset="100%" stop-color="#c9e8ff" stop-opacity="0.22" />
              </linearGradient>
              <linearGradient id="graph-line-reasoning" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#73f6eb" stop-opacity="0.2" />
                <stop offset="50%" stop-color="#54a6ff" stop-opacity="0.95" />
                <stop offset="100%" stop-color="#156b8f" stop-opacity="0.16" />
              </linearGradient>
              <linearGradient id="graph-line-action" x1="10%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f7fcff" stop-opacity="0.24" />
                <stop offset="50%" stop-color="#8cf0e4" stop-opacity="0.94" />
                <stop offset="100%" stop-color="#54a6ff" stop-opacity="0.26" />
              </linearGradient>
              <radialGradient id="graph-core-fill" cx="50%" cy="50%" r="65%">
                <stop offset="0%" stop-color="#d8f3ff" stop-opacity="0.95" />
                <stop offset="25%" stop-color="#8ecdfd" stop-opacity="0.44" />
                <stop offset="100%" stop-color="#0d2349" stop-opacity="0.18" />
              </radialGradient>
              <filter id="graph-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="10" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <g class="graph-backdrop">
              <circle cx="500" cy="356" r="288" class="graph-backdrop__aura graph-backdrop__aura--outer" />
              <circle cx="500" cy="356" r="208" class="graph-backdrop__aura graph-backdrop__aura--mid" />
              <circle cx="500" cy="356" r="122" class="graph-backdrop__aura graph-backdrop__aura--inner" />
              <circle cx="500" cy="356" r="332" class="graph-backdrop__ring" />
              <circle cx="500" cy="356" r="256" class="graph-backdrop__ring" />
              <circle cx="500" cy="356" r="176" class="graph-backdrop__ring" />
              <path d="M132 104 H880" class="graph-backdrop__axis" />
              <path d="M118 588 H872" class="graph-backdrop__axis" />
              <path d="M180 72 L854 646" class="graph-backdrop__axis graph-backdrop__axis--soft" />
              <path d="M156 632 L836 118" class="graph-backdrop__axis graph-backdrop__axis--soft" />
            </g>

            <g :transform="sceneTransform">
              <g class="graph-constellations">
                <circle
                  v-for="particle in particles"
                  :key="particle.id"
                  class="graph-particle"
                  :cx="particle.x"
                  :cy="particle.y"
                  :r="particle.r"
                  :style="{ animationDelay: particle.delay }"
                />
              </g>

              <g class="graph-links">
                <path
                  v-for="link in links"
                  :key="link.id"
                  class="graph-link"
                  :class="`graph-link--${link.group}`"
                  :d="link.d"
                  :style="getLinkStyle(link)"
                />
              </g>

              <g class="graph-core" :transform="coreTransform">
                <circle r="76" class="graph-core__halo" />
                <circle r="58" class="graph-core__body" />
                <circle r="14" class="graph-core__dot" />
                <text x="0" y="-8">Learning</text>
                <text x="0" y="20">Graph Core</text>
              </g>

              <g
                v-for="(node, index) in nodes"
                :key="node.id"
                class="graph-node"
                :class="`graph-node--${node.group}`"
                :style="{ opacity: getNodeOpacity(node) }"
                :transform="getNodeTransform(node, index)"
              >
                <circle :r="node.radius + 16" class="graph-node__pulse" />
                <rect
                  :x="-node.width / 2"
                  :y="-26"
                  :width="node.width"
                  :height="52"
                  rx="26"
                  class="graph-node__plate"
                />
                <circle :r="node.radius" class="graph-node__dot" />
                <text class="graph-node__label" x="12" y="4">{{ node.label }}</text>
                <text class="graph-node__kicker" x="12" y="-9">{{ node.kicker }}</text>
              </g>
            </g>
          </svg>

          <div
            v-for="item in displayedInsights"
            :key="item.title"
            class="graph-insight"
            :style="getInsightStyle(item)"
          >
            <span>{{ item.title }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.detail }}</p>
          </div>

          <div class="cinematic-graph__footer">
            <div class="signal-pill">
              <span>先修关系</span>
              <i>{{ Math.round(foundationPhase * 100) }}%</i>
            </div>
            <div class="signal-pill">
              <span>推理路径</span>
              <i>{{ Math.round(reasoningPhase * 100) }}%</i>
            </div>
            <div class="signal-pill">
              <span>教学动作</span>
              <i>{{ Math.round(actionPhase * 100) }}%</i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const chapters = [
  {
    eyebrow: 'Act I',
    title: '基础概念先被唤醒',
    description: '函数、递归、树结构和复杂度意识先被建立，图谱开始暴露先修依赖。',
    signal: 'Foundation'
  },
  {
    eyebrow: 'Act II',
    title: '关系推理开始蔓延',
    description: '状态设计、图搜索和约束传播被连成推理路径，搜索结果不再只是孤立答案。',
    signal: 'Reasoning'
  },
  {
    eyebrow: 'Act III',
    title: '知识回流到教学动作',
    description: '从知识命中直接进入作业批注、学习画像、推荐练习和教师预警闭环。',
    signal: 'Action'
  }
]

const nodes = [
  { id: 'function', label: '函数', kicker: 'Syntax', x: 184, y: 184, width: 128, radius: 10, group: 'foundation', parallax: 9, delay: 0.02 },
  { id: 'recursion', label: '递归', kicker: 'Recursion', x: 334, y: 132, width: 144, radius: 12, group: 'foundation', parallax: 10, delay: 0.08 },
  { id: 'tree', label: '树结构', kicker: 'Structure', x: 252, y: 332, width: 156, radius: 12, group: 'foundation', parallax: 8, delay: 0.14 },
  { id: 'stack', label: '栈帧', kicker: 'Runtime', x: 432, y: 264, width: 140, radius: 10, group: 'foundation', parallax: 10, delay: 0.22 },
  { id: 'state', label: '状态设计', kicker: 'Planning', x: 564, y: 154, width: 164, radius: 12, group: 'reasoning', parallax: 14, delay: 0.06 },
  { id: 'complexity', label: '复杂度', kicker: 'Complexity', x: 726, y: 248, width: 164, radius: 12, group: 'reasoning', parallax: 15, delay: 0.16 },
  { id: 'graph-search', label: '图搜索', kicker: 'Traversal', x: 646, y: 378, width: 156, radius: 12, group: 'reasoning', parallax: 16, delay: 0.24 },
  { id: 'path', label: '推理路径', kicker: 'Pathing', x: 812, y: 408, width: 168, radius: 12, group: 'reasoning', parallax: 15, delay: 0.3 },
  { id: 'practice', label: '推荐练习', kicker: 'Practice', x: 292, y: 548, width: 166, radius: 12, group: 'action', parallax: 12, delay: 0.08 },
  { id: 'annotation', label: '作业批注', kicker: 'Annotation', x: 492, y: 562, width: 170, radius: 13, group: 'action', parallax: 13, delay: 0.16 },
  { id: 'portrait', label: '学习画像', kicker: 'Portrait', x: 680, y: 568, width: 168, radius: 13, group: 'action', parallax: 13, delay: 0.24 },
  { id: 'warning', label: '教师预警', kicker: 'Warning', x: 842, y: 524, width: 170, radius: 13, group: 'action', parallax: 14, delay: 0.34 }
]

const links = [
  { id: 'l1', group: 'foundation', d: 'M184 184 C220 146 284 122 334 132', delay: 0.04 },
  { id: 'l2', group: 'foundation', d: 'M184 184 C204 246 224 280 252 332', delay: 0.08 },
  { id: 'l3', group: 'foundation', d: 'M334 132 C390 138 420 186 432 264', delay: 0.16 },
  { id: 'l4', group: 'foundation', d: 'M252 332 C318 322 374 300 432 264', delay: 0.22 },
  { id: 'l5', group: 'reasoning', d: 'M432 264 C472 226 516 182 564 154', delay: 0.06 },
  { id: 'l6', group: 'reasoning', d: 'M564 154 C622 168 686 192 726 248', delay: 0.14 },
  { id: 'l7', group: 'reasoning', d: 'M564 154 C596 230 610 296 646 378', delay: 0.22 },
  { id: 'l8', group: 'reasoning', d: 'M646 378 C696 364 754 372 812 408', delay: 0.3 },
  { id: 'l9', group: 'action', d: 'M252 332 C276 422 280 486 292 548', delay: 0.04 },
  { id: 'l10', group: 'action', d: 'M646 378 C598 454 548 514 492 562', delay: 0.14 },
  { id: 'l11', group: 'action', d: 'M646 378 C676 444 678 508 680 568', delay: 0.22 },
  { id: 'l12', group: 'action', d: 'M812 408 C822 444 832 482 842 524', delay: 0.3 },
  { id: 'l13', group: 'action', d: 'M492 562 C550 572 610 574 680 568', delay: 0.38 },
  { id: 'l14', group: 'action', d: 'M680 568 C734 560 782 542 842 524', delay: 0.46 }
]

const insights = [
  { title: '课程命中', value: '08 门', detail: '跨 Python、算法、数据结构和 Web 同时建立知识连接。', start: 0.08, top: '14%', left: '4%', depth: -16 },
  { title: '关系跨度', value: '12 跳', detail: '从薄弱点回推到先修概念，再进入问答与练习。', start: 0.36, top: '12%', right: '5%', depth: 18 },
  { title: '教学闭环', value: '批注 -> 画像 -> 预警', detail: '作业错误会被投影到学习画像和教师风险面板。', start: 0.68, bottom: '16%', right: '8%', depth: 22 }
]

const particles = [
  { id: 'p1', x: 160, y: 120, r: 2.6, delay: '0s' },
  { id: 'p2', x: 242, y: 86, r: 1.8, delay: '0.8s' },
  { id: 'p3', x: 364, y: 78, r: 2.2, delay: '0.6s' },
  { id: 'p4', x: 506, y: 84, r: 2.8, delay: '1.1s' },
  { id: 'p5', x: 694, y: 104, r: 2, delay: '0.4s' },
  { id: 'p6', x: 836, y: 152, r: 2.6, delay: '1.3s' },
  { id: 'p7', x: 884, y: 272, r: 1.8, delay: '0.2s' },
  { id: 'p8', x: 880, y: 418, r: 2.4, delay: '0.9s' },
  { id: 'p9', x: 816, y: 610, r: 1.8, delay: '1.6s' },
  { id: 'p10', x: 654, y: 644, r: 2.6, delay: '0.7s' },
  { id: 'p11', x: 440, y: 654, r: 2, delay: '1.4s' },
  { id: 'p12', x: 220, y: 610, r: 2.2, delay: '1s' },
  { id: 'p13', x: 124, y: 504, r: 1.8, delay: '0.3s' },
  { id: 'p14', x: 114, y: 344, r: 2.6, delay: '1.8s' },
  { id: 'p15', x: 132, y: 222, r: 2.1, delay: '1.2s' }
]

const sectionRef = ref(null)
const stageRef = ref(null)
const progress = ref(0)
const pointer = ref({ x: 0, y: 0 })
const compactMode = ref(false)
const reducedMotion = ref(false)

let frameId = 0
let compactQuery
let reducedQuery

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value))

const motionScale = computed(() => {
  if (reducedMotion.value) return 0.18
  if (compactMode.value) return 0.38
  return 1
})

const foundationPhase = computed(() => clamp(progress.value / 0.34))
const reasoningPhase = computed(() => clamp((progress.value - 0.24) / 0.32))
const actionPhase = computed(() => clamp((progress.value - 0.58) / 0.3))

const activeChapter = computed(() => {
  if (progress.value < 0.34) return 0
  if (progress.value < 0.68) return 1
  return 2
})

const currentChapter = computed(() => chapters[activeChapter.value])
const displayedInsights = computed(() => (compactMode.value ? insights.slice(0, 2) : insights))

const sceneStyle = computed(() => ({
  '--graph-progress': progress.value.toFixed(4),
  '--graph-pan-x': `${(pointer.value.x * 24 * motionScale.value).toFixed(2)}px`,
  '--graph-pan-y': `${(pointer.value.y * 18 * motionScale.value).toFixed(2)}px`,
  '--graph-tilt-x': `${(pointer.value.y * -7 * motionScale.value).toFixed(2)}deg`,
  '--graph-tilt-y': `${(pointer.value.x * 9 * motionScale.value).toFixed(2)}deg`
}))

const sceneTransform = computed(() => {
  const shiftX = pointer.value.x * 10 * motionScale.value
  const shiftY = pointer.value.y * 12 * motionScale.value
  const rotate = (progress.value - 0.5) * (compactMode.value ? 5 : 10)
  const scale = 0.98 + reasoningPhase.value * 0.04
  return `translate(${shiftX} ${shiftY}) rotate(${rotate} 500 356) scale(${scale})`
})

const coreTransform = computed(() => {
  const shiftX = 500 + pointer.value.x * 16 * motionScale.value
  const shiftY = 356 + pointer.value.y * 14 * motionScale.value
  const scale = 0.96 + progress.value * 0.08
  return `translate(${shiftX} ${shiftY}) scale(${scale})`
})

const syncModes = () => {
  if (typeof window === 'undefined') return

  compactMode.value = compactQuery?.matches ?? window.innerWidth < 768
  reducedMotion.value = reducedQuery?.matches ?? false

  if (compactMode.value || reducedMotion.value) {
    pointer.value = { x: 0, y: 0 }
  }
}

const updateProgress = () => {
  if (!sectionRef.value || typeof window === 'undefined') return

  const rect = sectionRef.value.getBoundingClientRect()
  const total = Math.max(sectionRef.value.offsetHeight - window.innerHeight, 1)
  progress.value = clamp(-rect.top / total)
}

const requestUpdate = () => {
  if (frameId || typeof window === 'undefined') return

  frameId = window.requestAnimationFrame(() => {
    frameId = 0
    updateProgress()
  })
}

const phaseValueByGroup = {
  foundation: foundationPhase,
  reasoning: reasoningPhase,
  action: actionPhase
}

const getRevealValue = (group, delay = 0) => {
  const phase = phaseValueByGroup[group]?.value ?? 0
  return clamp((phase - delay) / Math.max(1 - delay, 0.001))
}

const getChapterProgress = (index) => {
  if (index === 0) return clamp(progress.value / 0.34)
  if (index === 1) return clamp((progress.value - 0.24) / 0.44)
  return clamp((progress.value - 0.58) / 0.42)
}

const getNodeOpacity = (node) => {
  const reveal = getRevealValue(node.group, node.delay)
  return (0.08 + reveal * 0.94).toFixed(3)
}

const getNodeTransform = (node, index) => {
  const reveal = getRevealValue(node.group, node.delay)
  const float = Math.sin(progress.value * Math.PI * 4 + index * 0.9) * 6
  const driftX = pointer.value.x * node.parallax * motionScale.value
  const driftY = pointer.value.y * node.parallax * motionScale.value + (1 - reveal) * 32 + float
  const scale = 0.72 + reveal * 0.28
  return `translate(${node.x + driftX} ${node.y + driftY}) scale(${scale})`
}

const getLinkStyle = (link) => {
  const reveal = getRevealValue(link.group, link.delay)
  return {
    opacity: (0.06 + reveal * 0.94).toFixed(3),
    strokeDashoffset: `${(1 - reveal) * 420}px`
  }
}

const getInsightStyle = (item) => {
  const reveal = clamp((progress.value - item.start) / 0.24)
  const driftX = pointer.value.x * item.depth * motionScale.value
  const driftY = (1 - reveal) * 52 + pointer.value.y * 14 * motionScale.value

  return {
    top: item.top,
    right: item.right,
    bottom: item.bottom,
    left: item.left,
    opacity: (0.12 + reveal * 0.88).toFixed(3),
    transform: `translate3d(${driftX}px, ${driftY}px, 0) scale(${0.9 + reveal * 0.1})`
  }
}

const jumpToChapter = (index) => {
  if (!sectionRef.value || typeof window === 'undefined') return

  const targets = [0.08, 0.48, 0.82]
  const total = Math.max(sectionRef.value.offsetHeight - window.innerHeight, 1)
  const top = window.scrollY + sectionRef.value.getBoundingClientRect().top + total * targets[index]

  window.scrollTo({
    top,
    behavior: 'smooth'
  })
}

const handlePointerMove = (event) => {
  if (!stageRef.value || compactMode.value || reducedMotion.value) return

  const rect = stageRef.value.getBoundingClientRect()
  pointer.value = {
    x: clamp((event.clientX - rect.left) / rect.width, 0, 1) * 2 - 1,
    y: clamp((event.clientY - rect.top) / rect.height, 0, 1) * 2 - 1
  }
}

const handlePointerLeave = () => {
  pointer.value = { x: 0, y: 0 }
}

const handleModeChange = () => {
  syncModes()
  requestUpdate()
}

onMounted(() => {
  compactQuery = window.matchMedia('(max-width: 767px)')
  reducedQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  compactQuery.addEventListener('change', handleModeChange)
  reducedQuery.addEventListener('change', handleModeChange)
  syncModes()
  updateProgress()
  window.addEventListener('scroll', requestUpdate, { passive: true })
  window.addEventListener('resize', handleModeChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', requestUpdate)
  window.removeEventListener('resize', handleModeChange)
  compactQuery?.removeEventListener('change', handleModeChange)
  reducedQuery?.removeEventListener('change', handleModeChange)

  if (frameId && typeof window !== 'undefined') {
    window.cancelAnimationFrame(frameId)
  }
})
</script>

<style scoped>
.cinematic-graph {
  position: relative;
  min-height: 320vh;
}

.cinematic-graph__sticky {
  position: sticky;
  top: 18px;
  display: grid;
  grid-template-columns: minmax(320px, 0.4fr) minmax(0, 0.6fr);
  gap: 28px;
  min-height: calc(100vh - 36px);
  padding: clamp(24px, 3vw, 42px);
  border-radius: 40px;
  overflow: hidden;
  color: white;
  background:
    radial-gradient(circle at 20% 24%, rgba(82, 185, 255, 0.18), transparent 28%),
    radial-gradient(circle at 80% 18%, rgba(51, 211, 197, 0.12), transparent 24%),
    radial-gradient(circle at 48% 72%, rgba(139, 195, 255, 0.08), transparent 24%),
    linear-gradient(145deg, #061225 0%, #0a1f41 38%, #0b2d61 70%, #0d485e 100%);
  box-shadow: 0 36px 100px rgba(5, 14, 31, 0.34);
}

.cinematic-graph__noise,
.cinematic-graph__sticky::before,
.cinematic-graph__sticky::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.cinematic-graph__noise {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.9), transparent 95%);
  opacity: 0.24;
}

.cinematic-graph__sticky::before {
  content: '';
  background:
    radial-gradient(circle at 48% 50%, rgba(84, 166, 255, 0.1), transparent 24%),
    radial-gradient(circle at 44% 48%, rgba(51, 211, 197, 0.06), transparent 38%);
  filter: blur(24px);
}

.cinematic-graph__sticky::after {
  content: '';
  inset: 18px;
  border-radius: 32px;
  border: 1px solid rgba(193, 220, 255, 0.08);
}

.cinematic-graph__copy,
.cinematic-graph__stage {
  position: relative;
  z-index: 1;
}

.cinematic-graph__copy {
  display: grid;
  align-content: center;
  gap: 22px;
}

.section-label--light {
  color: rgba(223, 235, 255, 0.72);
}

.cinematic-graph__copy h2 {
  margin: 0;
  font-size: clamp(36px, 4.1vw, 58px);
  line-height: 0.98;
  letter-spacing: -0.05em;
}

.cinematic-graph__lead {
  margin: 0;
  color: rgba(226, 237, 255, 0.8);
  line-height: 1.85;
}

.cinematic-graph__chapters {
  display: grid;
  gap: 14px;
}

.chapter-card {
  appearance: none;
  width: 100%;
  text-align: left;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(226, 237, 255, 0.08);
  backdrop-filter: blur(16px);
  cursor: pointer;
  transition: transform 220ms ease, border-color 220ms ease, background 220ms ease;
}

.chapter-card--active {
  transform: translateX(8px);
  border-color: rgba(140, 240, 228, 0.36);
  background: rgba(255, 255, 255, 0.1);
}

.chapter-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(206, 226, 255, 0.62);
}

.chapter-card h3 {
  margin: 14px 0 0;
  font-size: 24px;
}

.chapter-card p {
  margin: 10px 0 0;
  color: rgba(226, 237, 255, 0.78);
  line-height: 1.7;
}

.chapter-card__meter {
  height: 6px;
  margin-top: 16px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.chapter-card__meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #54a6ff, #8cf0e4);
  box-shadow: 0 0 22px rgba(84, 166, 255, 0.42);
}

.cinematic-graph__summary {
  padding: 18px 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(226, 237, 255, 0.08);
}

.cinematic-graph__summary span,
.cinematic-graph__summary strong,
.cinematic-graph__summary p {
  display: block;
}

.cinematic-graph__summary span {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(206, 226, 255, 0.64);
}

.cinematic-graph__summary strong {
  margin-top: 10px;
  font-size: 20px;
}

.cinematic-graph__summary p {
  margin: 10px 0 0;
  color: rgba(226, 237, 255, 0.78);
  line-height: 1.7;
}

.cinematic-graph__stage {
  display: grid;
  align-items: center;
}

.cinematic-graph__viewport {
  position: relative;
  min-height: 76vh;
  padding: 22px;
  border-radius: 34px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
    radial-gradient(circle at 50% 50%, rgba(84, 166, 255, 0.14), transparent 38%);
  border: 1px solid rgba(226, 237, 255, 0.08);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  transform-style: preserve-3d;
}

.cinematic-graph__viewport::before {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  pointer-events: none;
}

.cinematic-graph__headline {
  position: absolute;
  top: 18px;
  left: 20px;
  right: 20px;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 999px;
  color: rgba(220, 236, 255, 0.84);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
}

.cinematic-graph__headline span {
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: 12px;
}

.cinematic-graph__headline strong {
  color: white;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  min-height: 76vh;
  display: block;
  transform: perspective(1400px) rotateX(var(--graph-tilt-x)) rotateY(var(--graph-tilt-y));
  transform-origin: center;
}

.graph-backdrop__aura {
  fill: rgba(84, 166, 255, 0.06);
}

.graph-backdrop__aura--mid {
  fill: rgba(84, 166, 255, 0.08);
}

.graph-backdrop__aura--inner {
  fill: rgba(140, 240, 228, 0.08);
}

.graph-backdrop__ring {
  fill: none;
  stroke: rgba(201, 232, 255, 0.08);
  stroke-width: 1;
  stroke-dasharray: 6 12;
}

.graph-backdrop__axis {
  fill: none;
  stroke: rgba(194, 219, 255, 0.08);
  stroke-width: 1;
}

.graph-backdrop__axis--soft {
  stroke: rgba(194, 219, 255, 0.04);
}

.graph-particle {
  fill: rgba(220, 241, 255, 0.88);
  animation: graphTwinkle 3.4s ease-in-out infinite;
}

.graph-link {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-dasharray: 420;
  filter: url(#graph-glow);
}

.graph-link--foundation {
  stroke: url(#graph-line-foundation);
}

.graph-link--reasoning {
  stroke: url(#graph-line-reasoning);
}

.graph-link--action {
  stroke: url(#graph-line-action);
}

.graph-core__halo {
  fill: url(#graph-core-fill);
  opacity: 0.54;
}

.graph-core__body {
  fill: rgba(242, 249, 255, 0.08);
  stroke: rgba(207, 231, 255, 0.2);
  stroke-width: 1.5;
  filter: url(#graph-glow);
}

.graph-core__dot {
  fill: #8cf0e4;
}

.graph-core text {
  text-anchor: middle;
  font-size: 15px;
  fill: white;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.graph-node__pulse {
  fill: rgba(84, 166, 255, 0.08);
  transform-origin: center;
  animation: graphPulse 3.2s ease-in-out infinite;
}

.graph-node__plate {
  fill: rgba(11, 32, 68, 0.72);
  stroke: rgba(214, 234, 255, 0.16);
  stroke-width: 1.4;
}

.graph-node__dot {
  fill: #8cf0e4;
  filter: url(#graph-glow);
}

.graph-node__label,
.graph-node__kicker {
  fill: white;
  text-anchor: start;
  pointer-events: none;
}

.graph-node__label {
  font-size: 15px;
  font-weight: 600;
}

.graph-node__kicker {
  font-size: 9px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  fill: rgba(212, 231, 255, 0.74);
}

.graph-node--action .graph-node__plate {
  fill: rgba(16, 54, 82, 0.82);
}

.graph-node--action .graph-node__pulse {
  fill: rgba(51, 211, 197, 0.12);
}

.graph-insight {
  position: absolute;
  z-index: 2;
  max-width: 220px;
  padding: 16px 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(226, 237, 255, 0.08);
  box-shadow: 0 18px 40px rgba(4, 12, 28, 0.22);
  backdrop-filter: blur(14px);
}

.graph-insight span,
.graph-insight strong,
.graph-insight p {
  display: block;
}

.graph-insight span {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(206, 226, 255, 0.64);
}

.graph-insight strong {
  margin-top: 8px;
  font-size: 22px;
}

.graph-insight p {
  margin: 10px 0 0;
  color: rgba(226, 237, 255, 0.78);
  line-height: 1.65;
}

.cinematic-graph__footer {
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 22px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.signal-pill {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 42px;
  padding: 0 14px;
  border-radius: 999px;
  color: rgba(221, 236, 255, 0.82);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.signal-pill i {
  color: white;
  font-style: normal;
}

.cinematic-graph--compact {
  min-height: 260vh;
}

.cinematic-graph--compact .graph-canvas,
.cinematic-graph--reduced .graph-canvas {
  transform: none;
}

.cinematic-graph--compact .cinematic-graph__viewport {
  min-height: 68vh;
}

.cinematic-graph--compact .graph-insight {
  max-width: 176px;
}

.cinematic-graph--reduced .graph-insight,
.cinematic-graph--reduced .chapter-card {
  transition: none;
}

@keyframes graphTwinkle {
  0%,
  100% {
    opacity: 0.24;
    transform: scale(0.8);
  }

  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@keyframes graphPulse {
  0%,
  100% {
    opacity: 0.28;
    transform: scale(0.92);
  }

  50% {
    opacity: 0.78;
    transform: scale(1.08);
  }
}

@media (max-width: 1279px) {
  .cinematic-graph {
    min-height: auto;
  }

  .cinematic-graph__sticky {
    position: relative;
    top: auto;
    min-height: auto;
    grid-template-columns: 1fr;
  }

  .cinematic-graph__viewport,
  .graph-canvas {
    min-height: 720px;
  }
}

@media (max-width: 767px) {
  .cinematic-graph__sticky {
    padding: 18px;
    border-radius: 28px;
  }

  .cinematic-graph__copy h2 {
    font-size: 38px;
  }

  .cinematic-graph__viewport {
    min-height: 620px;
    padding: 14px;
    border-radius: 26px;
  }

  .cinematic-graph__headline {
    left: 14px;
    right: 14px;
    top: 14px;
  }

  .graph-canvas {
    min-height: 600px;
  }

  .graph-insight {
    max-width: 172px;
    padding: 12px 14px;
  }

  .cinematic-graph__footer {
    left: 14px;
    right: 14px;
    bottom: 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .graph-particle,
  .graph-node__pulse {
    animation: none;
  }
}
</style>
