<template>
  <div class="workspace-page">
    <PageHero
      eyebrow="Student Insight"
      :title="`${portrait.name} · 学生画像详情`"
      description="从预警、评估和画像联动到单个学生的干预动作。"
    />

    <div class="metric-grid">
      <MetricCard icon="chart" :value="`${portrait.mastery}%`" label="掌握度" tone="success" />
      <MetricCard icon="spark" :value="`${portrait.focus}%`" label="学习专注度" tone="info" />
      <MetricCard icon="alert" :value="portrait.risk" label="风险等级" tone="warning" />
      <MetricCard icon="file" value="3 条" label="待跟进事项" hint="预警 / 批注 / 练习" />
    </div>

    <div class="workspace-split">
      <div class="workspace-stack">
        <PanelCard title="学生画像" subtitle="补充教师需要的对比与干预说明。">
          <div class="workspace-grid columns-2">
            <div class="resource-item">
              <h4>优势</h4>
              <div class="chip-list">
                <span v-for="item in portrait.strengths" :key="item" class="chip">{{ item }}</span>
              </div>
            </div>
            <div class="resource-item">
              <h4>薄弱点</h4>
              <div class="chip-list">
                <span v-for="item in portrait.weaknesses" :key="item" class="chip">{{ item }}</span>
              </div>
            </div>
          </div>
        </PanelCard>

        <PanelCard title="班级对比与干预建议" subtitle="帮助教师快速决策下一步动作。">
          <div class="timeline-list">
            <div class="timeline-item">
              <h4>班级对比</h4>
              <p>当前掌握度低于班级平均值 8%，建议优先补齐算法复杂度与递推题型。</p>
            </div>
            <div class="timeline-item">
              <h4>干预建议</h4>
              <p>安排一次错题回看、推送 3 题增量练习，并跟踪下一次作业完成质量。</p>
            </div>
          </div>
        </PanelCard>
      </div>

      <div class="workspace-stack">
        <PanelCard title="近期记录" subtitle="串联画像、评估和预警。">
          <div class="timeline-list">
            <div v-for="item in portrait.progress" :key="item.label" class="timeline-item">
              <h4>{{ item.label }}</h4>
              <p>{{ item.value }}</p>
            </div>
          </div>
        </PanelCard>

        <PanelCard title="教师操作" subtitle="从详情页直接下发下一步动作。">
          <div class="chip-list">
            <router-link to="/warning" class="chip">回到预警中心</router-link>
            <router-link to="/evaluation" class="chip">查看评估概览</router-link>
            <router-link to="/chat" class="chip">发起课程问答</router-link>
            <span class="chip">发送练习建议</span>
          </div>
        </PanelCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { portraitApi } from '@/api'
import { summarizePortrait } from '@/utils/viewModels'
import MetricCard from '@/components/ui/MetricCard.vue'
import PageHero from '@/components/ui/PageHero.vue'
import PanelCard from '@/components/ui/PanelCard.vue'

const route = useRoute()
const portrait = ref(summarizePortrait())

onMounted(async () => {
  const studentId = route.params.studentId
  try {
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
    portrait.value = summarizePortrait({ name: `学生 ${studentId || ''}` })
  }
})
</script>
