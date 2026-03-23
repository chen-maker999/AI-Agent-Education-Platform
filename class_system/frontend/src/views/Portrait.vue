<template>
  <div class="portrait-page">
    <!-- macOS Window Card -->
    <div class="mac-window" role="application" aria-label="学习画像">

      <!-- Title Bar -->
      <header class="titlebar">
        <div class="titlebar-title">学习画像 — PORTRAIT WORKSPACE</div>
        <span class="titlebar-hint">多维度能力与风险评估</span>
      </header>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="segmented" role="tablist" aria-label="视图模式">
          <button
            v-for="item in viewModes"
            :key="item.value"
            type="button"
            :aria-pressed="activeView === item.value ? 'true' : 'false'"
            @click="activeView = item.value"
          >
            {{ item.label }}
          </button>
        </div>

        <button type="button" class="tb-btn" title="刷新数据" @click="onRefresh">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          刷新
        </button>

        <div class="toolbar-spacer"></div>

        <!-- Search -->
        <div class="search-field">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>
          </svg>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="搜索画像…"
            autocomplete="off"
          />
        </div>
      </div>

      <!-- Main Content: Three-column split -->
      <div class="split-root">

        <!-- LEFT: Sidebar -->
        <aside class="sidebar" aria-label="画像维度">
          <div class="sidebar-header">画像维度</div>

          <nav class="filter-list">
            <button
              v-for="chip in dimensionChips"
              :key="chip.value"
              type="button"
              class="filter-chip"
              :class="{ active: selectedDimension === chip.value }"
              @click="selectedDimension = chip.value"
            >
              <span class="chip-icon" :style="{ background: chip.color }"></span>
              {{ chip.label }}
              <span class="count">{{ chip.value === 'all' ? portrait.mastery + '%' : chip.count }}</span>
            </button>
          </nav>

          <div class="sidebar-footer">
            <div class="stat-row">
              <span>风险等级</span>
              <strong :class="riskClass">{{ portrait.risk }}</strong>
            </div>
            <div class="stat-row">
              <span>更新时间</span>
              <strong>{{ updateTime }}</strong>
            </div>
          </div>
        </aside>

        <!-- MIDDLE: Canvas pane -->
        <section class="canvas-pane" aria-label="画像画布">
          <div class="canvas-toolbar">
            <span class="canvas-title">{{ activeViewLabel }}</span>
            <span class="hint">点击卡片查看右侧详情</span>
          </div>

          <div class="canvas-body">
            <div class="canvas-grid" aria-hidden="true"></div>

            <!-- Metric Cards Grid -->
            <div class="metric-cards-grid">
              <div class="metric-card-item" :class="{ active: selectedDimension === 'mastery' }">
                <div class="metric-icon" style="--icon-color: #34C759;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22,4 12,14.01 9,11.01"/>
                  </svg>
                </div>
                <div class="metric-content">
                  <div class="metric-value">{{ portrait.mastery }}%</div>
                  <div class="metric-label">知识掌握度</div>
                  <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: 78%; background: #34C759;"></div>
                  </div>
                </div>
              </div>

              <div class="metric-card-item" :class="{ active: selectedDimension === 'focus' }">
                <div class="metric-icon" style="--icon-color: #007AFF;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
                  </svg>
                </div>
                <div class="metric-content">
                  <div class="metric-value">{{ portrait.focus }}%</div>
                  <div class="metric-label">学习专注度</div>
                  <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: 65%; background: #007AFF;"></div>
                  </div>
                </div>
              </div>

              <div class="metric-card-item" :class="{ active: selectedDimension === 'completion' }">
                <div class="metric-icon" style="--icon-color: #FF9500;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9,11 12,14 22,4"/>
                    <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
                  </svg>
                </div>
                <div class="metric-content">
                  <div class="metric-value">{{ portrait.completion }}%</div>
                  <div class="metric-label">任务完成率</div>
                  <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: 72%; background: #FF9500;"></div>
                  </div>
                </div>
              </div>

              <div class="metric-card-item" :class="{ active: selectedDimension === 'risk' }">
                <div class="metric-icon" :style="{ '--icon-color': portrait.risk.includes('高') ? '#FF3B30' : '#FF9500' }">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                </div>
                <div class="metric-content">
                  <div class="metric-value">{{ portrait.risk }}</div>
                  <div class="metric-label">风险标签</div>
                  <div class="metric-bar">
                    <div class="metric-bar-fill" :style="{ width: portrait.risk.includes('高') ? '85%' : '45%', background: portrait.risk.includes('高') ? '#FF3B30' : '#FF9500' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Strengths & Weaknesses -->
            <div class="profile-sections">
              <div class="profile-section">
                <div class="section-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3zM7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/>
                  </svg>
                  优势项
                </div>
                <div class="chip-grid">
                  <span v-for="item in portrait.strengths" :key="item" class="chip chip-success">{{ item }}</span>
                </div>
              </div>

              <div class="profile-section">
                <div class="section-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  待提升项
                </div>
                <div class="chip-grid">
                  <span v-for="item in portrait.weaknesses" :key="item" class="chip chip-warning">{{ item }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- RIGHT: Inspector -->
        <aside class="inspector" aria-label="画像详情">
          <div class="inspector-header">画像详情</div>
          <div class="inspector-body">

            <div v-if="!selectedDimension || selectedDimension === 'all'" class="inspector-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <h4>选择一个维度</h4>
              <p>在左侧或上方选择一个维度后，此处显示详细信息、分析建议和推荐动作。</p>
            </div>

            <div v-else class="dimension-detail">
              <div class="group-box">
                <h5>维度信息</h5>
                <div class="row"><span>名称</span><span>{{ currentDimension.label }}</span></div>
                <div class="row"><span>当前值</span><span>{{ currentDimension.value }}</span></div>
                <div class="row"><span>状态</span><span :class="currentDimension.tone">{{ currentDimension.status }}</span></div>
              </div>

              <div class="group-box">
                <h5>分析建议</h5>
                <p class="analysis-text">{{ currentDimension.analysis }}</p>
              </div>

              <div class="group-box">
                <h5>推荐动作</h5>
                <div class="action-list">
                  <button type="button" class="action-btn" @click="onAction(action)" v-for="action in currentDimension.actions" :key="action">
                    {{ action }}
                  </button>
                </div>
              </div>

              <div class="group-box">
                <h5>历史趋势</h5>
                <div class="trend-chart">
                  <div class="trend-bars">
                    <div class="trend-bar" v-for="(val, i) in currentDimension.trend" :key="i" :style="{ height: val + '%' }"></div>
                  </div>
                  <div class="trend-labels">
                    <span>周1</span><span>周2</span><span>周3</span><span>周4</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="inspector-actions">
            <button type="button" class="btn" @click="onExport">导出报告</button>
            <button type="button" class="btn btn-primary" @click="onRefreshPortrait">更新画像</button>
          </div>
        </aside>
      </div>

      <!-- Status Bar -->
      <footer class="statusline">
        <span>学习画像</span>
        <span class="sep">|</span>
        <span>维度：{{ selectedDimensionLabel }}</span>
        <span class="sep">|</span>
        <span>风险：{{ portrait.risk }}</span>
      </footer>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { portraitApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { summarizePortrait } from '@/utils/viewModels'

const authStore = useAuthStore()

// View modes
const viewModes = [
  { label: '概览', value: 'overview' },
  { label: '能力', value: 'ability' },
  { label: '风险', value: 'risk' }
]
const activeView = ref('overview')
const searchQuery = ref('')

// Portrait data
const portrait = ref(summarizePortrait())

// Dimension chips
const selectedDimension = ref('all')

const dimensionChips = computed(() => [
  { label: '全部', value: 'all', color: '#007AFF', count: portrait.value.mastery + '%' },
  { label: '掌握度', value: 'mastery', color: '#34C759', count: portrait.value.mastery + '%' },
  { label: '专注度', value: 'focus', color: '#007AFF', count: portrait.value.focus + '%' },
  { label: '完成率', value: 'completion', color: '#FF9500', count: portrait.value.completion + '%' },
  { label: '风险', value: 'risk', color: portrait.value.risk.includes('高') ? '#FF3B30' : '#FF9500', count: portrait.value.risk }
])

const currentDimension = computed(() => {
  const dim = selectedDimension.value
  const p = portrait.value
  
  const dimensionMap = {
    mastery: {
      label: '知识掌握度',
      value: p.mastery + '%',
      status: p.mastery >= 80 ? '优秀' : p.mastery >= 60 ? '良好' : '待提升',
      tone: p.mastery >= 80 ? 'tone-success' : p.mastery >= 60 ? 'tone-warning' : 'tone-danger',
      analysis: '当前知识掌握度处于' + (p.mastery >= 80 ? '优秀水平，建议保持当前学习节奏并拓展深度' : p.mastery >= 60 ? '良好水平，建议加强薄弱环节的练习' : '待提升阶段，需要重点关注基础概念理解'),
      actions: ['查看评估详情', '生成练习', '追问知识点'],
      trend: [65, 72, 68, 78]
    },
    focus: {
      label: '学习专注度',
      value: p.focus + '%',
      status: p.focus >= 70 ? '良好' : '待提升',
      tone: p.focus >= 70 ? 'tone-info' : 'tone-warning',
      analysis: '学习专注度' + (p.focus >= 70 ? '表现良好，建议保持规律的作息时间' : '有提升空间，建议减少干扰因素，设定专注时间段'),
      actions: ['专注模式', '调整计划', '查看历史'],
      trend: [55, 62, 58, 65]
    },
    completion: {
      label: '任务完成率',
      value: p.completion + '%',
      status: p.completion >= 75 ? '优秀' : p.completion >= 50 ? '一般' : '待提升',
      tone: p.completion >= 75 ? 'tone-success' : p.completion >= 50 ? 'tone-warning' : 'tone-danger',
      analysis: '任务完成率' + (p.completion >= 75 ? '处于较高水平，学习效率良好' : '有待提高，建议优化时间管理和任务分解能力'),
      actions: ['查看任务列表', '调整任务', '生成计划'],
      trend: [60, 65, 70, 72]
    },
    risk: {
      label: '风险标签',
      value: p.risk,
      status: p.risk.includes('高') ? '需关注' : '正常',
      tone: p.risk.includes('高') ? 'tone-danger' : 'tone-warning',
      analysis: '当前' + (p.risk.includes('高') ? '存在较高的学习风险，建议及时调整学习策略并寻求帮助' : '学习状态正常，建议继续保持'),
      actions: ['查看预警', '联系教师', '调整计划'],
      trend: [30, 45, 60, 85]
    }
  }
  
  return dimensionMap[dim] || {
    label: '全部',
    value: p.mastery + '%',
    status: '综合',
    tone: 'tone-info',
    analysis: '学习画像综合了知识掌握度、学习专注度、任务完成率和风险评估等多个维度，全面反映学习状态。',
    actions: ['查看完整报告', '联系教师', '生成学习计划'],
    trend: [65, 70, 75, 78]
  }
})

const riskClass = computed(() => portrait.value.risk.includes('高') ? 'risk-high' : 'risk-low')
const updateTime = computed(() => new Date().toLocaleDateString('zh-CN'))

const activeViewLabel = computed(() => viewModes.find(v => v.value === activeView.value)?.label ?? '概览')
const selectedDimensionLabel = computed(() => dimensionChips.value.find(c => c.value === selectedDimension.value)?.label ?? '全部')

// Actions
function onRefresh() {
  loadPortrait()
}

function onRefreshPortrait() {
  loadPortrait()
}

function onExport() {
  alert('演示：导出当前画像报告为 PDF / JSON')
}

function onAction(action) {
  alert(`演示：执行动作 - ${action}`)
}

async function loadPortrait() {
  try {
    const studentId = authStore.user?.id || 'current_user'
    const [detailRes, strengthsRes, weaknessesRes, progressRes] = await Promise.all([
      portraitApi.get(studentId),
      portraitApi.strengths(studentId),
      portraitApi.weaknesses(studentId),
      portraitApi.progress(studentId)
    ])

    portrait.value = summarizePortrait(detailRes?.data, {
      strengths: strengthsRes?.data,
      weaknesses: weaknessesRes?.data,
      progress: progressRes?.data
    })
  } catch {
    portrait.value = summarizePortrait()
  }
}

onMounted(() => {
  loadPortrait()
})
</script>

<style scoped>
/* Page wrapper */
.portrait-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* Design tokens */
.mac-window {
  --bg-window: #ececec;
  --bg-content: #f5f5f7;
  --bg-panel: rgba(255, 255, 255, 0.72);
  --bg-panel-solid: #ffffff;
  --bg-sidebar: rgba(246, 246, 246, 0.85);
  --border: rgba(0, 0, 0, 0.08);
  --border-strong: rgba(0, 0, 0, 0.12);
  --text: #1d1d1f;
  --text-secondary: rgba(60, 60, 67, 0.72);
  --text-tertiary: rgba(60, 60, 67, 0.48);
  --accent: #007aff;
  --accent-soft: rgba(0, 122, 255, 0.12);
  --shadow-window: 0 22px 70px rgba(0, 0, 0, 0.12);
  --shadow-panel: 0 1px 3px rgba(0, 0, 0, 0.06);
  --radius-window: 14px;
  --radius-panel: 10px;
  --radius-pill: 980px;
}

.mac-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-window);
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  font-size: 13px;
  color: var(--text);
}

/* Title Bar */
.titlebar {
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: linear-gradient(180deg, #fbfbfb 0%, #ececec 100%);
  border-bottom: 1px solid var(--border);
}

.titlebar-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.titlebar-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* Toolbar */
.toolbar {
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  background: linear-gradient(180deg, #ebebed 0%, #e4e4e7 100%);
  border-bottom: 1px solid var(--border);
}

.segmented {
  display: inline-flex;
  background: rgba(0,0,0,0.06);
  border-radius: 6px;
  padding: 2px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
}

.segmented button {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.segmented button[aria-pressed="true"] {
  background: var(--bg-panel-solid);
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.segmented button:hover:not([aria-pressed="true"]) {
  background: rgba(0,0,0,0.04);
}

.toolbar-spacer { flex: 1; }

.search-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 200px;
  max-width: 280px;
  padding: 4px 10px;
  background: rgba(255,255,255,0.85);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  box-shadow: inset 0 1px 1px rgba(0,0,0,0.04);
}

.search-field:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.search-field input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 12px;
  color: var(--text);
}

.search-field input::placeholder { color: var(--text-tertiary); }
.search-field svg { width: 14px; height: 14px; color: var(--text-tertiary); flex-shrink: 0; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
}

.tb-btn:hover {
  background: #fff;
  border-color: var(--border-strong);
}

.tb-btn svg { width: 14px; height: 14px; }

/* Split Root */
.split-root {
  flex: 1;
  display: flex;
  min-height: 0;
  background: var(--bg-content);
}

/* Left Sidebar */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  backdrop-filter: blur(14px);
}

.sidebar-header {
  padding: 12px 12px 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.filter-list {
  padding: 0 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  max-height: 280px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.12s, color 0.12s;
  background: transparent;
  font-family: inherit;
  text-align: left;
}

.filter-chip:hover { background: rgba(0,0,0,0.04); color: var(--text); }

.filter-chip.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.filter-chip .count {
  margin-left: auto;
  font-size: 10px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
}

.filter-chip.active .count { color: var(--accent); opacity: 0.85; }

.chip-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-tertiary);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 4px 0;
}

.stat-row strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.risk-high { color: #FF3B30; }
.risk-low { color: #34C759; }

/* Middle: Canvas Pane */
.canvas-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: linear-gradient(180deg, #fafafa 0%, #f3f3f5 100%);
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.5);
  flex-shrink: 0;
}

.canvas-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.hint {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-tertiary);
}

.canvas-body {
  flex: 1;
  min-height: 0;
  position: relative;
  background: var(--bg-panel-solid);
  overflow-y: auto;
  padding: 16px;
}

.canvas-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 1px 1px, rgba(0,0,0,0.06) 1px, transparent 0);
  background-size: 18px 18px;
  opacity: 0.7;
  pointer-events: none;
}

/* Metric Cards Grid */
.metric-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.metric-card-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.metric-card-item:hover {
  border-color: rgba(0,122,255,0.3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.metric-card-item.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.metric-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  color: var(--icon-color);
  flex-shrink: 0;
}

.metric-icon svg { width: 22px; height: 22px; }

.metric-content { flex: 1; min-width: 0; }

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.metric-bar {
  height: 4px;
  background: rgba(0,0,0,0.08);
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.metric-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Profile Sections */
.profile-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.profile-section {
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.section-header svg { width: 16px; height: 16px; }

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.chip-success {
  background: rgba(52, 199, 89, 0.15);
  color: #34C759;
}

.chip-warning {
  background: rgba(255, 149, 0, 0.15);
  color: #FF9500;
}

/* Right: Inspector Panel */
.inspector {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(252, 252, 252, 0.92);
  border-left: 1px solid var(--border);
  backdrop-filter: blur(12px);
}

.inspector-header {
  padding: 12px 14px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  text-transform: uppercase;
  flex-shrink: 0;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.inspector-empty {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: var(--text-tertiary);
  padding: 20px;
}

.inspector-empty svg { width: 36px; height: 36px; opacity: 0.4; }
.inspector-empty h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.inspector-empty p { font-size: 12px; line-height: 1.45; }

.group-box {
  background: var(--bg-panel-solid);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.8) inset;
}

.group-box h5 {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.group-box .row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 3px 0;
  color: var(--text-secondary);
}

.group-box .row span:last-child {
  color: var(--text);
  font-weight: 500;
}

.tone-success { color: #34C759; }
.tone-warning { color: #FF9500; }
.tone-danger { color: #FF3B30; }
.tone-info { color: #007AFF; }

.analysis-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-btn {
  width: 100%;
  padding: 6px 10px;
  font-size: 12px;
  font-family: inherit;
  color: var(--accent);
  background: var(--accent-soft);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s;
  text-align: left;
}

.action-btn:hover {
  background: rgba(0, 122, 255, 0.2);
}

/* Trend Chart */
.trend-chart {
  padding: 4px 0;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 50px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border);
}

.trend-bar {
  flex: 1;
  background: linear-gradient(180deg, var(--accent) 0%, rgba(0, 122, 255, 0.4) 100%);
  border-radius: 3px 3px 0 0;
  min-height: 8px;
  transition: height 0.3s ease;
}

.trend-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 10px;
  color: var(--text-tertiary);
}

.inspector-actions {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn {
  flex: 1;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-strong);
  background: linear-gradient(180deg, #fff 0%, #f2f2f3 100%);
  color: var(--text);
  cursor: pointer;
  transition: filter 0.12s, box-shadow 0.12s;
}

.btn:hover { filter: brightness(1.02); }
.btn:active { filter: brightness(0.98); }

.btn-primary {
  border-color: rgba(0, 122, 255, 0.45);
  background: linear-gradient(180deg, #4da2ff 0%, #007aff 100%);
  color: #fff;
}

/* Status Bar */
.statusline {
  height: 24px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 11px;
  color: var(--text-tertiary);
  background: linear-gradient(180deg, #e9e9eb 0%, #e2e2e5 100%);
  border-top: 1px solid var(--border);
}

.statusline .sep { margin: 0 8px; opacity: 0.5; }

/* Responsive */
@media (max-width: 900px) {
  .portrait-page { padding: 12px; }
  .mac-window { width: 100%; }
  .inspector { width: 260px; }
  .sidebar { width: 190px; }
  .metric-cards-grid { grid-template-columns: 1fr; }
  .profile-sections { grid-template-columns: 1fr; }
}

@media (max-width: 720px) {
  .split-root { flex-direction: column; }
  .sidebar, .inspector {
    width: 100%;
    border-right: none;
    border-left: none;
    border-bottom: 1px solid var(--border);
  }
  .canvas-pane { min-height: 280px; }
}
</style>
