<template>
  <section
    id="journey"
    ref="sectionRef"
    class="journey-scene"
    :class="{
      'journey-scene--compact': compactMode,
      'journey-scene--reduced': reducedMotion
    }"
    :style="sceneStyle"
  >
    <div class="journey-scene__sticky">
      <div class="journey-scene__header">
        <div>
          <p class="section-label">Cinematic Workflow</p>
          <h2>往下滑，看到一次完整学习闭环如何被拍成电影。</h2>
        </div>

        <div class="journey-scene__status">
          <span>Current frame</span>
          <strong>{{ activeScene.frame }}</strong>
          <p>{{ activeScene.short }}</p>
        </div>
      </div>

      <div class="journey-scene__body">
        <div class="journey-scene__reel">
          <article
            v-for="(scene, index) in scenes"
            :key="scene.frame"
            class="journey-card"
            :class="[
              `journey-card--${scene.kind}`,
              { 'journey-card--active': activeIndex === index }
            ]"
            :style="getCardStyle(index)"
          >
            <div class="journey-card__chrome">
              <span>{{ scene.frame }}</span>
              <i>{{ scene.badge }}</i>
            </div>

            <div class="journey-card__visual">
              <div v-if="scene.kind === 'ingest'" class="journey-visual journey-visual--ingest">
                <div class="journey-visual__column">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div class="journey-visual__sheet">
                  <i></i>
                  <i></i>
                  <i></i>
                </div>
                <div class="journey-visual__queue">
                  <b></b>
                  <b></b>
                  <b></b>
                </div>
              </div>

              <div v-else-if="scene.kind === 'search'" class="journey-visual journey-visual--search">
                <div class="journey-visual__searchbar"></div>
                <div class="journey-visual__answer"></div>
                <div class="journey-visual__sources">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>

              <div v-else-if="scene.kind === 'portrait'" class="journey-visual journey-visual--portrait">
                <div class="journey-visual__radar">
                  <i></i>
                  <i></i>
                  <i></i>
                </div>
                <div class="journey-visual__node-cluster">
                  <span></span>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>

              <div v-else class="journey-visual journey-visual--warning">
                <div class="journey-visual__alerts">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div class="journey-visual__actions">
                  <i></i>
                  <i></i>
                </div>
              </div>
            </div>

            <div class="journey-card__content">
              <p>{{ scene.eyebrow }}</p>
              <h3>{{ scene.title }}</h3>
              <strong>{{ scene.metric }}</strong>
              <p class="journey-card__description">{{ scene.description }}</p>
              <div class="journey-card__tags">
                <span v-for="tag in scene.tags" :key="tag">{{ tag }}</span>
              </div>
            </div>
          </article>
        </div>

        <aside class="journey-scene__detail">
          <div class="journey-scene__detail-panel">
            <span>Scene direction</span>
            <h3>{{ activeScene.title }}</h3>
            <p>{{ activeScene.description }}</p>
          </div>

          <div class="journey-scene__rail">
            <button
              v-for="(scene, index) in scenes"
              :key="scene.frame"
              type="button"
              class="journey-rail__item"
              :class="{ 'journey-rail__item--active': activeIndex === index }"
              @click="jumpToScene(index)"
            >
              <strong>{{ scene.frame }}</strong>
              <span>{{ scene.short }}</span>
            </button>
          </div>

          <div class="journey-scene__caption">
            <span>Loop summary</span>
            <p>{{ activeScene.caption }}</p>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const scenes = [
  {
    frame: 'Scene 01',
    badge: 'Ingest',
    kind: 'ingest',
    eyebrow: 'Knowledge Assets',
    title: '课程资料进入知识资产台',
    short: '文档导入',
    metric: 'PDF / 课件 / 讲义 / 样例自动分块',
    description: '教师上传的课件、讲义、实验资料和作业样例，会直接进入可检索、可追踪、可复用的知识资产工作流。',
    caption: '首页从一开始就解释平台为什么不是普通 CMS，而是可检索的教学知识底座。',
    tags: ['批量上传', '向量化', '索引状态']
  },
  {
    frame: 'Scene 02',
    badge: 'Search',
    kind: 'search',
    eyebrow: 'Search Workspace',
    title: '搜索驱动的问答被点亮',
    short: '搜索问答',
    metric: 'RAG 命中 + 图谱关系 + 引用来源同屏出现',
    description: '学生或教师发起问题时，结果页不只给答案，还能展示来源、命中知识点、图谱路径和后续推荐动作。',
    caption: '搜索框成为整个系统的真正入口，问答、课程、知识和作业全部被统一组织。',
    tags: ['知识库对话', '课程问答', '来源回溯']
  },
  {
    frame: 'Scene 03',
    badge: 'Portrait',
    kind: 'portrait',
    eyebrow: 'Portrait Loop',
    title: '学习画像与评估回流成闭环',
    short: '画像回流',
    metric: '掌握度 / 风险 / 薄弱点 / 推荐练习同步生成',
    description: '问答行为、作业批注和测评结果会回流成能力雷达、知识缺口和跨课程成长轨迹，形成持续更新的学习画像。',
    caption: '这里展示的是“为什么推荐这个练习”，而不是只有一个孤立分数。',
    tags: ['能力雷达', '薄弱点', '成长轨迹']
  },
  {
    frame: 'Scene 04',
    badge: 'Intervene',
    kind: 'warning',
    eyebrow: 'Teacher Cockpit',
    title: '教师进入干预驾驶舱',
    short: '教师干预',
    metric: '风险识别后直接进入画像、通知和历史记录',
    description: '教师在预警页看到班级风险波动后，可以马上查看学生画像详情、发送干预建议并记录后续处理动作。',
    caption: '学生视角和教师视角在这里闭环，平台具备真正的教学运营能力。',
    tags: ['风险预警', '通知渠道', '干预记录']
  }
]

const sectionRef = ref(null)
const progress = ref(0)
const compactMode = ref(false)
const reducedMotion = ref(false)

let frameId = 0
let compactQuery
let reducedQuery

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value))
const motionScale = computed(() => {
  if (reducedMotion.value) return 0.18
  if (compactMode.value) return 0.46
  return 1
})

const focus = computed(() => progress.value * (scenes.length - 1))

const activeIndex = computed(() => Math.min(scenes.length - 1, Math.round(focus.value)))
const activeScene = computed(() => scenes[activeIndex.value])

const sceneStyle = computed(() => ({
  '--journey-progress': progress.value.toFixed(4)
}))

const syncModes = () => {
  if (typeof window === 'undefined') return

  compactMode.value = compactQuery?.matches ?? window.innerWidth < 768
  reducedMotion.value = reducedQuery?.matches ?? false
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

const getCardStyle = (index) => {
  const delta = index - focus.value
  const depth = Math.min(Math.abs(delta), 2.2)
  const scale = 1 - depth * (compactMode.value ? 0.07 : 0.12)
  const opacity = clamp(1 - depth * (compactMode.value ? 0.14 : 0.24), compactMode.value ? 0.32 : 0.16, 1)
  const translateX = delta * (compactMode.value ? 22 : 43)
  const translateY = depth * (compactMode.value ? 20 : 34)
  const rotateY = reducedMotion.value || compactMode.value ? 0 : delta * -16
  const rotateZ = reducedMotion.value ? 0 : delta * (compactMode.value ? -0.6 : -1.6)
  const blur = reducedMotion.value ? 0 : depth * (compactMode.value ? 0.8 : 2.2)

  return {
    opacity: opacity.toFixed(3),
    zIndex: `${120 - Math.round(depth * 22)}`,
    filter: `blur(${blur}px) saturate(${1 - depth * 0.08 * motionScale.value})`,
    transform: `translate3d(${translateX}%, ${translateY}px, 0) scale(${scale}) rotateY(${rotateY}deg) rotateZ(${rotateZ}deg)`
  }
}

const jumpToScene = (index) => {
  if (!sectionRef.value || typeof window === 'undefined') return

  const targets = [0.04, 0.34, 0.64, 0.92]
  const total = Math.max(sectionRef.value.offsetHeight - window.innerHeight, 1)
  const top = window.scrollY + sectionRef.value.getBoundingClientRect().top + total * targets[index]

  window.scrollTo({
    top,
    behavior: 'smooth'
  })
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
.journey-scene {
  position: relative;
  min-height: 260vh;
  margin-top: 18px;
}

.journey-scene__sticky {
  position: sticky;
  top: 18px;
  display: grid;
  gap: 28px;
  min-height: calc(100vh - 36px);
  padding: clamp(24px, 3vw, 38px);
  border-radius: 38px;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 24%, rgba(84, 166, 255, 0.15), transparent 26%),
    radial-gradient(circle at 78% 72%, rgba(51, 211, 197, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(241, 247, 255, 0.92));
  border: 1px solid rgba(145, 168, 202, 0.22);
  box-shadow: 0 32px 80px rgba(14, 28, 57, 0.12);
}

.journey-scene__sticky::before,
.journey-scene__sticky::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.journey-scene__sticky::before {
  background-image:
    linear-gradient(rgba(20, 70, 159, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20, 70, 159, 0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.74), transparent 100%);
}

.journey-scene__sticky::after {
  inset: 16px;
  border-radius: 28px;
  border: 1px solid rgba(145, 168, 202, 0.12);
}

.journey-scene__header,
.journey-scene__body {
  position: relative;
  z-index: 1;
}

.journey-scene__header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: end;
}

.journey-scene__header h2 {
  margin: 10px 0 0;
  font-size: clamp(32px, 3.7vw, 54px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: var(--ink-950);
}

.journey-scene__status {
  padding: 18px 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(145, 168, 202, 0.18);
}

.journey-scene__status span,
.journey-scene__status strong,
.journey-scene__status p {
  display: block;
}

.journey-scene__status span {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.journey-scene__status strong {
  margin-top: 10px;
  font-size: 22px;
  color: var(--ink-950);
}

.journey-scene__status p {
  margin: 8px 0 0;
  color: var(--text-secondary);
}

.journey-scene__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 26px;
  min-height: 0;
}

.journey-scene__reel {
  position: relative;
  min-height: 70vh;
  perspective: 2200px;
}

.journey-card {
  position: absolute;
  inset: 0;
  width: min(100%, 860px);
  height: min(70vh, 720px);
  margin: auto;
  display: grid;
  grid-template-columns: minmax(280px, 0.96fr) minmax(260px, 0.94fr);
  gap: 22px;
  padding: 20px;
  border-radius: 34px;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 22%, rgba(84, 166, 255, 0.18), transparent 24%),
    radial-gradient(circle at 86% 84%, rgba(51, 211, 197, 0.12), transparent 20%),
    linear-gradient(145deg, rgba(7, 20, 49, 0.96), rgba(10, 28, 65, 0.94));
  border: 1px solid rgba(200, 225, 255, 0.12);
  box-shadow: 0 34px 70px rgba(9, 23, 49, 0.24);
  transform-style: preserve-3d;
  transition: box-shadow 220ms ease, border-color 220ms ease;
}

.journey-card::before {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  pointer-events: none;
}

.journey-card--active {
  box-shadow: 0 40px 86px rgba(9, 23, 49, 0.28);
  border-color: rgba(140, 240, 228, 0.2);
}

.journey-card__chrome,
.journey-card__content,
.journey-card__visual {
  position: relative;
  z-index: 1;
}

.journey-card__chrome {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: rgba(230, 240, 255, 0.82);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.journey-card__chrome i {
  font-style: normal;
}

.journey-card__visual {
  display: grid;
  align-items: center;
  padding-top: 42px;
}

.journey-visual {
  position: relative;
  min-height: 100%;
  padding: 22px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
    rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(214, 234, 255, 0.12);
  overflow: hidden;
}

.journey-visual::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(84, 166, 255, 0.18), transparent 26%),
    radial-gradient(circle at 80% 74%, rgba(51, 211, 197, 0.12), transparent 24%);
  pointer-events: none;
}

.journey-visual--ingest,
.journey-visual--warning {
  display: grid;
  grid-template-columns: 96px 1fr 92px;
  gap: 16px;
  align-items: center;
}

.journey-visual__column,
.journey-visual__queue,
.journey-visual__actions,
.journey-visual__sources,
.journey-visual__alerts {
  display: grid;
  gap: 12px;
}

.journey-visual__column span,
.journey-visual__queue b,
.journey-visual__searchbar,
.journey-visual__answer,
.journey-visual__sources span,
.journey-visual__alerts span,
.journey-visual__actions i,
.journey-visual__sheet i {
  display: block;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(84, 166, 255, 0.26), rgba(51, 211, 197, 0.18));
  box-shadow: inset 0 0 0 1px rgba(214, 234, 255, 0.08);
}

.journey-visual__column span:nth-child(1),
.journey-visual__column span:nth-child(2),
.journey-visual__column span:nth-child(3) {
  min-height: 58px;
}

.journey-visual__sheet {
  position: relative;
  min-height: 280px;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(145, 168, 202, 0.16);
}

.journey-visual__sheet i:nth-child(1) {
  min-height: 28px;
}

.journey-visual__sheet i:nth-child(2) {
  min-height: 122px;
  margin-top: 14px;
}

.journey-visual__sheet i:nth-child(3) {
  min-height: 68px;
  margin-top: 14px;
}

.journey-visual__queue b:nth-child(1) {
  min-height: 54px;
}

.journey-visual__queue b:nth-child(2) {
  min-height: 98px;
}

.journey-visual__queue b:nth-child(3) {
  min-height: 72px;
}

.journey-visual--search {
  display: grid;
  align-content: center;
  gap: 16px;
}

.journey-visual__searchbar {
  min-height: 56px;
  border-radius: 999px;
}

.journey-visual__answer {
  min-height: 180px;
}

.journey-visual__sources {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.journey-visual__sources span {
  min-height: 74px;
}

.journey-visual--portrait {
  display: grid;
  place-items: center;
}

.journey-visual__radar {
  position: relative;
  width: min(320px, 100%);
  aspect-ratio: 1;
  border-radius: 50%;
  border: 1px solid rgba(214, 234, 255, 0.12);
}

.journey-visual__radar i {
  position: absolute;
  inset: 50%;
  border-radius: 50%;
  border: 1px solid rgba(214, 234, 255, 0.14);
  transform: translate(-50%, -50%);
}

.journey-visual__radar i:nth-child(1) {
  width: 100%;
  height: 100%;
}

.journey-visual__radar i:nth-child(2) {
  width: 66%;
  height: 66%;
}

.journey-visual__radar i:nth-child(3) {
  width: 34%;
  height: 34%;
}

.journey-visual__node-cluster {
  position: absolute;
  inset: 0;
}

.journey-visual__node-cluster span {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #54a6ff, #8cf0e4);
  box-shadow: 0 0 0 8px rgba(84, 166, 255, 0.1);
}

.journey-visual__node-cluster span:nth-child(1) {
  top: 24%;
  left: 30%;
}

.journey-visual__node-cluster span:nth-child(2) {
  top: 20%;
  right: 24%;
}

.journey-visual__node-cluster span:nth-child(3) {
  bottom: 24%;
  left: 26%;
}

.journey-visual__node-cluster span:nth-child(4) {
  bottom: 28%;
  right: 28%;
}

.journey-visual__alerts {
  grid-template-columns: 1fr;
}

.journey-visual__alerts span:nth-child(1) {
  min-height: 64px;
}

.journey-visual__alerts span:nth-child(2) {
  min-height: 96px;
}

.journey-visual__alerts span:nth-child(3) {
  min-height: 68px;
}

.journey-visual__actions i:nth-child(1) {
  min-height: 82px;
}

.journey-visual__actions i:nth-child(2) {
  min-height: 122px;
}

.journey-card__content {
  display: grid;
  align-content: end;
  gap: 14px;
  padding: 64px 10px 6px 0;
}

.journey-card__content > p:first-of-type {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(223, 236, 255, 0.66);
}

.journey-card__content h3 {
  margin: 0;
  font-size: clamp(28px, 3vw, 42px);
  line-height: 1.02;
  color: white;
}

.journey-card__content strong {
  color: #8cf0e4;
  font-size: 16px;
}

.journey-card__description {
  margin: 0;
  color: rgba(223, 236, 255, 0.82);
  line-height: 1.75;
}

.journey-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.journey-card__tags span {
  padding: 8px 12px;
  border-radius: 999px;
  color: rgba(235, 244, 255, 0.86);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.journey-scene__detail {
  display: grid;
  align-content: center;
  gap: 18px;
}

.journey-scene__detail-panel,
.journey-scene__caption {
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(145, 168, 202, 0.18);
}

.journey-scene__detail-panel span,
.journey-scene__caption span {
  display: block;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.journey-scene__detail-panel h3 {
  margin: 10px 0 0;
  font-size: 26px;
  line-height: 1.08;
}

.journey-scene__detail-panel p,
.journey-scene__caption p {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.journey-scene__rail {
  display: grid;
  gap: 10px;
}

.journey-rail__item {
  display: grid;
  gap: 6px;
  justify-items: start;
  padding: 16px 18px;
  border-radius: 20px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(145, 168, 202, 0.14);
}

.journey-rail__item--active {
  color: var(--ink-950);
  border-color: rgba(84, 166, 255, 0.24);
  box-shadow: 0 12px 30px rgba(14, 28, 57, 0.08);
}

.journey-rail__item strong {
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.journey-rail__item span {
  text-align: left;
}

.journey-scene--compact {
  min-height: 220vh;
}

.journey-scene--compact .journey-card {
  transform-style: flat;
}

.journey-scene--compact .journey-scene__reel {
  perspective: 1200px;
}

.journey-scene--reduced .journey-card {
  filter: none !important;
}

@media (max-width: 1279px) {
  .journey-scene {
    min-height: auto;
  }

  .journey-scene__sticky {
    position: relative;
    top: auto;
    min-height: auto;
  }

  .journey-scene__header,
  .journey-scene__body,
  .journey-card {
    grid-template-columns: 1fr;
  }

  .journey-scene__reel {
    min-height: 780px;
  }

  .journey-card {
    height: 760px;
  }

  .journey-card__content {
    padding-right: 0;
  }
}

@media (max-width: 767px) {
  .journey-scene__sticky {
    padding: 18px;
    border-radius: 28px;
  }

  .journey-scene__header h2 {
    font-size: 36px;
  }

  .journey-scene__reel {
    min-height: 720px;
  }

  .journey-card {
    height: 700px;
    padding: 16px;
    border-radius: 26px;
  }

  .journey-card__chrome {
    top: 16px;
    left: 16px;
    right: 16px;
  }

  .journey-visual--ingest,
  .journey-visual--warning {
    grid-template-columns: 1fr;
  }

  .journey-visual__sheet {
    min-height: 220px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .journey-card {
    filter: none !important;
    transform: none !important;
  }
}
</style>
