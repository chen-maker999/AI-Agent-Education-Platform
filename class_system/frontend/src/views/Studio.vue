<template>
  <div class="workspace-page">
    <PageHero
      eyebrow="Admin Workspace"
      title="Agent Studio"
      description="为可视化 Agent 构建工具预留完整界面骨架，当前以只读方式展示能力结构和待接入状态。"
    />

    <div class="workspace-split">
      <PanelCard title="构建画布" subtitle="拖拽式 Agent 编排、节点参数和执行链路将在这里承载。">
        <div class="studio-canvas glass">
          <div class="studio-canvas__node">Orchestrator</div>
          <div class="studio-canvas__node">Tutor Agent</div>
          <div class="studio-canvas__node">Diagnostic Agent</div>
          <div class="studio-canvas__node">Grader Agent</div>
        </div>
      </PanelCard>

      <div class="workspace-stack">
        <PanelCard title="能力清单" subtitle="根据题目和计划书保留关键模块入口。">
          <div class="chip-list">
            <span class="chip">Orchestrator</span>
            <span class="chip">Tutor</span>
            <span class="chip">Diagnostic</span>
            <span class="chip">Grader</span>
            <span class="chip">Trace ID</span>
            <span class="chip">Rollback</span>
          </div>
        </PanelCard>

        <PanelCard title="后续接入" subtitle="优先对接节点配置、流程保存、运行调试和日志回看。">
          <div class="timeline-list">
            <div class="timeline-item">
              <h4>节点模板库</h4>
              <p>按课程和功能分类提供标准 Agent 模板。</p>
            </div>
            <div class="timeline-item">
              <h4>运行追踪</h4>
              <p>展示 Agent 协作链路、上下文结构与错误回滚。</p>
            </div>
          </div>
        </PanelCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import PageHero from '@/components/ui/PageHero.vue'
import PanelCard from '@/components/ui/PanelCard.vue'
</script>

<style scoped>
.studio-canvas {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  min-height: 360px;
  padding: 18px;
  border-radius: 24px;
}

.studio-canvas__node {
  display: grid;
  place-items: center;
  min-height: 120px;
  border-radius: 20px;
  border: 1px solid rgba(163, 203, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-weight: 700;
}
</style>
