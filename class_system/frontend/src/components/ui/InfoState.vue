<template>
  <div class="info-state" :class="`state-${type}`">
    <div class="info-state__icon">
      <AppIcon :name="iconName" :size="20" />
    </div>
    <div class="info-state__content">
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  type: {
    type: String,
    default: 'empty'
  },
  title: {
    type: String,
    default: '暂无内容'
  },
  description: {
    type: String,
    default: '当前还没有可以展示的数据。'
  }
})

const iconName = computed(() => {
  if (props.type === 'loading') return 'spark'
  if (props.type === 'error') return 'alert'
  if (props.type === 'locked') return 'settings'
  return 'database'
})
</script>

<style scoped>
.info-state {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: var(--radius-xl);
  border: 1px solid rgba(37,99,235,0.14);
  background: rgba(255,255,255,0.90);
  box-shadow: var(--shadow-xs);
}

.info-state__icon {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: var(--brand-500);
  background: rgba(37,99,235,0.08);
}

.info-state__content h3 {
  margin-bottom: 8px;
  font-size: 16px;
}

.info-state__content p {
  color: var(--text-secondary);
  line-height: 1.7;
}

.state-error .info-state__icon {
  color: var(--red-500);
  background: rgba(244,63,94,0.08);
}

.state-locked .info-state__icon {
  color: var(--amber-500);
  background: rgba(245,158,11,0.08);
}
</style>
