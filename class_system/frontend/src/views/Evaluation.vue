<template>
  <div class="evaluation-page">
    <!-- macOS Window Card -->
    <div class="mac-window" role="application" aria-label="学习评估">

      <!-- Title Bar -->
      <header class="titlebar">
        <div class="titlebar-title">学习评估 — ASSESSMENT WORKSPACE</div>
        <span class="titlebar-hint">掌握度、趋势与课程分析</span>
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

        <button type="button" class="tb-btn" title="开始评估" @click="onStartEvaluation">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5,3 19,12 5,21"/>
          </svg>
          开始评估
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
            placeholder="搜索课程或知识点…"
            autocomplete="off"
          />
        </div>

        <button type="button" class="tb-btn" title="导出报告" @click="onExport">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          导出
        </button>
      </div>

      <!-- Main Content: Three-column split -->
      <div class="split-root">

        <!-- LEFT: Sidebar -->
        <aside class="sidebar" aria-label="评估维度">
          <div class="sidebar-header">评估维度</div>

          <nav class="filter-list">
            <button
              v-for="chip in dimensionChips"
              :key="chip.value"
              type="button"
              class="filter-chip"
              :class="{ active: selectedDimension === chip.value }"
              @click="selectedDimension = chip.value"
            >
              <span class="chip-dot" :style="{ background: chip.color }"></span>
              {{ chip.label }}
              <span class="count">{{ chip.value === 'all' ? courseCards.length : chip.count }}</span>
            </button>
          </nav>

          <div class="sidebar-footer">
            <div class="stat-row">
              <span>整体评级</span>
              <strong class="grade-badge">{{ evaluation.grade }}</strong>
            </div>
            <div class="stat-row">
              <span>进步趋势</span>
              <strong :class="progressTrend > 0 ? 'trend-up' : 'trend-down'">
                {{ progressTrend > 0 ? '+' : '' }}{{ progressTrend }}%
              </strong>
            </div>
          </div>
        </aside>

        <!-- MIDDLE: Canvas pane -->
        <section class="canvas-pane" aria-label="评估画布">
          <div class="canvas-toolbar">
            <span class="canvas-title">{{ activeViewLabel }}</span>
            <span class="hint">点击课程查看右侧详情</span>
          </div>

          <div class="canvas-body">
            <div class="canvas-grid" aria-hidden="true"></div>

            <!-- Metric Overview -->
            <div class="metric-overview">
              <div class="overview-card">
                <div class="overview-icon" style="--icon-color: #34C759;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22,4 12,14.01 9,11.01"/>
                  </svg>
                </div>
                <div class="overview-content">
                  <div class="overview-value">{{ evaluation.mastery }}%</div>
                  <div class="overview-label">整体掌握度</div>
                </div>
                <div class="overview-bar">
                  <div class="overview-bar-fill" :style="{ width: evaluation.mastery + '%', background: '#34C759' }"></div>
                </div>
              </div>

              <div class="overview-card">
                <div class="overview-icon" style="--icon-color: #007AFF;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"/>
                    <polyline points="17,6 23,6 23,12"/>
                  </svg>
                </div>
                <div class="overview-content">
                  <div class="overview-value">{{ evaluation.progress }}%</div>
                  <div class="overview-label">阶段进步</div>
                </div>
                <div class="overview-bar">
                  <div class="overview-bar-fill" :style="{ width: evaluation.progress + '%', background: '#007AFF' }"></div>
                </div>
              </div>
            </div>

            <!-- Course Cards -->
            <div class="course-grid">
              <button
                v-for="(course, index) in filteredCourses"
                :key="course.name"
                type="button"
                class="course-card"
                :class="{ active: selectedCourse?.name === course.name }"
                :style="{ animationDelay: index * 60 + 'ms' }"
                @click="selectedCourse = course"
              >
                <div class="course-card-header">
                  <span class="course-name">{{ course.name }}</span>
                  <span class="course-grade" :class="course.tone">{{ course.grade }}</span>
                </div>
                <p class="course-summary">{{ course.summary }}</p>
                <div class="course-progress">
                  <div class="progress-info">
                    <span>掌握进度</span>
                    <strong>{{ course.progress }}%</strong>
                  </div>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: course.progress + '%', background: course.tone === 'tone-success' ? '#34C759' : course.tone === 'tone-warning' ? '#FF9500' : '#007AFF' }"></div>
                  </div>
                </div>
              </button>
            </div>

            <!-- Insights Section -->
            <div class="insights-section">
              <div class="insights-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                趋势与洞察
              </div>
              <div class="insights-list">
                <div class="insight-item">
                  <div class="insight-icon up">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="18,15 12,9 6,15"/>
                    </svg>
                  </div>
                  <div class="insight-content">
                    <h4>本周提升点</h4>
                    <p>知识点掌握度从 {{ Math.max(evaluation.mastery - 6, 0) }}% 提升到 {{ evaluation.mastery }}%，建议继续强化错因相关练习。</p>
                  </div>
                </div>
                <div class="insight-item">
                  <div class="insight-icon info">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </div>
                  <div class="insight-content">
                    <h4>画像联动</h4>
                    <p>评估结果将同步回学习画像中的能力雷达、薄弱点和风险标签。</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- RIGHT: Inspector -->
        <aside class="inspector" aria-label="评估详情">
          <div class="inspector-header">评估详情</div>
          <div class="inspector-body">

            <div v-if="!selectedCourse" class="inspector-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
              </svg>
              <h4>选择一个课程</h4>
              <p>在左侧选择一个课程后，此处显示详细的评估分析、历史记录和建议。</p>
            </div>

            <div v-else class="course-detail">
              <div class="group-box">
                <h5>课程信息</h5>
                <div class="row"><span>课程名称</span><span>{{ selectedCourse.name }}</span></div>
                <div class="row"><span>掌握进度</span><span>{{ selectedCourse.progress }}%</span></div>
                <div class="row"><span>综合评级</span><span :class="selectedCourse.tone">{{ selectedCourse.grade }}</span></div>
              </div>

              <div class="group-box">
                <h5>评估摘要</h5>
                <p class="analysis-text">{{ selectedCourse.summary }}</p>
              </div>

              <div class="group-box">
                <h5>推荐动作</h5>
                <div class="action-list">
                  <button type="button" class="action-btn" @click="onAction('回看错题')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14,2 14,8 20,8"/>
                    </svg>
                    回看错题
                  </button>
                  <button type="button" class="action-btn" @click="onAction('生成练习')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polygon points="5,3 19,12 5,21"/>
                    </svg>
                    生成练习
                  </button>
                  <button type="button" class="action-btn" @click="onAction('追问知识点')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    追问知识点
                  </button>
                </div>
              </div>

              <div class="group-box">
                <h5>评估历史</h5>
                <div v-if="evaluation.history.length" class="history-list">
                  <div v-for="item in evaluation.history.slice(0, 5)" :key="item.id" class="history-item">
                    <div class="history-date">{{ item.date }}</div>
                    <div class="history-title">{{ item.title }}</div>
                    <div class="history-score">{{ item.score }}</div>
                  </div>
                </div>
                <div v-else class="no-history">
                  暂无历史记录
                </div>
              </div>
            </div>
          </div>

          <div class="inspector-actions">
            <button type="button" class="btn" @click="onExport">导出报告</button>
            <button type="button" class="btn btn-primary" @click="onStartEvaluation">开始评估</button>
          </div>
        </aside>
      </div>

      <!-- Status Bar -->
      <footer class="statusline">
        <span>学习评估</span>
        <span class="sep">|</span>
        <span>课程数: {{ courseCards.length }}</span>
        <span class="sep">|</span>
        <span>整体评级: {{ evaluation.grade }}</span>
        <span class="sep">|</span>
        <span>进步: {{ evaluation.progress }}%</span>
      </footer>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { evaluationApi } from '@/api'
import { summarizeEvaluation } from '@/utils/viewModels'

// View modes
const viewModes = [
  { label: '概览', value: 'overview' },
  { label: '课程', value: 'course' },
  { label: '趋势', value: 'trend' }
]
const activeView = ref('overview')
const searchQuery = ref('')

// Dimension chips
const selectedDimension = ref('all')
const selectedCourse = ref(null)

// Evaluation data
const evaluation = ref({
  mastery: 84,
  progress: 67,
  grade: 'A-',
  history: []
})

const courseCards = ref([
  {
    name: 'Python 编程',
    summary: '语法基础与面向对象掌握较好，建议继续加强异常处理与工程化意识。',
    progress: 88,
    grade: 'A',
    tone: 'tone-success'
  },
  {
    name: '算法设计',
    summary: '递归与动态规划提升明显，但复杂度分析仍需巩固。',
    progress: 76,
    grade: 'B+',
    tone: 'tone-warning'
  },
  {
    name: '数据结构',
    summary: '树与图基础稳定，建议继续加强图搜索与最短路径题型。',
    progress: 81,
    grade: 'A-',
    tone: 'tone-info'
  }
])

// Dimension chips
const dimensionChips = computed(() => [
  { label: '全部课程', value: 'all', color: '#007AFF', count: courseCards.value.length },
  ...courseCards.value.map(course => ({
    label: course.name,
    value: course.name,
    color: course.tone === 'tone-success' ? '#34C759' : course.tone === 'tone-warning' ? '#FF9500' : '#007AFF',
    count: course.progress + '%'
  }))
])

// Filtered courses
const filteredCourses = computed(() => {
  if (!searchQuery.value && selectedDimension.value === 'all') {
    return courseCards.value
  }
  
  return courseCards.value.filter(course => {
    const matchesSearch = !searchQuery.value || 
      course.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      course.summary.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesDimension = selectedDimension.value === 'all' || course.name === selectedDimension.value
    return matchesSearch && matchesDimension
  })
})

// Progress trend
const progressTrend = computed(() => {
  return evaluation.value.progress - 60 // mock previous value
})

// View label
const activeViewLabel = computed(() => viewModes.find(v => v.value === activeView.value)?.label ?? '概览')

// Actions
function onStartEvaluation() {
  alert('演示：开始新的学习评估流程')
}

function onExport() {
  alert('演示：导出评估报告为 PDF')
}

function onAction(action) {
  alert(`演示：执行动作 - ${action}`)
}

// Auto-select first course if none selected
if (courseCards.value.length > 0 && !selectedCourse.value) {
  selectedCourse.value = courseCards.value[0]
}

onMounted(async () => {
  try {
    const summaryRes = await evaluationApi.summary('default')
    const historyRes = await evaluationApi.history('default')
    evaluation.value = summarizeEvaluation(summaryRes?.data, historyRes?.data)
  } catch {
    evaluation.value = summarizeEvaluation()
  }
})
</script>

<style scoped>
/* Page wrapper */
.evaluation-page {
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

.chip-dot {
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

.grade-badge {
  color: #34C759 !important;
  font-size: 16px !important;
}

.trend-up { color: #34C759 !important; }
.trend-down { color: #FF3B30 !important; }

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

/* Metric Overview */
.metric-overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.overview-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.04);
  border-radius: 12px;
  color: var(--icon-color);
  flex-shrink: 0;
}

.overview-icon svg { width: 24px; height: 24px; }

.overview-content { flex: 1; }

.overview-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
}

.overview-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.overview-bar {
  width: 100%;
  height: 6px;
  background: rgba(0,0,0,0.06);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 8px;
}

.overview-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Course Grid */
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.course-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
  animation: fadeIn 0.3s ease backwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.course-card:hover {
  border-color: rgba(0,122,255,0.3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.course-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.course-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.course-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.course-grade {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 8px;
}

.tone-success { color: #34C759; background: rgba(52, 199, 89, 0.15); }
.tone-warning { color: #FF9500; background: rgba(255, 149, 0, 0.15); }
.tone-info { color: #007AFF; background: rgba(0, 122, 255, 0.15); }

.course-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
  flex: 1;
}

.course-progress { }

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.progress-info span { font-size: 11px; color: var(--text-tertiary); }
.progress-info strong { font-size: 12px; color: var(--text); }

.progress-bar {
  height: 4px;
  background: rgba(0,0,0,0.06);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Insights Section */
.insights-section {
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  padding: 16px;
  position: relative;
  z-index: 1;
}

.insights-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 14px;
}

.insights-header svg { width: 18px; height: 18px; color: var(--accent); }

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item {
  display: flex;
  gap: 12px;
}

.insight-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  flex-shrink: 0;
}

.insight-icon svg { width: 18px; height: 18px; }

.insight-icon.up {
  background: rgba(52, 199, 89, 0.15);
  color: #34C759;
}

.insight-icon.info {
  background: rgba(0, 122, 255, 0.15);
  color: #007AFF;
}

.insight-content h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.insight-content p {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
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
  margin-bottom: 8px;
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
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
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

.action-btn svg { width: 16px; height: 16px; }

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.history-item:last-child { border-bottom: none; }

.history-date {
  font-size: 10px;
  color: var(--text-tertiary);
}

.history-title {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-score {
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
}

.no-history {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 12px;
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
  .evaluation-page { padding: 12px; }
  .mac-window { width: 100%; }
  .inspector { width: 260px; }
  .sidebar { width: 190px; }
  .metric-overview { grid-template-columns: 1fr; }
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
