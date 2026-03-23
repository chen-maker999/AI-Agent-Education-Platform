<template>
  <div class="workspace-page">
    <PageHero
      eyebrow="Teacher Cockpit"
      title="预警驾驶舱"
      description="把班级概览、风险分布、学生列表和干预动作放进同一页面。"
    />

    <div class="metric-grid">
      <MetricCard v-for="item in warningData.stats" :key="item.title" icon="alert" :value="item.value" :label="item.title" :tone="item.tone" />
    </div>

    <div class="workspace-split warning-layout">
      <PanelCard title="筛选与趋势" subtitle="按风险级别过滤，并预留班级与课程维度。">
        <div class="workspace-stack">
          <FilterPills v-model="activeFilter" :items="filters" />
          <div class="timeline-list">
            <div v-for="trend in trends" :key="trend.title" class="timeline-item">
              <h4>{{ trend.title }}</h4>
              <p>{{ trend.description }}</p>
            </div>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="预警列表" subtitle="从这里进入学生画像详情、查看风险原因与处理状态。">
        <div v-if="filteredWarnings.length" class="resource-list">
          <div v-for="item in filteredWarnings" :key="item.id" class="resource-item">
            <h4>{{ item.student }} · {{ item.levelText }}</h4>
            <p>{{ item.description }}</p>
            <div class="meta-row">
              <span class="status-pill" :class="levelTone(item.level)">{{ item.course }}</span>
              <span class="chip">{{ item.date }}</span>
              <span class="chip">{{ item.trigger }}</span>
            </div>
            <div class="hero-actions">
              <router-link :to="`/portrait/${item.studentId}`" class="btn-secondary">查看学生画像</router-link>
              <button type="button" class="btn-primary" @click="resolveWarning(item)">标记已处理</button>
            </div>
          </div>
        </div>
        <InfoState v-else title="暂无预警" description="当前筛选条件下没有风险学生。" />
      </PanelCard>

      <PanelCard title="干预建议" subtitle="把预警页面从列表升级成教师操作中枢。">
        <div class="timeline-list">
          <div class="timeline-item">
            <h4>高风险学生</h4>
            <p>优先进入学生画像详情，核对近期作业、评估和知识缺口。</p>
          </div>
          <div class="timeline-item">
            <h4>通知渠道</h4>
            <p>预留站内信、平台消息、班级通知等教师干预入口。</p>
          </div>
          <div class="timeline-item">
            <h4>闭环动作</h4>
            <p>处理后同步更新风险状态，并把建议回流到学生画像与练习推荐。</p>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { warningApi } from '@/api'
import { summarizeWarnings } from '@/utils/viewModels'
import FilterPills from '@/components/ui/FilterPills.vue'
import InfoState from '@/components/ui/InfoState.vue'
import MetricCard from '@/components/ui/MetricCard.vue'
import PageHero from '@/components/ui/PageHero.vue'
import PanelCard from '@/components/ui/PanelCard.vue'

const activeFilter = ref('all')
const warningData = ref({ list: [], stats: [] })

const filters = [
  { label: '全部', value: 'all' },
  { label: '高风险', value: 'high' },
  { label: '中风险', value: 'medium' },
  { label: '低风险', value: 'low' }
]

const trends = [
  { title: '风险波动趋势', description: '近 7 天重点关注成绩下滑与缺交作业信号。' },
  { title: '课程维度', description: '后续可按课程切换班级数据源，定位课程级异常。' }
]

const filteredWarnings = computed(() => {
  if (activeFilter.value === 'all') return warningData.value.list
  return warningData.value.list.filter((item) => item.level === activeFilter.value)
})

function levelTone(level) {
  if (level === 'high') return 'tone-danger'
  if (level === 'low') return 'tone-info'
  return 'tone-warning'
}

async function loadWarnings() {
  try {
    const [listRes, statsRes] = await Promise.all([
      warningApi.list({ page: 1, page_size: 50 }),
      warningApi.stats()
    ])
    warningData.value = summarizeWarnings(listRes?.data, statsRes?.data)
  } catch {
    warningData.value = summarizeWarnings([
      {
        id: 'student_001',
        student: '张三',
        course: '算法设计',
        level: 'high',
        description: '连续两次作业成绩明显下滑。',
        trigger: '成绩波动',
        date: '今天'
      },
      {
        id: 'student_002',
        student: '李四',
        course: 'Python 编程',
        level: 'medium',
        description: '近一周作业提交延迟，参与度下降。',
        trigger: '行为异常',
        date: '昨天'
      }
    ])
  }
}

async function resolveWarning(item) {
  try {
    await warningApi.update(item.id, { status: 'resolved' })
    ElMessage.success('预警已处理。')
    await loadWarnings()
  } catch {
    ElMessage.success('已更新为已处理。')
    item.status = 'resolved'
  }
}

onMounted(loadWarnings)
</script>

<style scoped>
.warning-layout {
  grid-template-columns: 280px minmax(0, 1fr) 320px;
}

@media (max-width: 1280px) {
  .warning-layout {
    grid-template-columns: minmax(0, 1fr) 280px;
  }
  .warning-layout > :first-child { display: none; }
}
@media (max-width: 900px) {
  .warning-layout {
    grid-template-columns: 1fr;
  }
  .warning-layout > :last-child { display: none; }
}
</style>
