<template>
  <div class="agent-call-card" :class="{ 'is-expanded': expanded }">
    <!-- 折叠头：始终可见 -->
    <div class="agent-call-card__header" @click="toggle">
      <div class="agent-call-card__icon-wrap">
        <!-- Running: spinner -->
        <svg v-if="status === 'running'" class="spin" width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5" stroke-dasharray="22" stroke-dashoffset="7"/>
        </svg>
        <!-- Done / Error -->
        <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
          <path v-if="status === 'done'" d="M4 6.5l2 2 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path v-else d="M4.5 4.5l4 4M8.5 4.5l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>

      <div class="agent-call-card__title-wrap">
        <span class="agent-call-card__label">
          <svg width="11" height="11" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <circle cx="6.5" cy="4.5" r="2.5" stroke="currentColor" stroke-width="1.2"/>
            <path d="M1.5 11c0-2.21 2.239-4 5-4s5 1.79 5 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            <circle cx="10.5" cy="3.5" r="1.5" fill="currentColor" opacity="0.7"/>
          </svg>
          {{ title }}
        </span>
        <span class="agent-call-card__status-text" :class="`status-${status}`">{{ statusText }}</span>
      </div>

      <div class="agent-call-card__chevron" :class="{ open: expanded }">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 3.5l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <!-- 展开详情 -->
    <transition name="agent-card-expand">
      <div v-if="expanded" class="agent-call-card__body">
        <!-- 输入参数 -->
        <div v-if="args && Object.keys(args).length > 0" class="agent-call-card__section">
          <div class="agent-call-card__section-label">输入参数</div>
          <div class="agent-call-card__code-block">
            <pre>{{ formatArgs(args) }}</pre>
          </div>
        </div>

        <!-- 执行结果 -->
        <div v-if="result !== undefined" class="agent-call-card__section">
          <div class="agent-call-card__section-label">执行结果</div>
          <div v-if="resultError" class="agent-call-card__error">
            <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M6 2v5M6 9v1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            {{ resultError }}
          </div>
          <div v-else class="agent-call-card__result">
            <pre>{{ formatResult(result) }}</pre>
          </div>
        </div>

        <!-- 子步骤列表 -->
        <div v-if="steps && steps.length > 0" class="agent-call-card__section">
          <div class="agent-call-card__section-label">执行步骤 ({{ steps.length }})</div>
          <div class="agent-call-card__steps">
            <div
              v-for="(step, i) in steps"
              :key="i"
              class="agent-call-card__step"
            >
              <div class="agent-call-card__step-dot" :class="`dot-${step.status || 'pending'}`"></div>
              <div class="agent-call-card__step-content">
                <span class="agent-call-card__step-name">{{ step.name || step.tool || step.task_id || `步骤 ${i + 1}` }}</span>
                <span class="agent-call-card__step-badge">{{ step.status === 'done' ? '完成' : step.status === 'error' ? '失败' : '进行中' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '子代理' },
  status: { type: String, default: 'pending' }, // pending | running | done | error
  args: { type: Object, default: () => ({}) },
  result: { type: [Object, String], default: undefined },
  steps: { type: Array, default: () => [] }
})

const expanded = ref(false)

function toggle() {
  expanded.value = !expanded.value
}

const statusText = computed(() => {
  switch (props.status) {
    case 'running': return '执行中...'
    case 'done': return '已完成'
    case 'error': return '执行失败'
    default: return '等待中'
  }
})

const resultError = computed(() => {
  if (!props.result) return null
  if (typeof props.result === 'object' && props.result.error) return props.result.error
  return null
})

function formatArgs(args) {
  if (!args) return ''
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

function formatResult(result) {
  if (!result) return '(空)'
  if (typeof result === 'string') return result
  try {
    return JSON.stringify(result, null, 2)
  } catch {
    return String(result)
  }
}
</script>

<style scoped>
/* ── 卡片容器：灰色边框，始终统一色调 ── */
.agent-call-card {
  margin: 6px 0;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.03);
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  font-family: inherit;
}

.agent-call-card:hover {
  border-color: rgba(255, 255, 255, 0.22);
}

.agent-call-card.is-expanded {
  border-color: rgba(255, 255, 255, 0.2);
}

/* ── Header ── */
.agent-call-card__header {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 13px;
  cursor: pointer;
  user-select: none;
}

.agent-call-card__icon-wrap {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #6b7280;
}

.agent-call-card__title-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.agent-call-card__label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
}

.agent-call-card__status-text {
  font-size: 11px;
  color: #9ca3af;
}

.agent-call-card__status-text.status-running {
  color: #60a5fa;
}

.agent-call-card__status-text.status-done {
  color: #6b7280;
}

.agent-call-card__status-text.status-error {
  color: #f87171;
}

.agent-call-card__status-text.status-pending {
  color: #9ca3af;
}

.agent-call-card__chevron {
  color: #6b7280;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.agent-call-card__chevron.open {
  transform: rotate(180deg);
}

/* ── Body ── */
.agent-call-card__body {
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding: 10px 13px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-call-card__section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #9ca3af;
  margin-bottom: 5px;
}

.agent-call-card__code-block {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 7px;
  padding: 9px 11px;
  overflow-x: auto;
  max-height: 160px;
  overflow-y: auto;
}

.agent-call-card__code-block pre {
  margin: 0;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.55;
  color: rgba(165, 243, 252, 0.8);
  white-space: pre-wrap;
  word-break: break-all;
}

.agent-call-card__result {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 7px;
  padding: 9px 11px;
  max-height: 200px;
  overflow-y: auto;
}

.agent-call-card__result pre {
  margin: 0;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.55;
  color: rgba(165, 243, 252, 0.75);
  white-space: pre-wrap;
  word-break: break-all;
}

.agent-call-card__error {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  padding: 7px 9px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 7px;
  font-size: 12px;
  color: #fca5a5;
  line-height: 1.5;
}

/* ── Steps ── */
.agent-call-card__steps {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.agent-call-card__step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 9px;
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.12);
}

.agent-call-card__step-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.agent-call-card__step-dot.dot-done {
  background: rgba(255, 255, 255, 0.5);
}

.agent-call-card__step-dot.dot-error {
  background: rgba(239, 68, 68, 0.6);
}

.agent-call-card__step-dot.dot-running {
  background: rgba(255, 255, 255, 0.4);
  animation: pulse-step 1s ease-in-out infinite;
}

.agent-call-card__step-dot.dot-pending {
  background: rgba(255, 255, 255, 0.2);
}

.agent-call-card__step-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.agent-call-card__step-name {
  color: rgba(255, 255, 255, 0.6);
  font-family: 'Fira Code', monospace;
}

.agent-call-card__step-badge {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.3);
}

/* ── Animations ── */
.agent-card-expand-enter-active,
.agent-card-expand-leave-active {
  transition: max-height 0.22s ease, opacity 0.18s ease;
  overflow: hidden;
  max-height: 500px;
}

.agent-card-expand-enter-from,
.agent-card-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

@keyframes pulse-step {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
