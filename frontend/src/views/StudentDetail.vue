<template>
  <div class="student-detail-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        返回
      </button>
      <h1>学生详情 - {{ studentId }}</h1>
    </div>
    <div class="detail-content">
      <p>学生详细信息页面</p>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const studentId = route.params.studentId
</script>

<style scoped>
.student-detail-page { padding: 24px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.back-btn { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; }
.back-btn:hover { background: #f8fafc; }
h1 { font-size: 24px; }
.detail-content { background: white; padding: 32px; border-radius: 16px; }
</style>
