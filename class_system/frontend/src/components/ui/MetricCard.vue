<template>
  <article class="metric-card" :class="`tone-${tone}`">
    <div class="metric-card__icon">
      <AppIcon :name="icon" :size="18" />
    </div>

    <div class="metric-card__content">
      <span class="metric-card__label">{{ label }}</span>
      <strong class="metric-card__value">{{ value }}</strong>
      <span v-if="hint" class="metric-card__hint">{{ hint }}</span>
    </div>
  </article>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  icon: {
    type: String,
    default: 'spark'
  },
  value: {
    type: [String, Number],
    default: '-'
  },
  label: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  tone: {
    type: String,
    default: 'default'
  }
})
</script>

<style scoped>
.metric-card {
  position: relative;
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  min-height: 136px;
  padding: 20px;
  overflow: hidden;
  border-radius: 26px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 252, 255, 0.98)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 30%);
  box-shadow: var(--shadow-soft);
}

.metric-card::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.80);
  pointer-events: none;
}

.metric-card__icon,
.metric-card__content {
  position: relative;
  z-index: 1;
}

.metric-card__icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border-radius: 20px;
  color: var(--brand-500);
  background:
    linear-gradient(145deg, rgba(37, 99, 235, 0.12), rgba(37, 99, 235, 0.04)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.80), transparent);
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.metric-card__content {
  display: grid;
  gap: 5px;
}

.metric-card__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.metric-card__value {
  font-size: clamp(28px, 2.8vw, 40px);
  line-height: 1;
}

.metric-card__hint {
  color: var(--text-secondary);
  line-height: 1.6;
}

.tone-success {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(240, 255, 248, 0.98)),
    radial-gradient(circle at top right, rgba(16, 185, 129, 0.10), transparent 30%);
}

.tone-success .metric-card__icon {
  color: var(--emerald-500);
  background: linear-gradient(145deg, rgba(16, 185, 129, 0.14), rgba(16, 185, 129, 0.04));
}

.tone-warning {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 252, 240, 0.98)),
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.10), transparent 30%);
}

.tone-warning .metric-card__icon {
  color: var(--amber-500);
  background: linear-gradient(145deg, rgba(245, 158, 11, 0.14), rgba(245, 158, 11, 0.04));
}

.tone-danger {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 240, 244, 0.98)),
    radial-gradient(circle at top right, rgba(244, 63, 94, 0.10), transparent 30%);
}

.tone-danger .metric-card__icon {
  color: var(--rose-500);
  background: linear-gradient(145deg, rgba(244, 63, 94, 0.14), rgba(244, 63, 94, 0.04));
}

.tone-info {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(240, 248, 255, 0.98)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 30%);
}

.tone-info .metric-card__icon {
  color: var(--cyan-500);
  background: linear-gradient(145deg, rgba(6, 182, 212, 0.12), rgba(6, 182, 212, 0.04));
}

/* Dark mode overrides */
[data-theme="dark"] .metric-card {
  border-color: rgba(163, 203, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(12, 20, 34, 0.76), rgba(8, 14, 26, 0.9)),
    radial-gradient(circle at top right, rgba(79, 140, 255, 0.14), transparent 30%);
}
[data-theme="dark"] .metric-card::after {
  border-color: rgba(255, 255, 255, 0.04);
}
[data-theme="dark"] .metric-card__icon {
  color: var(--brand-300);
  background:
    linear-gradient(145deg, rgba(79, 140, 255, 0.22), rgba(79, 140, 255, 0.04)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent);
  border-color: rgba(163, 203, 255, 0.14);
}
[data-theme="dark"] .tone-success {
  background:
    linear-gradient(180deg, rgba(12, 20, 34, 0.76), rgba(8, 14, 26, 0.9)),
    radial-gradient(circle at top right, rgba(25, 192, 142, 0.18), transparent 30%);
}
[data-theme="dark"] .tone-success .metric-card__icon {
  color: var(--emerald-300);
  background: linear-gradient(145deg, rgba(25, 192, 142, 0.22), rgba(25, 192, 142, 0.04));
}
[data-theme="dark"] .tone-warning {
  background:
    linear-gradient(180deg, rgba(12, 20, 34, 0.76), rgba(8, 14, 26, 0.9)),
    radial-gradient(circle at top right, rgba(231, 154, 44, 0.18), transparent 30%);
}
[data-theme="dark"] .tone-warning .metric-card__icon {
  color: var(--amber-300);
  background: linear-gradient(145deg, rgba(231, 154, 44, 0.22), rgba(231, 154, 44, 0.04));
}
[data-theme="dark"] .tone-danger {
  background:
    linear-gradient(180deg, rgba(12, 20, 34, 0.76), rgba(8, 14, 26, 0.9)),
    radial-gradient(circle at top right, rgba(240, 124, 156, 0.18), transparent 30%);
}
[data-theme="dark"] .tone-danger .metric-card__icon {
  color: var(--rose-400);
  background: linear-gradient(145deg, rgba(240, 124, 156, 0.22), rgba(240, 124, 156, 0.04));
}
</style>
