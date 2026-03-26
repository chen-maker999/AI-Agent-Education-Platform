<template>
  <div class="workspace-page">
    <PageHero
      eyebrow="Admin Workspace"
      title="平台接入"
      description="统一管理超星、钉钉等主流教学平台的嵌入能力、适配状态和接入规范。"
    />

    <div class="workspace-grid columns-2">
      <PanelCard title="平台适配状态" subtitle="当前提供接入外壳与状态占位，待平台 API 接入后展示实时数据。">
        <div class="resource-list">
          <div class="resource-item">
            <h4>超星学习通</h4>
            <p>支持课程嵌入、统一身份认证、作业与学情数据同步。</p>
            <div class="meta-row">
              <span class="status-pill tone-warning">待接入</span>
            </div>
          </div>
          <div class="resource-item">
            <h4>钉钉</h4>
            <p>支持工作台入口、机器人通知、组织架构同步与课堂消息触达。</p>
            <div class="meta-row">
              <span class="status-pill tone-warning">待接入</span>
            </div>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="标准化接口" subtitle="保留接入指南、回调配置、密钥管理和可嵌入组件状态。">
        <div class="timeline-list">
          <div class="timeline-item">
            <h4>身份与权限</h4>
            <p>统一定义登录态映射、角色映射和嵌入上下文。</p>
          </div>
          <div class="timeline-item">
            <h4>组件嵌入</h4>
            <p>支持搜索入口、问答组件、图谱组件和作业批注组件单独嵌入。</p>
          </div>
          <div class="timeline-item">
            <h4>回调与监控</h4>
            <p>对接平台回调、调用日志、版本管理和健康状态监控。</p>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup>
import PageHero from '@/components/ui/PageHero.vue'
import PanelCard from '@/components/ui/PanelCard.vue'
</script>
