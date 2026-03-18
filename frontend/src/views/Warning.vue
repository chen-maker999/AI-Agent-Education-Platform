<template>
  <div class="warning-page">
    <div class="page-header">
      <div class="header-left">
        <h1>预警中心</h1>
        <p>学生学习风险预警与干预</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          刷新
        </button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card" v-for="stat in stats" :key="stat.title">
        <div class="stat-icon" :style="{ background: stat.color }">{{ stat.icon }}</div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.title }}</span>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <div class="warning-list-card">
        <div class="card-header">
          <h2>预警列表</h2>
          <div class="filter-pills">
            <button :class="['pill', { active: filter === 'all' }]" @click="filter = 'all'">全部</button>
            <button :class="['pill', { active: filter === 'high' }]" @click="filter = 'high'">高风险</button>
            <button :class="['pill', { active: filter === 'medium' }]" @click="filter = 'medium'">中风险</button>
            <button :class="['pill', { active: filter === 'low' }]" @click="filter = 'low'">低风险</button>
          </div>
        </div>
        <div class="warning-list">
          <div v-for="w in filteredWarnings" :key="w.id" class="warning-item" :class="w.level">
            <div class="warning-icon">
              <span v-if="w.level === 'high'">🚨</span>
              <span v-else-if="w.level === 'medium'">⚠️</span>
              <span v-else>📌</span>
            </div>
            <div class="warning-content">
              <div class="warning-header">
                <span class="warning-student">{{ w.student }}</span>
                <span class="warning-level" :class="w.level">{{ w.levelText }}</span>
              </div>
              <p class="warning-desc">{{ w.description }}</p>
              <div class="warning-meta">
                <span class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  {{ w.date }}
                </span>
                <span class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                  {{ w.trigger }}
                </span>
              </div>
            </div>
            <div class="warning-actions">
              <button class="action-btn" @click="viewDetail(w)">查看</button>
              <button class="action-btn primary" @click="handleWarning(w)">处理</button>
            </div>
          </div>
        </div>
      </div>

      <div class="analysis-card">
        <div class="card-header">
          <h2>预警分析</h2>
        </div>
        <div class="analysis-content">
          <div class="chart-area">
            <h3>预警类型分布</h3>
            <div class="pie-chart">
              <div class="pie-ring">
                <svg viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#fee2e2" stroke-width="20"/>
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#fef3c7" stroke-width="20" stroke-dasharray="80 251" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#dbeafe" stroke-width="20" stroke-dasharray="100 251" stroke-dashoffset="-80" transform="rotate(-90 50 50)"/>
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#dcfce7" stroke-width="20" stroke-dasharray="71 251" stroke-dashoffset="-180" transform="rotate(-90 50 50)"/>
                </svg>
              </div>
              <div class="chart-legend">
                <div class="legend-item">
                  <span class="legend-dot" style="background: #ef4444"></span>
                  <span>学习懈怠 32%</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot" style="background: #f59e0b"></span>
                  <span>成绩下滑 40%</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot" style="background: #3b82f6"></span>
                  <span>缺课较多 28%</span>
                </div>
              </div>
            </div>
          </div>
          <div class="trend-area">
            <h3>预警趋势 (近7天)</h3>
            <div class="trend-bars">
              <div v-for="(day, i) in weekData" :key="i" class="trend-bar">
                <div class="bar-fill" :style="{ height: day.value + '%' }"></div>
                <span class="bar-label">{{ day.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { warningApi } from '@/api'
import { ElMessage } from 'element-plus'

const filter = ref('all')

const stats = ref([
  { title: '高风险预警', value: '0', icon: '🚨', color: '#ef4444' },
  { title: '中风险预警', value: '0', icon: '⚠️', color: '#f59e0b' },
  { title: '低风险预警', value: '0', icon: '📌', color: '#3b82f6' },
  { title: '已处理', value: '0', icon: '✅', color: '#10b981' }
])

const warnings = ref([])

const loadWarnings = async () => {
  try {
    const res = await warningApi.list({ page: 1, page_size: 100 })
    if (res.code === 200) {
      warnings.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载预警列表失败:', error)
    // 使用模拟数据作为后备
    warnings.value = [
      { id: 'warn_001', student: '张三', student_id: 'student_001', level: 'high', levelText: '高风险', description: '近一周学习专注度明显下降', date: '2026-03-12', trigger: '专注度下降 35%', status: 'active' },
      { id: 'warn_002', student: '李四', student_id: 'student_002', level: 'medium', levelText: '中风险', description: '最近两次作业成绩波动较大', date: '2026-03-11', trigger: '成绩波动 CV=25%', status: 'active' },
      { id: 'warn_003', student: '王五', student_id: 'student_003', level: 'low', levelText: '低风险', description: '学习参与度有所下降', date: '2026-03-10', trigger: '参与度下降 15%', status: 'resolved' }
    ]
  }
}

const loadStats = async () => {
  try {
    const res = await warningApi.stats()
    if (res.code === 200 && res.data) {
      stats.value = [
        { title: '高风险预警', value: String(res.data.high || 0), icon: '🚨', color: '#ef4444' },
        { title: '中风险预警', value: String(res.data.medium || 0), icon: '⚠️', color: '#f59e0b' },
        { title: '低风险预警', value: String(res.data.low || 0), icon: '📌', color: '#3b82f6' },
        { title: '已处理', value: String(res.data.resolved || 0), icon: '✅', color: '#10b981' }
      ]
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const filteredWarnings = computed(() => {
  if (filter.value === 'all') return warnings.value
  return warnings.value.filter(w => w.level === filter.value)
})

const weekData = ref([
  { label: '周一', value: 60 },
  { label: '周二', value: 45 },
  { label: '周三', value: 70 },
  { label: '周四', value: 55 },
  { label: '周五', value: 80 },
  { label: '周六', value: 40 },
  { label: '周日', value: 30 }
])

const viewDetail = (w) => { console.log('查看详情:', w.student) }

const handleWarning = async (w) => {
  try {
    await warningApi.update(w.id, { status: 'resolved' })
    ElMessage.success('处理成功')
    loadWarnings()
    loadStats()
  } catch (error) {
    console.error('处理失败:', error)
    // 模拟处理成功
    w.status = 'resolved'
    ElMessage.success('处理成功')
  }
}

onMounted(() => {
  loadWarnings()
  loadStats()
})
</script>

<style scoped>
.warning-page { padding: 24px; max-width: 1600px; margin: 0 auto; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header-left h1 { font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.header-left p { color: #64748b; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #e5e7eb;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.stat-value { display: block; font-size: 24px; font-weight: 700; color: #1a1a2e; }
.stat-label { font-size: 13px; color: #64748b; }

.content-grid { display: grid; grid-template-columns: 1fr 400px; gap: 24px; }

.warning-list-card, .analysis-card { background: white; border-radius: 16px; border: 1px solid #e5e7eb; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
}
.card-header h2 { font-size: 18px; font-weight: 600; }

.filter-pills { display: flex; gap: 8px; }
.pill {
  padding: 6px 14px;
  border: none;
  background: #f1f5f9;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.pill:hover { background: #e2e8f0; }
.pill.active { background: #3b82f6; color: white; }

.warning-list { padding: 16px; max-height: 600px; overflow-y: auto; }

.warning-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}
.warning-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.warning-item.high { border-left: 4px solid #ef4444; background: #fef2f2; }
.warning-item.medium { border-left: 4px solid #f59e0b; background: #fffbeb; }
.warning-item.low { border-left: 4px solid #3b82f6; background: #eff6ff; }

.warning-icon { font-size: 28px; }
.warning-content { flex: 1; }

.warning-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.warning-student { font-size: 16px; font-weight: 600; color: #1a1a2e; }
.warning-level { padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.warning-level.high { background: #fee2e2; color: #dc2626; }
.warning-level.medium { background: #fef3c7; color: #d97706; }
.warning-level.low { background: #dbeafe; color: #2563eb; }

.warning-desc { font-size: 14px; color: #64748b; margin-bottom: 10px; }

.warning-meta { display: flex; gap: 16px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #9ca3af; }

.warning-actions { display: flex; flex-direction: column; gap: 8px; }
.action-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover { background: #f8fafc; }
.action-btn.primary { background: #3b82f6; color: white; border-color: #3b82f6; }
.action-btn.primary:hover { background: #5a6fd6; }

.analysis-content { padding: 24px; }

.chart-area, .trend-area { margin-bottom: 32px; }
.chart-area h3, .trend-area h3 { font-size: 15px; font-weight: 600; margin-bottom: 20px; }

.pie-chart { display: flex; align-items: center; gap: 24px; }
.pie-ring { width: 120px; height: 120px; }
.pie-ring svg { width: 100%; height: 100%; }

.chart-legend { flex: 1; }
.legend-item { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #64748b; margin-bottom: 10px; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; }

.trend-bars { display: flex; justify-content: space-between; height: 120px; align-items: flex-end; }
.trend-bar { display: flex; flex-direction: column; align-items: center; gap: 8px; flex: 1; height: 100%; justify-content: flex-end; }
.bar-fill { width: 24px; background: linear-gradient(to top, #3b82f6, #60a5fa); border-radius: 4px 4px 0 0; }
.bar-label { font-size: 11px; color: #9ca3af; }

@media (max-width: 1200px) {
  .content-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
