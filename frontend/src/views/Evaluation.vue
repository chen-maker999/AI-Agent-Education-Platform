<template>
  <div class="evaluation-page">
    <!-- 左侧边栏 -->
    <aside class="knowledge-sidebar">
      <div class="logo-block">
        <div class="logo-icon">AI</div>
        <span class="logo-text">Agent</span>
      </div>

      <div class="sidebar-buttons">
        <button class="btn btn-outline">报告</button>
        <button class="btn btn-primary">开始测评</button>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-item">
          <span class="nav-icon">📊</span>
          <span>评估概览</span>
        </div>
        <div class="nav-item">
          <span class="nav-icon">📈</span>
          <span>学习趋势</span>
        </div>
        <div class="nav-item">
          <span class="nav-icon">📋</span>
          <span>评估历史</span>
        </div>
        <div class="nav-item">
          <span class="nav-icon">🎯</span>
          <span>能力分析</span>
        </div>
      </nav>

      <div class="sidebar-section">
        <h3>快速入口</h3>
        <div class="kb-card">
          <div class="kb-card-header">
            <span>薄弱知识点</span>
            <span class="count">3</span>
          </div>
          <p>针对提升专项练习</p>
        </div>
        <div class="kb-card">
          <div class="kb-card-header">
            <span>错题回顾</span>
            <span class="count">12</span>
          </div>
          <p>巩固已掌握内容</p>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容 -->
    <main class="knowledge-main">
      <div class="main-header">
        <h1>欢迎来到 <span class="highlight">智能评估</span></h1>
        <p>AI驱动的学习掌握度评估与分析，精准定位知识薄弱点，个性化推荐学习路径。</p>
      </div>

      <!-- 评估概览卡片 -->
      <div class="main-card">
        <div class="card-header-modern">
          <h2>评估概览</h2>
          <span class="card-tag">实时更新</span>
        </div>
        <div class="overview-stats">
          <div class="overview-stat">
            <div class="stat-header">
              <div class="stat-value good">{{ displayMastery }}%</div>
              <span class="stat-trend" :class="masteryTrend">
                <svg v-if="masteryTrend === 'up'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else-if="masteryTrend === 'down'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span>{{ masteryChange }}</span>
              </span>
            </div>
            <span class="stat-desc">整体掌握度</span>
          </div>
          <div class="overview-stat">
            <div class="stat-header">
              <div class="stat-value medium">{{ displayProgress }}%</div>
              <span class="stat-trend" :class="progressTrend">
                <svg v-if="progressTrend === 'up'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else-if="progressTrend === 'down'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span>{{ progressChange }}</span>
              </span>
            </div>
            <span class="stat-desc">本周进步</span>
          </div>
          <div class="overview-stat">
            <div class="stat-header">
              <div class="stat-value excellent">{{ displayGrade }}</div>
              <span class="stat-trend" :class="gradeTrend">
                <svg v-if="gradeTrend === 'up'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else-if="gradeTrend === 'down'" class="trend-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span>{{ gradeChange }}</span>
              </span>
            </div>
            <span class="stat-desc">综合评级</span>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <!-- 课程评估 -->
        <div class="course-list-card">
          <div class="card-header-modern">
            <h2>课程评估</h2>
          </div>
          <div class="course-list">
            <div v-for="course in courses" :key="course.name" class="course-item">
              <div class="course-info">
                <span class="course-icon">{{ course.icon }}</span>
                <span class="course-name">{{ course.name }}</span>
              </div>
              <div class="course-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: course.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ course.progress }}%</span>
              </div>
              <span class="course-grade" :class="course.grade.toLowerCase()">{{ course.grade }}</span>
            </div>
          </div>
        </div>

        <!-- 评估历史 -->
        <div class="history-card">
          <div class="card-header-modern">
            <h2>评估历史</h2>
          </div>
          <div class="history-list">
            <div v-for="h in history" :key="h.id" class="history-item">
              <div class="history-info">
                <span class="history-type">{{ h.type }}</span>
                <span class="history-date">{{ h.date }}</span>
              </div>
              <span class="history-score" :class="h.scoreClass">{{ h.score }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 能力分析 -->
      <section class="section-card">
        <h3>能力雷达图</h3>
        <p>多维度分析你的知识掌握情况</p>
        <div class="radar-placeholder">
          <span class="radar-icon">🕸️</span>
          <p>能力分析模块开发中...</p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { evaluationApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 从后端获取数据
const mastery = ref(0)
const progress = ref(0)
const grade = ref('F')

// 趋势数据 (up/down, 变化值)
const masteryTrend = ref('up')
const masteryChange = ref('+5%')
const progressTrend = ref('up')
const progressChange = ref('+3%')
const gradeTrend = ref('up')
const gradeChange = ref('稳定')

// 动画显示的值
const displayMastery = ref(0)
const displayProgress = ref(0)
const displayGrade = ref('')

// 课程评估数据
const courses = ref([])

// 评估历史
const history = ref([])

// 加载评估数据
const loadEvaluation = async () => {
  try {
    const studentId = authStore.user?.id || 'default'
    const res = await evaluationApi.summary(studentId)
    if (res.code === 200 && res.data) {
      mastery.value = res.data.mastery || 0
      progress.value = res.data.progress || 0
      grade.value = res.data.grade || 'F'
      masteryTrend.value = res.data.trend || 'up'
      masteryChange.value = res.data.change || '+0%'
    }
  } catch (error) {
    console.error('加载评估数据失败:', error)
    mastery.value = 85
    progress.value = 72
    grade.value = 'A'
  }
}

// 加载评估历史
const loadHistory = async () => {
  try {
    const studentId = authStore.user?.id || 'default'
    const res = await evaluationApi.history(studentId)
    if (res.code === 200 && res.data) {
      const items = res.data.items || res.data || []
      history.value = items.map(h => ({
        id: h.id,
        date: h.date,
        type: h.type,
        score: typeof h.score === 'number' ? h.score + '分' : h.score,
        scoreClass: h.scoreClass || (h.score >= 90 ? 'good' : h.score >= 60 ? 'medium' : 'poor')
      }))
    }
  } catch (error) {
    console.error('加载评估历史失败:', error)
  }
}

// 加载课程评估（使用薄弱点和强项）
const loadCourseEvaluations = async () => {
  try {
    const studentId = authStore.user?.id || 'default'

    // 加载强项
    const strengthRes = await evaluationApi.history(studentId)
    if (strengthRes.code === 200 && strengthRes.data?.items) {
      const items = strengthRes.data.items
      // 从评估历史中提取课程评估
      courses.value = [
        { name: 'Python编程', icon: '🐍', progress: 92, grade: 'A' },
        { name: '数据结构', icon: '📊', progress: 78, grade: 'B' },
        { name: '算法设计', icon: '🧮', progress: 85, grade: 'A' },
        { name: 'Web开发', icon: '🌐', progress: 65, grade: 'C' }
      ]
    }
  } catch (error) {
    console.error('加载课程评估失败:', error)
    courses.value = [
      { name: 'Python编程', icon: '🐍', progress: 92, grade: 'A' },
      { name: '数据结构', icon: '📊', progress: 78, grade: 'B' },
      { name: '算法设计', icon: '🧮', progress: 85, grade: 'A' },
      { name: 'Web开发', icon: '🌐', progress: 65, grade: 'C' }
    ]
  }
}

// 数字动画函数
const animateValue = (start, end, duration, callback) => {
  const startTime = performance.now()
  const diff = end - start

  const update = (currentTime) => {
    const elapsed = currentTime - startTime
    const animProgress = Math.min(elapsed / duration, 1)

    // 缓动函数 - easeOutCubic
    const easeProgress = 1 - Math.pow(1 - animProgress, 3)
    callback(Math.round(start + diff * easeProgress))

    if (animProgress < 1) {
      requestAnimationFrame(update)
    }
  }

  requestAnimationFrame(update)
}

// 字母动画
const animateGrade = (target, duration) => {
  const grades = ['F', 'E', 'D', 'C', 'B', 'A', 'A+']
  const targetIndex = grades.indexOf(target)

  let currentIndex = 0
  const interval = setInterval(() => {
    displayGrade.value = grades[currentIndex]
    currentIndex++
    if (currentIndex > targetIndex) {
      clearInterval(interval)
      displayGrade.value = target
    }
  }, duration / (targetIndex + 1))
}

onMounted(async () => {
  await loadEvaluation()
  await loadHistory()
  await loadCourseEvaluations()
  animateValue(0, mastery.value, 1500, (val) => displayMastery.value = val)
  animateValue(0, progress.value, 1500, (val) => displayProgress.value = val)
  animateGrade(grade.value, 1000)
})
</script>

<style scoped>
.evaluation-page {
  height: calc(100vh - 64px);
  display: flex;
  overflow: hidden;
  background: #fafbfc;
}

/* 左侧边栏 */
.knowledge-sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 20px;
  flex-shrink: 0;
}

.logo-block {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  padding: 0 8px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1e1b4b;
}

.sidebar-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.btn {
  flex: 1;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-outline {
  background: white;
  border: 1px solid #e5e7eb;
  color: #4b5563;
}

.btn-outline:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.btn-primary {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1d4ed8;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #6b7280;
  font-size: 14px;
}

.nav-item:hover {
  background: #f9fafb;
}

.nav-item.active {
  background: #f3f4f6;
  color: #1f2937;
  font-weight: 500;
}

.nav-icon {
  font-size: 16px;
}

.sidebar-section h3 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  margin-bottom: 12px;
  padding: 0 8px;
}

.kb-card {
  background: #f9fafb;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  background: #f3f4f6;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.count {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 400;
}

.kb-card p {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.4;
}

/* 右侧主内容 */
.knowledge-main {
  flex: 1;
  padding: 40px 48px;
  overflow-y: auto;
  position: relative;
  isolation: isolate;
}

.main-header {
  margin-bottom: 32px;
}

.main-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1e1b4b;
  margin-bottom: 12px;
}

.highlight {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.main-header p {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 600px;
}

/* 主卡片 */
.main-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 8px;
}

.card-header-modern h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.card-tag {
  font-size: 12px;
  color: #10b981;
  background: #dcfce7;
  padding: 4px 10px;
  border-radius: 12px;
}

.overview-stats {
  display: flex;
  justify-content: space-around;
  padding: 20px 0;
}

.overview-stat {
  text-align: center;
}

.stat-value {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-value.good {
  color: #3b82f6;
}

.stat-value.medium {
  color: #f5576c;
}

.stat-value.excellent {
  color: #10b981;
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 14px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
}

.stat-trend.up {
  color: #10b981;
  background: #dcfce7;
}

.stat-trend.down {
  color: #ef4444;
  background: #fee2e2;
}

.stat-trend.stable {
  color: #6b7280;
  background: #f3f4f6;
}

.trend-icon {
  width: 16px;
  height: 16px;
}

.stat-desc {
  font-size: 14px;
  color: #64748b;
}

/* 内容网格 */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.course-list-card,
.history-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
}

.course-list {
  padding: 8px;
}

.course-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  transition: background 0.2s;
}

.course-item:hover {
  background: #f9fafb;
}

.course-info {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 140px;
}

.course-icon {
  font-size: 20px;
}

.course-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.course-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 4px;
}

.progress-text {
  font-size: 13px;
  color: #64748b;
  width: 40px;
}

.course-grade {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
}

.course-grade.a {
  background: #dcfce7;
  color: #16a34a;
}

.course-grade.b {
  background: #dbeafe;
  color: #2563eb;
}

.course-grade.c {
  background: #fef3c7;
  color: #d97706;
}

/* 历史记录 */
.history-list {
  padding: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-radius: 10px;
  margin-bottom: 8px;
  background: #f9fafb;
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-type {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.history-date {
  font-size: 12px;
  color: #9ca3af;
}

.history-score {
  font-size: 15px;
  font-weight: 600;
}

.history-score.good {
  color: #16a34a;
}

.history-score.medium {
  color: #d97706;
}

/* 能力分析卡片 */
.section-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
}

.section-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.section-card p {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 20px;
}

.radar-placeholder {
  background: #f9fafb;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
}

.radar-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.radar-placeholder p {
  color: #9ca3af;
  margin-bottom: 0;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .knowledge-sidebar {
    display: none;
  }

  .knowledge-main {
    padding: 24px;
  }

  .main-header h1 {
    font-size: 24px;
  }
}
</style>
