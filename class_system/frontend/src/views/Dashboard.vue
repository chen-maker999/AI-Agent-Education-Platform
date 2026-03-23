<template>
  <div class="workspace-page">
    <!-- 加载动画 Overlay -->
    <Transition name="loader-fade">
      <div v-if="isLoading" class="splash-overlay">
        <iframe
          src="https://my.spline.design/pathgrowthanimation-9znyCYaQ6XjBoBQx9Qsbhq7u"
          frameborder="0"
          width="100%"
          height="100%"
          class="splash-iframe"
        ></iframe>
      </div>
    </Transition>

    <!-- Spline 3D animated background (浅色白底 + 蓝光) -->
    <div class="spline-container">
      <iframe
        src="https://my.spline.design/ventura2copy-QlljPuDvQWfMiAnUXFOrCrsY"
        frameborder="0"
        width="100%"
        height="100%"
        id="aura-spline"
      ></iframe>
    </div>
    <!-- ═══ HERO BANNER ═══ -->
    <div class="dash-hero">
      <div class="dash-hero__bg">
        <svg viewBox="0 0 800 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
          <defs>
            <linearGradient id="dhLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#2563eb" stop-opacity="0"/>
              <stop offset="50%" stop-color="#2563eb" stop-opacity="0.5"/>
              <stop offset="100%" stop-color="#0891b2" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="1" x2="800" y2="1" stroke="url(#dhLine)" stroke-width="1.5"/>
          <g opacity="0.03" stroke="#a0c8ff" stroke-width="0.5">
            <line v-for="i in 12" :key="i" :x1="i*65" y1="0" :x2="i*65" y2="200"/>
          </g>
          <circle cx="680" cy="100" r="60" fill="none" stroke="rgba(48,112,255,0.06)" stroke-dasharray="4 10" class="dash-orbit"/>
          <circle r="2.5" fill="#2563eb" opacity="0.6">
            <animateMotion dur="12s" repeatCount="indefinite" path="M680,40 A60,60 0 1,1 679,40"/>
          </circle>
        </svg>
      </div>
      <div class="dash-hero__content">
        <p class="section-label">{{ workspaceLabel }}</p>
        <h2 class="dash-hero__title">{{ heroTitle }}</h2>
        <p class="dash-hero__desc">{{ heroDescription }}</p>
      </div>
      <div class="dash-hero__actions">
        <router-link to="/chat" class="btn-primary">进入智能问答</router-link>
        <router-link to="/knowledge" class="btn-secondary">查看知识资产</router-link>
      </div>
    </div>

    <!-- ═══ METRICS ═══ -->
    <div class="metric-grid">
      <MetricCard icon="search" value="1 个" label="统一搜索入口" hint="跨课程、跨模块、跨角色检索" />
      <MetricCard icon="database" :value="docCount" label="知识文档" hint="可用于问答、图谱与引用追踪" />
      <MetricCard icon="file" :value="homeworkCount" label="作业总量" hint="学生提交与教师批改共用同一工作台" />
      <MetricCard :icon="focusMetric.icon" :value="focusMetric.value" :label="focusMetric.label" :hint="focusMetric.hint" :tone="focusMetric.tone" />
    </div>

    <!-- ═══ MAIN CONTENT ═══ -->
    <div class="workspace-split">
      <div class="workspace-stack">
        <PanelCard title="今日优先动作" subtitle="把最高价值的入口直接铺到工作台第一屏。">
          <div class="resource-list">
            <div v-for="task in tasks" :key="task.title" class="resource-item dash-task">
              <div class="dash-task__indicator" :class="task.toneClass"></div>
              <div class="dash-task__body">
                <h4>{{ task.title }}</h4>
                <p>{{ task.description }}</p>
                <div class="meta-row">
                  <span class="tone-pill" :class="task.toneClass">{{ task.meta }}</span>
                  <router-link :to="task.to" class="link-inline">立即进入 →</router-link>
                </div>
              </div>
            </div>
          </div>
        </PanelCard>

        <PanelCard title="最近知识资产" subtitle="面向问答、图谱、画像和教学复用的统一素材底座。">
          <div v-if="recentDocuments.length" class="resource-list">
            <div v-for="doc in recentDocuments" :key="doc.id" class="resource-item">
              <h4>{{ doc.title }}</h4>
              <p>{{ doc.course }} · {{ doc.status }} · {{ doc.chunks }} 个知识块</p>
              <div class="meta-row">
                <span class="chip">{{ doc.updatedAt }}</span>
              </div>
            </div>
          </div>
          <InfoState v-else title="知识资产尚未准备" description="上传课件、讲义或实验资料后，这里会显示最近索引结果。"/>
        </PanelCard>
      </div>

      <div class="workspace-stack">
        <PanelCard title="核心能力面板" subtitle="竞赛题目中最关键的功能都能从这里一跳直达。">
          <div class="dash-caps">
            <router-link v-for="cap in capabilities" :key="cap.to" :to="cap.to" class="dash-cap">
              <div class="dash-cap__icon" :style="`--cap-color:${cap.color}`">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="3" :fill="cap.color" opacity="0.8"/>
                  <circle cx="8" cy="8" r="6" :stroke="cap.color" stroke-width="1" opacity="0.3"/>
                </svg>
              </div>
              <span>{{ cap.label }}</span>
            </router-link>
          </div>
        </PanelCard>

        <PanelCard title="推荐路径" subtitle="根据当前角色自动调整下一步建议。">
          <div class="timeline-list">
            <div v-for="(item, i) in recommendations" :key="item.title" class="timeline-item dash-timeline">
              <div class="dash-timeline__num">{{ i + 1 }}</div>
              <div>
                <h4>{{ item.title }}</h4>
                <p>{{ item.description }}</p>
              </div>
            </div>
          </div>
        </PanelCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { homeworkApi, ragApi, warningApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { summarizeDocuments } from '@/utils/viewModels'
import { getUserRole, getWorkspaceLabel } from '@/utils/workspace'
import InfoState from '@/components/ui/InfoState.vue'
import MetricCard from '@/components/ui/MetricCard.vue'
import PanelCard from '@/components/ui/PanelCard.vue'

const authStore = useAuthStore()
const role = computed(() => getUserRole(authStore.user))
const isTeacher = computed(() => role.value === 'teacher' || role.value === 'admin')
const workspaceLabel = computed(() => getWorkspaceLabel(role.value))

const docCount = ref(0)
const homeworkCount = ref(0)
const warningCount = ref(0)
const recentDocuments = ref([])
const isLoading = ref(true)

const heroTitle = computed(() => `欢迎回来，${authStore.user?.username || (isTeacher.value ? '老师' : '同学')}`)
const heroDescription = computed(() => {
  if (isTeacher.value) return '这里聚合了班级风险、批改队列、知识更新与教学建议，帮助你更快完成干预与决策。'
  return '这里是你的学习工作台，统一收纳问答、作业反馈、知识关系和阶段性成长洞察。'
})

const focusMetric = computed(() => {
  if (isTeacher.value) return { icon: 'alert', value: `${warningCount.value} 条`, label: '活跃预警', hint: '班级风险与干预动作联动', tone: warningCount.value > 0 ? 'warning' : 'success' }
  return { icon: 'radar', value: '84%', label: '当前掌握度', hint: '来自画像与阶段评估的综合判断', tone: 'success' }
})

const capabilities = computed(() => {
  const base = [
    { to: '/chat', label: '智能问答', color: '#2563eb' },
    { to: '/knowledge', label: '知识资产', color: '#0891b2' },
    { to: '/graph', label: '知识图谱', color: '#a080ff' },
    { to: '/homework', label: '作业批注', color: '#20f0a8' },
    { to: '/portrait', label: '学习画像', color: '#ffb850' },
  ]
  if (isTeacher.value) base.push({ to: '/warning', label: '预警驾驶舱', color: '#ff6098' })
  return base
})

const tasks = computed(() => {
  if (isTeacher.value) return [
    { title: '优先处理高风险学生', description: '查看近期成绩波动、作业缺失和投入异常学生。', meta: `${warningCount.value} 条待处理`, toneClass: warningCount.value ? 'tone-warning' : 'tone-success', to: '/warning' },
    { title: '检查批改队列', description: '集中处理待批改作业、文档预览和精细化批注入口。', meta: `${homeworkCount.value} 份作业`, toneClass: 'tone-info', to: '/homework' }
  ]
  return [
    { title: '发起知识问答', description: '基于课程资料进行多轮追问，保留引用来源与下一步建议。', meta: `${docCount.value} 份知识素材`, toneClass: 'tone-info', to: '/chat' },
    { title: '回看最近作业反馈', description: '从作业批注里定位问题，串联到知识图谱和推荐练习。', meta: `${homeworkCount.value} 份作业`, toneClass: 'tone-success', to: '/homework' }
  ]
})

const recommendations = computed(() => {
  if (isTeacher.value) return [
    { title: '更新课程知识资产', description: '补充新课件和实验资料，提升问答和图谱质量。' },
    { title: '联动预警与画像', description: '把风险信号回接到学生画像与个性化练习方案。' },
    { title: '检查批注质量', description: '验证精细化批注是否覆盖关键错误与上下文解释。' }
  ]
  return [
    { title: '先查知识图谱', description: '用知识关系理解本周重点与先修链路。' },
    { title: '再追问难点', description: '将困惑带入智能问答，拿到引用式解释。' },
    { title: '最后回到画像', description: '结合评估结果确认下一轮增量练习方向。' }
  ]
})

onMounted(async () => {
  try { const r = await ragApi.listDocuments(); recentDocuments.value = summarizeDocuments(r?.data).slice(0,4); docCount.value = recentDocuments.value.length } catch { recentDocuments.value = []; docCount.value = 0 }
  try { const r = await homeworkApi.statistics(); homeworkCount.value = r?.data?.total_files || 0 } catch { homeworkCount.value = 0 }
  if (isTeacher.value) { try { const r = await warningApi.stats(); warningCount.value = (r?.data?.high||0)+(r?.data?.medium||0) } catch { warningCount.value = 0 } }
  
  // 4秒后隐藏加载动画
  setTimeout(() => { isLoading.value = false }, 4000)
})
</script>

<style scoped>
/* 加载动画 Overlay */
.splash-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
}
.splash-iframe {
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
  transform: translateX(120px);
}
.loader-fade-leave-active {
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}
.loader-fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}
.loader-fade-enter-active {
  transition: opacity 0.3s ease-in;
}
.loader-fade-enter-from {
  opacity: 0;
}

.spline-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  border-radius: 0;
  overflow: hidden;
}
.spline-container iframe {
  width: 100%;
  height: 100%;
  display: block;
}
.workspace-page {
  max-width: 1100px;
  margin-left: auto;
  margin-right: auto;
}

/* Hero */
.dash-hero {
  position: relative; overflow: hidden;
  padding: 28px 32px; border-radius: var(--r-3xl);
  background: var(--glass-bg); border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur);
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  animation: fade-in-up 0.6s var(--ease-expo) both;
}
.dash-hero__bg {
  position: absolute; inset: 0; pointer-events: none;
}
.dash-hero__bg svg { width: 100%; height: 100%; }
.dash-orbit { animation: spin-slow 20s linear infinite; transform-origin: 680px 100px; }
.dash-hero__content { position: relative; z-index: 1; flex: 1; }
.dash-hero__title { font-size: clamp(24px, 2.8vw, 36px); margin-bottom: 8px; font-family: var(--font-display2); }
.dash-hero__desc { color: var(--text-secondary); line-height: 1.8; max-width: 600px; font-size: 14px; }
.dash-hero__actions { position: relative; z-index: 1; display: flex; gap: 10px; flex-shrink: 0; }

/* Task items */
.dash-task { display: flex; gap: 14px; align-items: stretch; }
.dash-task__indicator {
  width: 3px; border-radius: 3px; flex-shrink: 0;
  background: var(--brand-500);
}
.dash-task__indicator.tone-warning { background: var(--amber-400); }
.dash-task__indicator.tone-success { background: var(--emerald-400); }
.dash-task__indicator.tone-info { background: var(--brand-400); }
.dash-task__indicator.tone-danger { background: var(--rose-400); }
.dash-task__body { flex: 1; }

/* Capabilities grid */
.dash-caps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.dash-cap {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 16px 8px; border-radius: var(--r-xl);
  background: rgba(255,255,255,0.90); border: 1px solid rgba(37,99,235,0.12);
  box-shadow: var(--shadow-xs);
  transition: all var(--t-base) var(--ease-out);
  text-align: center; font-size: 13px; font-weight: 500;
  color: var(--text-secondary);
}
.dash-cap:hover {
  background: rgba(255,255,255,0.98); border-color: rgba(37,99,235,0.24);
  transform: translateY(-3px); color: var(--text-primary);
  box-shadow: var(--shadow-sm), 0 0 0 1px rgba(37,99,235,0.12);
}
.dash-cap__icon {
  width: 36px; height: 36px; display: grid; place-items: center;
  border-radius: var(--r-md);
  background: rgba(37,99,235,0.08);
}

/* Timeline */
.dash-timeline { display: flex; gap: 14px; align-items: flex-start; }
.dash-timeline__num {
  width: 28px; height: 28px; display: grid; place-items: center;
  border-radius: 50%; flex-shrink: 0;
  background: rgba(48,112,255,0.10); border: 1px solid rgba(48,112,255,0.20);
  color: var(--brand-300); font-size: 12px; font-weight: 700;
}

@media (max-width: 900px) {
  .dash-hero { flex-direction: column; align-items: stretch; }
  .dash-caps { grid-template-columns: repeat(2, 1fr); }
}

/* ── Light mode overrides ── */
:global([data-theme="light"]) .dash-cap {
  background: rgba(36, 104, 232, 0.05);
  border-color: rgba(36, 104, 232, 0.14);
}
:global([data-theme="light"]) .dash-cap:hover {
  background: rgba(36, 104, 232, 0.10);
  border-color: rgba(36, 104, 232, 0.24);
  box-shadow: 0 8px 24px rgba(36, 80, 180, 0.10);
}
:global([data-theme="light"]) .dash-cap__icon {
  background: rgba(36, 104, 232, 0.08);
}
</style>
