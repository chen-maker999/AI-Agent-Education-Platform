<template>
  <section class="page-hero">
    <div class="page-hero__noise"></div>
    <svg class="page-hero__orbit" viewBox="0 0 420 180" aria-hidden="true">
      <circle cx="350" cy="76" r="56" class="orbit orbit-a" />
      <circle cx="312" cy="112" r="84" class="orbit orbit-b" />
      <circle cx="372" cy="122" r="8" class="dot dot-a" />
      <circle cx="254" cy="72" r="5" class="dot dot-b" />
    </svg>

    <div class="page-hero__content">
      <p v-if="eyebrow" class="page-hero__eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
    </div>

    <div v-if="$slots.actions" class="page-hero__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.page-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: end;
  padding: clamp(24px, 3vw, 34px);
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(37, 99, 235, 0.18);
  background:
    linear-gradient(180deg, rgba(240, 246, 255, 0.92), rgba(232, 244, 255, 0.98)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.10), transparent 28%),
    radial-gradient(circle at 22% 92%, rgba(6, 182, 212, 0.06), transparent 18%);
  box-shadow: var(--shadow-soft);
}

.page-hero::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.80);
  pointer-events: none;
}

.page-hero__noise,
.page-hero__orbit {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.page-hero__noise {
  opacity: 0.08;
  background-image:
    linear-gradient(rgba(37, 99, 235, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.04) 1px, transparent 1px);
  background-size: 30px 30px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.3), transparent 100%);
}

.page-hero__orbit {
  width: 100%;
  height: 100%;
}

.orbit {
  fill: none;
  stroke: rgba(37, 99, 235, 0.12);
  stroke-width: 1.1;
  transform-origin: center;
}

.orbit-a {
  stroke-dasharray: 10 14;
  animation: orbitSpinA 14s linear infinite;
}

.orbit-b {
  stroke-dasharray: 4 12;
  animation: orbitSpinB 18s linear infinite;
}

.dot {
  fill: rgba(37, 99, 235, 0.6);
}

.dot-a {
  animation: pulse 2.8s ease-in-out infinite;
}

.dot-b {
  animation: pulse 4.2s ease-in-out infinite;
}

.page-hero__content,
.page-hero__actions {
  position: relative;
  z-index: 1;
}

.page-hero__eyebrow {
  margin: 0 0 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--brand-500);
}

.page-hero h1 {
  font-size: clamp(34px, 4vw, 54px);
  line-height: 0.96;
}

.page-hero p {
  max-width: 840px;
  margin-top: 14px;
  color: var(--text-secondary);
  line-height: 1.75;
}

.page-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@keyframes orbitSpinA {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes orbitSpinB {
  from {
    transform: rotate(360deg);
  }
  to {
    transform: rotate(0deg);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.45;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

@media (max-width: 900px) {
  .page-hero {
    grid-template-columns: 1fr;
  }
}

/* Dark mode overrides */
[data-theme="dark"] .page-hero {
  border-color: rgba(163, 203, 255, 0.16);
  background:
    linear-gradient(180deg, rgba(12, 20, 34, 0.86), rgba(8, 14, 26, 0.94)),
    radial-gradient(circle at top right, rgba(79, 140, 255, 0.16), transparent 28%),
    radial-gradient(circle at 22% 92%, rgba(56, 215, 197, 0.12), transparent 18%);
}
[data-theme="dark"] .page-hero::after {
  border-color: rgba(255, 255, 255, 0.04);
}
[data-theme="dark"] .page-hero__noise {
  opacity: 0.35;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
}
[data-theme="dark"] .page-hero__eyebrow {
  color: var(--brand-300);
}
[data-theme="dark"] .orbit {
  stroke: rgba(163, 203, 255, 0.14);
}
[data-theme="dark"] .dot {
  fill: rgba(255, 255, 255, 0.72);
}
</style>
