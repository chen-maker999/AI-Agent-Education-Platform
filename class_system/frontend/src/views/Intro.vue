<template>
  <div class="intro-root" ref="rootEl">

    <!-- ═══ SPLINE BACKGROUND ═══ -->
    <div class="intro-bg" aria-hidden="true">
      <!-- 纯色背景层 -->
      <div class="intro-bg__solid"></div>
      <!-- Spline动画层 -->
      <div class="spline-container">
        <iframe
          :src="`https://my.spline.design/voiceinteractionanimation-nA95ssn2FUGaZE51T4LIF9ck/`"
          frameborder="0"
          width="100%"
          height="100%"
          allow="autoplay; fullscreen"
          class="spline-iframe"
        ></iframe>
      </div>
      <div class="intro-bg__overlay" aria-hidden="true"></div>
    </div>

    <!-- ═══ PILL NAV ═══ -->
    <nav class="pill-nav" id="pill-nav">
      <div class="pill-nav__row">
        <div class="pill-nav__inner">
          <router-link to="/" class="pill-nav__logo">
            <svg width="28" height="28" viewBox="0 0 36 36" fill="none">
              <rect width="36" height="36" rx="10" fill="rgba(0,122,255,0.1)" stroke="rgba(0,122,255,0.3)" stroke-width="1.2"/>
              <path d="M9 18L18 9L27 18L18 27Z" fill="none" stroke="#007aff" stroke-width="1.5"/>
              <circle cx="18" cy="18" r="4" fill="#5856d6"/>
              <circle cx="18" cy="9" r="2" fill="#ff9500"/>
            </svg>
          </router-link>
          <div class="pill-nav__divider"></div>
          <div class="pill-nav__links">
            <a v-for="sec in sections" :key="sec.id"
              :href="`#${sec.id}`"
              :class="{ active: activeSection === sec.id }"
              @click.prevent="scrollToSection(sec.id)">{{ sec.label }}</a>
          </div>
          <div class="pill-nav__divider"></div>
          <button class="pill-nav__btn" @click="openLogin">登录</button>
          <div class="pill-nav__divider"></div>
          <!-- 动效按钮 -->
          <button class="start-btn-glow" @click="openRegister">
            <div class="start-btn-glow__loader">
              <div class="start-btn-glow__beam"></div>
            </div>
          <span class="start-btn-glow__text">
              <span class="loader-letter" style="animation-delay: 0.1s">现</span>
              <span class="loader-letter" style="animation-delay: 0.3s;">在</span>
              <span class="loader-letter" style="animation-delay: 0.5s;">开</span>
              <span class="loader-letter" style="animation-delay: 0.7s;">始</span>
          </span>
          </button>
        </div>
      </div>
    </nav>

    <!-- ═══ HERO ═══ -->
    <section id="hero" class="ig-section ig-hero">

      <!-- Step indicators -->
      <div class="step-indicators anim-in" style="--delay:0.1s">
        <div v-for="(step, i) in steps" :key="step.label"
          class="step-item" :class="{ active: i === 0 }">
          <span class="step-num">{{ String(i+1).padStart(2,'0') }}</span>
          <div class="step-bar" :class="{ active: i === 0 }"></div>
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>

      <h1 class="hero-title anim-in" style="--delay:0.2s">
        <span class="hero-title--search">搜索原生</span><br>
        <span class="hero-title--accent anim-in" style="--delay:0.8s"><span class="hero-title--ai anim-in" style="--delay:1.2s">AI</span> 教学平台</span>
      </h1>
      <p class="hero-sub anim-in" style="--delay:0.3s">
        把智能答疑、知识图谱、精细批注、学习画像、预警干预、Agent Studio 和平台接入，
        全部折叠进一个优雅、可扩展、可嵌入的教学操作系统。
      </p>

      <!-- Search demo card -->
      <div class="search-card anim-in float-1" style="--delay:0.4s">
        <div class="search-card__bar">
          <svg class="search-card__icon" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M14 14L18 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="search-typed">{{ typedText }}</span>
          <span class="search-cursor"></span>
          <button class="search-send">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="search-chips">
          <span v-for="c in chips" :key="c" class="search-chip">{{ c }}</span>
        </div>
      </div>

      <div class="hero-actions anim-in" style="--delay:0.5s">
        <button class="btn-hero-primary" @click="openRegister">申请演示</button>
        <button class="btn-hero-ghost" @click="openLogin">进入工作区</button>
      </div>

      <!-- Floating stat bubbles -->
      <div class="float-bubble float-bubble--a float-1">
        <span class="float-bubble__val">8</span>
        <span class="float-bubble__label">核心模块</span>
      </div>
      <div class="float-bubble float-bubble--b float-2">
        <span class="float-bubble__val">3</span>
        <span class="float-bubble__label">角色空间</span>
      </div>
      <div class="float-bubble float-bubble--c float-3">
        <span class="float-bubble__val">∞</span>
        <span class="float-bubble__label">可扩展</span>
      </div>

      <div class="scroll-hint" :class="{ hidden: scrollY > 100 }">
        <div class="scroll-hint__arrow"></div>
        <span>向下滚动探索</span>
      </div>
    </section>

    <!-- ═══ BELOW HERO: CONTENT WRAPPER ═══ -->
    <div class="intro-content-wrapper" aria-label="主要内容区">

    <!-- ═══ STATS ═══ -->
    <section id="stats" class="ig-section stats-section" ref="statsRef">
      <div class="stats-grid">
        <div v-for="(stat, i) in stats" :key="stat.label"
          class="stat-card scroll-flip-card"
          :data-index="i">
          <div class="stat-card__accent" :style="`background:${stat.color}`"></div>
          <div class="stat-card__num" :style="`color:${stat.color}`">{{ stat.value }}</div>
          <div class="stat-card__label">{{ stat.label }}</div>
          <div class="stat-card__desc">{{ stat.desc }}</div>
        </div>
      </div>
    </section>

    <!-- ═══ FEATURES ═══ -->
    <section id="features" class="ig-section" ref="featuresRef">
      <div class="section-head reveal-left" :class="{ 'reveal-visible': featuresVisible }">
        <p class="section-eyebrow">Capability Matrix</p>
        <h2>八大核心能力，覆盖教学全链路</h2>
        <p>不是孤立页面，而是围绕搜索、知识、评估、作业、预警和平台接入联动的前台系统。</p>
      </div>
      <div class="features-grid">
        <article v-for="(feat, i) in features" :key="feat.title"
          class="feat-card scroll-flip-card"
          :data-index="i"
          :style="`--accent:${feat.color}`">
          <div class="feat-card__top">
            <div class="feat-card__icon" :style="`background:${feat.color}18;border-color:${feat.color}30`">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="4" :fill="feat.color" opacity="0.9"/>
                <circle cx="10" cy="10" r="8" :stroke="feat.color" stroke-width="1" opacity="0.25"/>
              </svg>
            </div>
            <span class="feat-card__tag">{{ feat.tag }}</span>
          </div>
          <h3>{{ feat.title }}</h3>
          <p>{{ feat.desc }}</p>
          <ul class="feat-card__points">
            <li v-for="pt in feat.points" :key="pt">{{ pt }}</li>
          </ul>
          <router-link :to="feat.to" class="feat-card__link">
            进入模块
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </router-link>
          <div class="feat-card__shine"></div>
        </article>
      </div>
    </section>

    <!-- ═══ ROLES ═══ -->
    <section id="roles" class="ig-section" ref="rolesRef">
      <div class="section-head reveal-right" :class="{ 'reveal-visible': rolesVisible }">
        <p class="section-eyebrow">Role-aware Experience</p>
        <h2>三类角色，共用一套系统，拥有不同视角</h2>
      </div>
      <div class="roles-grid">
        <div v-for="(role, i) in roles" :key="role.name"
          class="role-card scroll-flip-card"
          :data-index="i">
          <div class="role-card__header">
            <div class="role-card__badge" :style="`background:${role.gradient}`"></div>
            <div>
              <h3>{{ role.name }}</h3>
              <p class="role-card__sub">{{ role.sub }}</p>
            </div>
          </div>
          <p class="role-card__desc">{{ role.desc }}</p>
          <ul class="role-card__list">
            <li v-for="pt in role.points" :key="pt">
              <span class="role-dot" :style="`background:${role.color}`"></span>
              {{ pt }}
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ═══ WORKFLOW TIMELINE ═══ -->
    <section id="workflow" class="ig-section timeline-section" ref="workflowRef">
      <div class="section-head reveal-left" :class="{ 'reveal-visible': workflowVisible }">
        <p class="section-eyebrow">Learning Flow</p>
        <h2>从一次搜索，到完整的学习闭环</h2>
      </div>
      <div class="timeline" id="timeline-wrap">
        <div class="timeline__beam-track">
          <div class="timeline__beam-fill" id="timeline-beam"></div>
        </div>
        <div id="timeline-steps">
          <div v-for="(step, i) in workflow" :key="step.title"
            class="timeline-step scroll-flip-card"
            :data-index="i">
            <div class="timeline-node" :style="`border-color:${step.color};color:${step.color}`">
              {{ String(i+1).padStart(2,'00') }}
            </div>
            <div class="timeline-body">
              <h4>{{ step.title }}</h4>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ CTA ═══ -->
    <section id="cta" class="ig-section cta-section" ref="ctaRef">
      <div class="cta-card scroll-flip-card" data-index="0">
        <div class="cta-orb cta-orb--a"></div>
        <div class="cta-orb cta-orb--b"></div>
        <p class="section-eyebrow">Ready To Launch</p>
        <h2>现在就开始，把 <span class="ai-word">AI</span> 能力带入你的课堂</h2>
        <p>EduNavigator 已覆盖竞赛题目、项目计划书和业务功能全貌，随时可以接入。</p>
        <div class="cta-actions">
          <button class="btn-hero-primary" @click="openRegister">立即注册体验</button>
          <button class="btn-hero-ghost" @click="openLogin">进入现有工作区</button>
        </div>
      </div>
    </section>

    </div><!-- end .intro-content-wrapper -->

  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAuthModal } from '@/composables/useAuthModal'

const router = useRouter()
const authStore = useAuthStore()
const { openLogin, openRegister } = useAuthModal()

const rootEl = ref(null)
const scrollY = ref(0)
const activeSection = ref('hero')

const sections = [
  { id: 'hero', label: '首页' },
  { id: 'features', label: '功能矩阵' },
  { id: 'roles', label: '角色空间' },
  { id: 'workflow', label: '学习流程' },
]

const steps = [
  { label: '搜索驱动' },
  { label: '知识联动' },
  { label: '教学闭环' },
]

const chips = ['智能答疑', '知识图谱', '精细批注', '画像预警', 'Agent Studio']
const typedText = ref('')
let promptIdx = 0, charTimer = null, promptTimer = null
let bgParallax = null

const prompts = [
  '搜索"数据结构薄弱点"，生成本周增量练习',
  '定位实验报告中的错误段落并给出批注',
  '展示跨课程知识图谱中动态规划的先修路径',
  '把高风险学生按课程维度聚类并生成干预建议',
]

function typePrompt(text, cb) {
  let i = 0; typedText.value = ''
  charTimer = setInterval(() => {
    if (i < text.length) { typedText.value += text[i]; i++ }
    else { clearInterval(charTimer); cb && cb() }
  }, 42)
}
function cyclePrompts() {
  typePrompt(prompts[promptIdx], () => {
    promptTimer = setTimeout(() => {
      promptIdx = (promptIdx + 1) % prompts.length
      cyclePrompts()
    }, 2400)
  })
}

/* 与 Intro 页视觉统一的配色：蓝色系（MacOS风格） */
const stats = [
  { value: '8 大模块', label: '核心功能覆盖', desc: '从问答到预警，完整教学链路', color: '#007aff' },
  { value: '3 类角色', label: '差异化工作台', desc: '学生 / 教师 / 管理员各有专属视角', color: '#5856d6' },
  { value: '1 个入口', label: '统一搜索驱动', desc: '跨模块、跨课程、跨角色检索', color: '#ff9500' },
  { value: '∞ 扩展', label: '平台接入能力', desc: '超星、钉钉等主流平台可嵌入', color: '#34c759' },
]

const features = [
  { title: '智能问答工作区', tag: 'RAG + Search', color: '#007aff', desc: '基于课程知识库的多轮追问，保留引用来源与行动建议。', points: ['课程文档精准检索', '多轮上下文对话', '引用来源可追溯'], to: '/chat' },
  { title: '知识资产台', tag: 'Knowledge OS', color: '#5856d6', desc: '统一承接文档上传、知识点管理、向量索引与可追问素材。', points: ['文档上传与解析', '知识点结构化管理', '向量索引自动构建'], to: '/knowledge' },
  { title: '知识图谱舞台', tag: 'Cross-course', color: '#ff9500', desc: '让先修关系、跨课连接和学习路径成为直觉化可视网络。', points: ['先修关系可视化', '跨课程知识连接', '学习路径推荐'], to: '/graph' },
  { title: '作业精细批注', tag: 'Annotation', color: '#34c759', desc: '为文本、代码、报告类作业预留段落级和上下文级反馈能力。', points: ['段落级精细批注', '错误定位与解释', '批注历史回看'], to: '/homework' },
  { title: '学习画像与评估', tag: 'Insight Loop', color: '#007aff', desc: '把掌握度、投入度、趋势和后续练习串成闭环。', points: ['掌握度雷达图', '薄弱点精准定位', '个性化练习推荐'], to: '/portrait' },
  { title: '预警驾驶舱', tag: 'Early Warning', color: '#ff2d55', desc: '聚合高风险学生、群体异常和可执行的教学干预动作。', points: ['多维风险信号聚合', '班级异常趋势分析', '干预动作一键触发'], to: '/warning' },
  { title: 'Agent Studio', tag: 'Orchestration', color: '#5856d6', desc: '为课程 Agent 的构建、编排、调试和复用预留统一工作台。', points: ['Agent 可视化编排', '工作流调试与测试', '跨课程 Agent 复用'], to: '/studio' },
  { title: '平台接入', tag: 'Integration', color: '#ff9500', desc: '统一管理超星、钉钉等主流教学平台的嵌入能力与适配状态。', points: ['超星 / 钉钉嵌入', '接口状态实时监控', '多平台统一治理'], to: '/integrations' },
]

const roles = [
  { name: '学生空间', sub: 'Student Workspace', gradient: 'linear-gradient(135deg,#007aff,#5856d6)', color: '#007aff', desc: '从搜索入手，把答疑、练习、作业回看和画像反馈串成一条学习路径。', points: ['课程问答与知识追问', '个性化练习与薄弱点修复', '作业批注回看与行动建议', '学习画像与阶段评估'] },
  { name: '教师空间', sub: 'Teacher Workspace', gradient: 'linear-gradient(135deg,#ff9500,#ff2d55)', color: '#ff9500', desc: '把班级洞察、风险预警、作业批改和知识资源更新统一到教学节奏里。', points: ['高风险学生优先处理', '批改队列与错误定位', '教学决策与知识覆盖校准', '预警信号与干预联动'] },
  { name: '管理员空间', sub: 'Admin Workspace', gradient: 'linear-gradient(135deg,#5856d6,#34c759)', color: '#5856d6', desc: '负责 Agent 构建、平台嵌入、权限治理与系统能力的持续扩展。', points: ['Agent Studio 编排', '平台接口接入治理', '跨课程能力统一配置', '系统监控与权限管理'] },
]

const workflow = [
  { title: '发起搜索', desc: '在统一搜索框输入问题、课程或知识点', color: '#007aff' },
  { title: '知识检索', desc: 'RAG 引擎从向量库精准召回相关知识块', color: '#5856d6' },
  { title: 'Agent 推理', desc: 'Tutor Agent 生成引用式解释与行动建议', color: '#ff9500' },
  { title: '画像更新', desc: '交互数据实时回写学习画像与掌握度模型', color: '#34c759' },
  { title: '闭环干预', desc: '预警信号触发教师干预或个性化练习推送', color: '#ff2d55' },
]

// Visibility (for reveal-left/right section heads only)
const statsRef = ref(null), featuresRef = ref(null), rolesRef = ref(null)
const workflowRef = ref(null), ctaRef = ref(null)
const statsVisible = ref(false), featuresVisible = ref(false)
const rolesVisible = ref(false), workflowVisible = ref(false), ctaVisible = ref(false)

let observers = []
function makeObserver(r, v) {
  const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) v.value = true }, { threshold: 0.05 })
  if (r.value) obs.observe(r.value)
  observers.push(obs)
}

// 3D scroll flip loop (model.html style)
let rafId = null
let flipCardsData = []

function initFlipCards() {
  const cards = document.querySelectorAll('.scroll-flip-card')
  flipCardsData = Array.from(cards).map((el, index) => ({
    el, index,
    targetP: 1, currentP: 1, direction: 1, absoluteCenterY: 0
  }))
  calcCenters()
}

function calcCenters() {
  const el = rootEl.value
  if (!el) return
  flipCardsData.forEach(d => {
    const prev = d.el.style.transform
    d.el.style.transform = 'none'
    const rect = d.el.getBoundingClientRect()
    d.absoluteCenterY = rect.top + el.scrollTop + rect.height / 2
    d.el.style.transform = prev
  })
}

function flipLoop() {
  const isMobile = window.innerWidth < 768
  if (isMobile) {
    flipCardsData.forEach(d => {
      d.el.style.transform = 'none'
      d.el.style.opacity = '1'
      d.el.style.filter = 'none'
    })
    rafId = requestAnimationFrame(flipLoop)
    return
  }
  const el = rootEl.value
  const wh = el ? el.clientHeight : window.innerHeight
  const vc = wh / 2
  const sy = el ? el.scrollTop : 0
  const threshold = 0.25
  const animRange = 0.5

  flipCardsData.forEach(d => {
    const trueCenter = d.absoluteCenterY - sy
    const dist = trueCenter - vc
    const norm = dist / wh
    let targetP = 0, dir = 1
    if (norm > threshold) { targetP = (norm - threshold) / animRange; dir = 1 }
    else if (norm < -threshold) { targetP = (-norm - threshold) / animRange; dir = -1 }
    d.targetP = Math.min(1, Math.max(0, targetP))
    if (Math.abs(norm) > threshold) d.direction = dir
    const lerpSpeed = d.targetP === 0 ? 0.08 : 0.25
    d.currentP += (d.targetP - d.currentP) * lerpSpeed
    const p = d.currentP
    const ep = 1 - Math.pow(1 - p, 3)
    const opacity = 1 - ep * 0.85
    const rotX = d.direction * 40 * ep
    const rotY = d.direction * (d.index % 2 === 0 ? 1 : -1) * 10 * ep
    const ty = d.direction * 150 * ep
    const tz = -250 * ep
    const blur = 8 * Math.pow(ep, 2)
    d.el.style.opacity = Math.min(1, Math.max(0, opacity)).toFixed(3)
    d.el.style.filter = blur > 0.5 ? `blur(${blur.toFixed(1)}px)` : 'none'
    d.el.style.transform = `perspective(2000px) translate3d(0,${ty.toFixed(1)}px,${tz.toFixed(1)}px) rotateX(${rotX.toFixed(1)}deg) rotateY(${rotY.toFixed(1)}deg)`
  })
  rafId = requestAnimationFrame(flipLoop)
}

function onScroll() {
  const el = rootEl.value
  if (!el) return
  scrollY.value = el.scrollTop
  const ids = ['hero', 'stats', 'features', 'roles', 'workflow', 'cta']
  for (const id of [...ids].reverse()) {
    const domEl = document.getElementById(id)
    if (domEl && domEl.getBoundingClientRect().top <= 120) { activeSection.value = id; break }
  }
  // Timeline beam
  const wrap = document.getElementById('timeline-wrap')
  const beam = document.getElementById('timeline-beam')
  if (wrap && beam) {
    const rect = wrap.getBoundingClientRect()
    const fill = Math.max(0, Math.min(el.clientHeight * 0.55 - rect.top, rect.height))
    beam.style.height = fill + 'px'
    wrap.querySelectorAll('.timeline-node').forEach(node => {
      const step = node.closest('.timeline-step')
      const nodeTop = step.offsetTop + step.offsetHeight / 2
      node.classList.toggle('node-active', fill >= nodeTop)
    })
  }
}

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  document.body.style.overflow = 'auto'
  cyclePrompts()
  const el = rootEl.value
  if (el) {
    el.addEventListener('scroll', onScroll, { passive: true })
  }
  window.addEventListener('resize', calcCenters, { passive: true })
  makeObserver(statsRef, statsVisible)
  makeObserver(featuresRef, featuresVisible)
  makeObserver(rolesRef, rolesVisible)
  makeObserver(workflowRef, workflowVisible)
  makeObserver(ctaRef, ctaVisible)
  setTimeout(() => { initFlipCards(); flipLoop() }, 50)

  // Mouse parallax on background
  bgParallax = (e) => {
    const bg = document.querySelector('.intro-bg')
    if (!bg) return
    const x = (e.clientX / window.innerWidth - 0.5) * 24
    const y = (e.clientY / window.innerHeight - 0.5) * 24
    bg.style.transform = `translate(${x}px, ${y}px)`
  }
  window.addEventListener('mousemove', bgParallax)
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  clearInterval(charTimer); clearTimeout(promptTimer)
  const el = rootEl.value
  if (el) {
    el.removeEventListener('scroll', onScroll)
  }
  window.removeEventListener('resize', calcCenters)
  observers.forEach(o => o.disconnect())
  if (bgParallax) { window.removeEventListener('mousemove', bgParallax); bgParallax = null }
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
/* ── Root（MacOS风格：浅灰背景 + 蓝色点缀）── */
.intro-root {
  --intro-bg: #e8e8ed;
  --intro-sidebar-bg: rgba(246, 246, 246, 0.95);
  --intro-card-bg: rgba(255, 255, 255, 0.98);
  --intro-border: rgba(0, 0, 0, 0.1);
  --intro-text: #1d1d1f;
  --intro-text-secondary: #86868b;
  --intro-accent: #007aff;
  --intro-accent-secondary: #5856d6;
  --intro-orange: #ff9500;
  --intro-pink: #ff2d55;
  --intro-green: #34c759;
  --intro-radius: 12px;
  --intro-radius-lg: 20px;
  --intro-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  --intro-blur: 20px;

  position: relative; overflow-x: hidden; overflow-y: auto;
  min-height: 100vh;
  background: var(--intro-bg);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', sans-serif;
  color: var(--intro-text);
  -webkit-font-smoothing: antialiased;
}

/* ── Spline background ── */
.intro-bg {
  position: fixed; inset: 0; z-index: 0;
  will-change: transform;
  transition: transform 0.12s ease-out;
}
.intro-bg__solid {
  position: absolute; inset: 0; z-index: 0;
  background: #e8e8ed;
}
.intro-bg__overlay {
  position: absolute; inset: 0; z-index: 2; pointer-events: none;
  background: transparent;
}
.spline-container {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 1;
}
.spline-iframe {
  width: 100%; height: 100%; display: block;
}

/* ── Pill nav（MacOS风格）── */
.pill-nav {
  position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 100; transition: all 0.4s ease;
}
.pill-nav__row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.pill-nav__cta {
  flex-shrink: 0;
}
.pill-nav__row .start-btn-glow {
  height: 36px;
  padding: 0 16px;
  font-size: 13px;
  border-radius: 9999px;
  background: linear-gradient(135deg, #007aff 0%, #ff9500 50%, #ff2d55 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(0px);
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.pill-nav__row .start-btn-glow:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 122, 255, 0.4), 0 0 0 2px rgba(255, 149, 0, 0.3);
}
.start-btn-glow__loader {
  position: absolute; top: 0; left: 0; height: 100%; width: 100%; z-index: 1;
  background-color: transparent;
  mask: repeating-linear-gradient(90deg, transparent 0, transparent 6px, black 7px, black 8px);
  -webkit-mask: repeating-linear-gradient(90deg, transparent 0, transparent 6px, black 7px, black 8px);
}
.start-btn-glow__beam {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background-image: radial-gradient(circle at 50% 50%, #f43f5e 0%, transparent 50%), radial-gradient(circle at 45% 45%, #ef4444 0%, transparent 45%), radial-gradient(circle at 55% 55%, #fb7185 0%, transparent 45%), radial-gradient(circle at 45% 55%, #f87171 0%, transparent 45%), radial-gradient(circle at 55% 45%, #dc2626 0%, transparent 45%);
  mask: radial-gradient(circle at 50% 50%, transparent 0%, transparent 10%, black 25%);
  -webkit-mask: radial-gradient(circle at 50% 50%, transparent 0%, transparent 10%, black 25%);
  animation: transform-animation 2s infinite alternate, opacity-animation 4s infinite;
  animation-timing-function: cubic-bezier(0.6, 0.8, 0.5, 1);
  filter: drop-shadow(0 0 6px rgba(244, 63, 94, 0.5));
}
.start-btn-glow__text {
  position: relative; z-index: 2;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 1em; font-weight: 600;
  user-select: none; color: #fff;
  display: flex; gap: 0.1rem;
}
.loader-letter {
  display: inline-block;
  opacity: 0;
  animation: loader-letter-anim 4s infinite;
}
@keyframes transform-animation {
  0% { transform: translate(-55%); }
  100% { transform: translate(55%); }
}
@keyframes opacity-animation {
  0%, 100% { opacity: 0; }
  15% { opacity: 1; }
  65% { opacity: 0; }
}
@keyframes loader-letter-anim {
  0% {
    opacity: 0;
    transform: translateY(4px) scale(0.9);
  }
  8% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  88% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
.pill-nav__inner {
  display: flex; align-items: center; gap: 4px;
  padding: 6px; border-radius: 9999px;
  background: var(--intro-card-bg);
  backdrop-filter: blur(var(--intro-blur));
  -webkit-backdrop-filter: blur(var(--intro-blur));
  border: 1px solid var(--intro-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}
.pill-nav__logo {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 50%;
  transition: transform 0.2s ease;
}
.pill-nav__logo:hover { transform: scale(1.1); }
.pill-nav__divider { width: 1px; height: 16px; background: rgba(0, 0, 0, 0.1); margin: 0 6px; }
.pill-nav__links { display: flex; gap: 2px; }
.pill-nav__links a {
  padding: 6px 14px; border-radius: 9999px;
  font-size: 13px; font-weight: 500; color: var(--intro-text-secondary);
  transition: background 0.2s ease, color 0.2s ease;
}
.pill-nav__links a:hover, .pill-nav__links a.active {
  background: var(--intro-accent);
  color: white;
}
.pill-nav__btn {
  padding: 6px 14px; border-radius: 9999px;
  font-size: 13px; font-weight: 500; color: var(--intro-text-secondary);
  transition: all 0.2s ease;
}
/* ── Sections ── */
.ig-section {
  position: relative; z-index: 2;
  width: min(1280px, 100%); margin: 0 auto; padding: 0 24px;
}

/* 内容包裹器 */
.intro-glass-wrapper {
  position: relative; z-index: 1;
  padding: 32px 36px 64px;
  background: transparent;
  min-height: 100vh;
}

/* ── Hero ── */
.ig-hero {
  position: relative;
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center;
  padding-top: 100px; padding-bottom: 60px; gap: 28px;
  overflow: visible;
}

/* Anim-in utility */
.anim-in {
  opacity: 0; filter: blur(8px);
  animation: animIn 0.5s ease-out var(--delay, 0s) both;
}
@keyframes animIn {
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

/* Step indicators */
.step-indicators { display: flex; gap: 40px; align-items: center; justify-content: center; animation: slideUpStep 0.5s ease-out 0.1s both; }
@keyframes slideUpStep {
  from { transform: translateY(-40px); opacity: 0; filter: blur(8px); }
  to { transform: translateY(-40px); opacity: 1; filter: blur(0); }
}
.step-item { display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; }
.step-num { font-size: 11px; font-weight: 700; letter-spacing: 0.18em; color: var(--intro-text-secondary); text-transform: uppercase; transition: color 0.3s; }
.step-item.active .step-num { color: var(--intro-accent); }
.step-bar { height: 3px; width: 64px; border-radius: 9999px; background: rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.step-bar.active {
  background: linear-gradient(90deg, var(--intro-accent), var(--intro-accent-secondary));
  box-shadow: 0 0 14px rgba(0, 122, 255, 0.35);
}
.step-label { font-size: 13px; font-weight: 500; color: var(--intro-text-secondary); transition: all 0.3s; }
.step-item.active .step-label { color: var(--intro-accent); font-weight: 600; }

/* Hero title */
.hero-title {
  font-size: clamp(52px, 7vw, 96px); line-height: 1.05;
  font-weight: 700;
  color: var(--intro-text);
  letter-spacing: -0.03em;
  align-self: flex-start;
  text-align: left;
}
.hero-title--search {
  background: linear-gradient(90deg, var(--intro-text), var(--intro-accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-title--accent {
  background: linear-gradient(90deg, var(--intro-text), var(--intro-accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-title--ai {
  background: linear-gradient(90deg, #007aff, #ff9500, #ff2d55);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  display: inline-block;
  transform: scaleX(1.3);
  font-weight: 700;
  animation: animIn 0.5s ease-out var(--delay, 0s) both, scaleX-persist 0.5s ease-out var(--delay, 0s) both;
}
@keyframes scaleX-persist {
  to { transform: scaleX(1.3); }
}
.ai-word {
  background: linear-gradient(90deg, #007aff, #ff9500, #ff2d55);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  display: inline-block;
  font-weight: 700;
  transform: scaleX(1.3);
  animation: scaleX-persist-ai 0.5s ease-out both;
}
@keyframes scaleX-persist-ai {
  to { transform: scaleX(1.3); }
}
.hero-sub {
  max-width: 640px;
  width: 100%;
  align-self: flex-start;
  text-align: left;
  font-size: 16px;
  line-height: 1.9;
  color: var(--intro-text-secondary);
  font-weight: 500;
}

/* Search card */
.search-card {
  background: var(--intro-card-bg);
  backdrop-filter: blur(var(--intro-blur));
  border: 1px solid var(--intro-border);
  border-radius: 12px;
  padding: 6px;
  box-shadow: var(--intro-shadow);
  width: min(560px, 100%);
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.search-card:hover {
  border-color: rgba(0, 122, 255, 0.3);
  box-shadow: 0 12px 40px rgba(0, 122, 255, 0.1);
}
.search-card__icon { flex-shrink: 0; color: var(--intro-accent); opacity: 0.9; }
.search-card__bar {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; border-radius: 10px;
  background: #fff;
  border: 1px solid var(--intro-border);
}
.search-typed { flex: 1; font-size: 14px; font-weight: 500; color: var(--intro-text); }
.search-cursor {
  width: 2px; height: 18px; border-radius: 1px;
  background: var(--intro-accent);
  animation: blink-cursor 1s steps(1) infinite;
}
.search-send {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--intro-accent);
  color: #fff;
  display: grid; place-items: center;
  border: none;
  box-shadow: 0 4px 14px rgba(0, 122, 255, 0.3);
  transition: background 0.2s ease, transform 0.2s ease;
}
.search-send:hover { background: var(--intro-accent-secondary); transform: scale(1.05); }
.search-chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 10px 4px; }
.search-chip {
  padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;
  background: #fff;
  border: 1px solid var(--intro-border);
  color: var(--intro-accent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}
.search-chip:hover {
  background: var(--intro-accent);
  border-color: var(--intro-accent);
  color: white;
  transform: translateY(-1px);
}

/* Hero actions */
.hero-actions { display: flex; gap: 12px; }
.btn-hero-primary {
  padding: 12px 28px; border-radius: 12px;
  background: var(--intro-accent);
  color: #fff; font-size: 15px; font-weight: 600;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
  transition: all 0.3s ease;
}
.btn-hero-primary:hover {
  background: var(--intro-accent-secondary);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.35);
}
.btn-hero-ghost {
  padding: 12px 28px; border-radius: 12px;
  background: #fff;
  color: var(--intro-text); font-size: 15px; font-weight: 600;
  border: 1px solid var(--intro-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}
.btn-hero-ghost:hover {
  border-color: var(--intro-accent);
  color: var(--intro-accent);
  transform: translateY(-2px);
}

/* Float bubbles */
.float-bubble {
  position: absolute; display: flex; flex-direction: column; align-items: center; gap: 2px;
  background: var(--intro-card-bg);
  backdrop-filter: blur(var(--intro-blur));
  border: 1px solid var(--intro-border);
  border-radius: 16px;
  padding: 12px 18px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  pointer-events: none;
}
.float-bubble--a { right: 4%; top: 32%; }
.float-bubble--b { right: 2%; top: 52%; }
.float-bubble--c { right: 6%; top: 68%; }
.float-bubble__val {
  font-size: 22px; font-weight: 700;
  color: var(--intro-accent);
}
.float-bubble--b .float-bubble__val {
  color: var(--intro-orange);
}
.float-bubble--c .float-bubble__val {
  color: var(--intro-accent-secondary);
}
.float-bubble__label { font-size: 11px; color: var(--intro-text-secondary); font-weight: 600; }

/* Float animations */
.float-1 { animation: floatBubble1 7s ease-in-out infinite; }
.float-2 { animation: floatBubble2 8s ease-in-out infinite; }
.float-3 { animation: floatBubble3 6s ease-in-out infinite; }
@keyframes floatBubble1 { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-20px) rotate(4deg); } }
@keyframes floatBubble2 { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(25px) rotate(-4deg); } }
@keyframes floatBubble3 { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-15px) rotate(2deg); } }

/* Scroll hint */
.scroll-hint {
  position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
  transition: opacity 0.5s ease;
  text-shadow: 0 1px 0 rgba(0,0,0,0.8);
}
.scroll-hint.hidden { opacity: 0; pointer-events: none; }
.scroll-hint__arrow {
  width: 18px; height: 18px;
  border-right: 2px solid var(--intro-orange); border-bottom: 2px solid var(--intro-orange);
  transform: rotate(45deg);
  animation: bounceDown 1.6s ease-in-out infinite;
}
@keyframes bounceDown { 0%,100% { transform: rotate(45deg) translateY(0); } 50% { transform: rotate(45deg) translateY(6px); } }

/* ── Scroll flip cards (model.html style) ── */
.scroll-flip-card {
  will-change: transform, opacity, filter;
  transform-style: preserve-3d;
  /* remove old opacity:0 initial state — JS controls this */
}

/* ── Reveal left/right for section headers ── */
.reveal-left {
  opacity: 0;
  transform: translate3d(-50px, 0, 0);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform, opacity;
}
.reveal-right {
  opacity: 0;
  transform: translate3d(50px, 0, 0);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform, opacity;
}
.reveal-visible {
  opacity: 1 !important;
  transform: translate3d(0, 0, 0) !important;
}

/* ── Stats ── */
.stats-section { padding: 0; margin-bottom: 48px; }
.stats-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; }
.stat-card {
  position: relative; overflow: hidden;
  background: #fff;
  border: 1px solid var(--intro-border);
  border-radius: 16px;
  padding: 28px 24px;
  box-shadow: var(--intro-shadow);
  opacity: 0; transform: translateY(28px);
  transition: opacity 0.4s ease, transform 0.4s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.stat-card.visible { opacity: 1; transform: translateY(0); }
.stat-card:hover {
  border-color: var(--intro-accent);
  box-shadow: 0 12px 40px rgba(0, 122, 255, 0.08);
  transform: translateY(-4px);
}
.stat-card__accent { position: absolute; top: 0; left: 0; right: 0; height: 4px; opacity: 1; }
.stat-card__num { font-size: 30px; font-weight: 700; margin-bottom: 8px; }
.stat-card__label { font-size: 14px; font-weight: 600; color: var(--intro-text); margin-bottom: 6px; }
.stat-card__desc { font-size: 12px; color: var(--intro-text-secondary); line-height: 1.65; font-weight: 500; }

/* ── Section head ── */
.section-head {
  margin-bottom: 40px; opacity: 0; transform: translateY(24px);
  transition: all 0.5s ease;
}
.section-head.visible { opacity: 1; transform: translateY(0); }
.section-eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--intro-accent);
  margin-bottom: 12px;
}
.section-head h2 {
  font-size: clamp(28px,3.5vw,48px); font-weight: 700;
  color: var(--intro-text);
  line-height: 1.15; margin-bottom: 12px;
}
.section-head p { color: var(--intro-text-secondary); font-size: 15px; line-height: 1.85; max-width: 680px; font-weight: 500; }

/* ── Features ── */
.features-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; padding-bottom: 80px; }
.feat-card {
  position: relative; overflow: hidden;
  background: #fff;
  border: 1px solid var(--intro-border);
  border-radius: 16px;
  padding: 22px;
  box-shadow: var(--intro-shadow);
  display: flex; flex-direction: column; gap: 10px;
  opacity: 0; transform: translateY(32px);
  transition: opacity 0.4s ease, transform 0.4s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.feat-card.visible { opacity: 1; transform: translateY(0); }
.feat-card:hover {
  border-color: var(--intro-accent);
  box-shadow: 0 12px 40px rgba(0, 122, 255, 0.08);
  transform: translateY(-5px);
}
.feat-card:hover .feat-card__shine { opacity: 1; }
.feat-card__shine {
  position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at 50% 0%, rgba(0, 122, 255, 0.08), transparent 60%);
  opacity: 0; transition: opacity 0.4s ease;
}
.feat-card__top { display: flex; align-items: center; justify-content: space-between; }
.feat-card__icon {
  width: 44px; height: 44px; display: grid; place-items: center;
  border-radius: 10px; border: 1px solid;
}
.feat-card__tag {
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
  color: var(--intro-accent);
  padding: 4px 10px; border-radius: 9999px;
  background: rgba(0, 122, 255, 0.08);
  border: 1px solid rgba(0, 122, 255, 0.2);
}
.feat-card h3 { font-size: 15px; font-weight: 700; color: var(--intro-text); }
.feat-card > p { font-size: 13px; color: var(--intro-text-secondary); line-height: 1.75; flex: 1; font-weight: 500; }
.feat-card__points { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 5px; }
.feat-card__points li {
  font-size: 12px; color: var(--intro-text-secondary); padding-left: 14px; position: relative; font-weight: 500;
}
.feat-card__points li::before {
  content: ''; position: absolute; left: 0; top: 7px;
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--accent, var(--intro-accent)); opacity: 0.7;
}
.feat-card__link {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600; color: var(--accent, var(--intro-accent));
  margin-top: 4px; transition: gap 0.2s ease;
}
.feat-card__link:hover { gap: 10px; }

/* ── Roles ── */
.roles-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; padding-bottom: 80px; }
.role-card {
  background: #fff;
  border: 1px solid var(--intro-border);
  border-radius: 16px;
  padding: 28px;
  box-shadow: var(--intro-shadow);
  opacity: 0; transform: translateY(28px);
  transition: opacity 0.4s ease, transform 0.4s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.role-card.visible { opacity: 1; transform: translateY(0); }
.role-card:hover {
  border-color: var(--intro-accent);
  box-shadow: 0 12px 40px rgba(0, 122, 255, 0.08);
  transform: translateY(-4px);
}
.role-card__header { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.role-card__badge { width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0; }
.role-card__header h3 { font-size: 20px; font-weight: 700; color: var(--intro-text); margin-bottom: 4px; }
.role-card__sub { font-size: 11px; color: var(--intro-accent); font-weight: 600; letter-spacing: 0.08em; }
.role-card__desc { font-size: 14px; color: var(--intro-text-secondary); line-height: 1.85; margin-bottom: 16px; font-weight: 500; }
.role-card__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.role-card__list li { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--intro-text-secondary); font-weight: 500; }
.role-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

/* ── Timeline ── */
.timeline-section { padding-bottom: 0; margin-top: 48px; }
.timeline {
  position: relative; padding-left: 48px;
  background: #fff;
  border: 1px solid var(--intro-border);
  border-radius: 16px;
  padding: 32px 32px 32px 64px;
  box-shadow: var(--intro-shadow);
}
.timeline__beam-track {
  position: absolute; left: 32px; top: 32px; bottom: 32px; width: 3px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 2px; overflow: hidden;
}
.timeline__beam-fill {
  width: 100%; height: 0;
  background: linear-gradient(180deg, var(--intro-accent), var(--intro-accent-secondary));
  border-radius: 2px; transition: height 0.1s linear;
}
.timeline-step {
  display: flex; align-items: flex-start; gap: 20px;
  padding: 20px 0; border-bottom: 1px solid var(--intro-border);
  opacity: 0; transform: translateX(-20px);
  transition: opacity 0.35s ease, transform 0.35s ease;
}
.timeline-step:last-child { border-bottom: none; }
.timeline-step.visible { opacity: 1; transform: translateX(0); }
.timeline-node {
  width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
  display: grid; place-items: center;
  font-size: 13px; font-weight: 700;
  border: 2px solid; background: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}
.timeline-node.node-active {
  background: currentColor; color: #fff !important;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.25);
}
.timeline-body h4 { font-size: 16px; font-weight: 700; color: var(--intro-text); margin-bottom: 6px; }
.timeline-body p { font-size: 14px; color: var(--intro-text-secondary); line-height: 1.75; font-weight: 500; }

/* ── CTA ── */
.cta-section { padding-bottom: 0; margin-top: 48px; }
.cta-card {
  position: relative; overflow: hidden;
  background: #fff;
  border: 1px solid var(--intro-border);
  border-radius: 20px;
  padding: 64px 48px; text-align: center;
  box-shadow: var(--intro-shadow);
  opacity: 0; transform: translateY(24px);
  transition: all 0.5s ease;
}
.cta-card.visible { opacity: 1; transform: translateY(0); }
.cta-orb {
  position: absolute; border-radius: 50%; pointer-events: none; filter: blur(80px);
}
.cta-orb--a { width: 320px; height: 320px; top: -80px; left: -60px; background: rgba(0, 122, 255, 0.08); animation: aurora 18s ease-in-out infinite; }
.cta-orb--b { width: 260px; height: 260px; bottom: -60px; right: -40px; background: rgba(88, 86, 214, 0.06); animation: aurora 22s ease-in-out infinite reverse; }
.cta-card h2 {
  font-size: clamp(28px,3.5vw,48px); font-weight: 700;
  color: var(--intro-text);
  margin-bottom: 16px;
}
.cta-card > p { color: var(--intro-text-secondary); font-size: 15px; line-height: 1.85; margin-bottom: 32px; font-weight: 500; }
.cta-actions { display: flex; gap: 12px; justify-content: center; }

@keyframes aurora {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.85; }
  50% { transform: translate(12px, -8px) scale(1.05); opacity: 1; }
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .features-grid { grid-template-columns: repeat(2,1fr); }
  .stats-grid { grid-template-columns: repeat(2,1fr); }
}
@media (max-width: 900px) {
  .pill-nav__links { display: none; }
  .pill-nav__row { gap: 8px; flex-wrap: wrap; justify-content: center; max-width: calc(100vw - 24px); }
  .pill-nav__row .start-btn-glow { height: 36px; padding: 0 16px; font-size: 13px; }
  .ig-hero { padding-top: 100px; }
  .hero-title { font-size: 44px; }
  .intro-glass-wrapper {
    padding: 28px 18px 48px;
  }
  .stats-section { margin-bottom: 32px; }
  .timeline-section { margin-top: 32px; }
  .cta-section { margin-top: 32px; }
  .features-grid, .roles-grid { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: repeat(2,1fr); }
  .float-bubble { display: none; }
  .cta-card { padding: 40px 24px; }
  .cta-actions { flex-direction: column; align-items: center; }
  .timeline { padding: 24px 24px 24px 56px; }
}
</style>
