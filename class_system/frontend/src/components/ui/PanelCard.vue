<template>
  <section class="panel-card" :class="[`tone-${tone}`, { compact }]">
    <div class="panel-card__beam"></div>
    <div class="panel-card__mesh"></div>

    <header v-if="title || $slots.header" class="panel-card__header">
      <div class="panel-card__heading">
        <p v-if="eyebrow" class="panel-card__eyebrow">{{ eyebrow }}</p>
        <h3 v-if="title" class="panel-card__title">{{ title }}</h3>
        <p v-if="subtitle" class="panel-card__subtitle">{{ subtitle }}</p>
      </div>

      <div v-if="$slots.headerAction" class="panel-card__action">
        <slot name="headerAction" />
      </div>
      <slot v-else name="header" />
    </header>

    <div class="panel-card__body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  eyebrow: {
    type: String,
    default: ''
  },
  tone: {
    type: String,
    default: 'default'
  },
  compact: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.panel-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(37, 99, 235, 0.14);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.90), rgba(248, 252, 255, 0.96)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.06), transparent 28%),
    radial-gradient(circle at left bottom, rgba(37, 99, 235, 0.04), transparent 22%);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(22px);
}

.panel-card::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.80);
  pointer-events: none;
}

.panel-card__beam,
.panel-card__mesh {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.panel-card__beam {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 28%),
    radial-gradient(circle at left bottom, rgba(37, 99, 235, 0.04), transparent 22%);
}

.panel-card__mesh {
  opacity: 0.12;
  background-image:
    linear-gradient(rgba(37, 99, 235, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.06) 1px, transparent 1px);
  background-size: 26px 26px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.3), transparent 100%);
}

.panel-card__header,
.panel-card__body {
  position: relative;
  z-index: 1;
}

.panel-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 26px 26px 0;
}

.panel-card__body {
  padding: 22px 26px 26px;
}

.panel-card.compact .panel-card__header {
  padding: 18px 18px 0;
}

.panel-card.compact .panel-card__body {
  padding: 16px 18px 18px;
}

.panel-card__eyebrow {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.panel-card__title {
  font-size: clamp(20px, 2vw, 28px);
  line-height: 1.06;
}

.panel-card__subtitle {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.75;
}

.tone-accent {
  border-color: rgba(37, 99, 235, 0.18);
  background:
    linear-gradient(180deg, rgba(240, 246, 255, 0.92), rgba(232, 244, 255, 0.98)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.10), transparent 28%),
    radial-gradient(circle at 12% 82%, rgba(6, 182, 212, 0.08), transparent 22%);
}

.tone-dark {
  background:
    linear-gradient(180deg, rgba(232, 238, 255, 0.94), rgba(224, 234, 255, 0.98)),
    radial-gradient(circle at 18% 20%, rgba(37, 99, 235, 0.08), transparent 18%);
}

/* Dark mode overrides */
[data-theme="dark"] .panel-card {
  border-color: var(--border-soft);
  background: var(--panel-bg);
}
[data-theme="dark"] .panel-card::after {
  border-color: rgba(255, 255, 255, 0.04);
}
[data-theme="dark"] .panel-card__mesh {
  opacity: 0.28;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.72), transparent 100%);
}
[data-theme="dark"] .tone-accent {
  border-color: rgba(163, 203, 255, 0.18);
  background:
    linear-gradient(180deg, rgba(14, 24, 42, 0.88), rgba(8, 14, 26, 0.94)),
    radial-gradient(circle at top right, rgba(79, 140, 255, 0.24), transparent 28%),
    radial-gradient(circle at 12% 82%, rgba(56, 215, 197, 0.16), transparent 22%);
}
[data-theme="dark"] .tone-dark {
  background:
    linear-gradient(180deg, rgba(9, 16, 28, 0.94), rgba(6, 10, 20, 0.98)),
    radial-gradient(circle at 18% 20%, rgba(79, 140, 255, 0.16), transparent 18%);
}
</style>
