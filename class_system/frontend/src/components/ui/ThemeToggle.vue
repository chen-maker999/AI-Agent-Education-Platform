<template>
  <button class="theme-toggle-btn" type="button" @click="themeStore.toggle()"
    :title="themeStore.theme === 'dark' ? '切换亮色模式' : '切换暗色模式'">
    <!-- Sun icon (shown in dark mode → click to go light) -->
    <svg v-if="themeStore.theme === 'dark'" width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="3.5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M3.05 12.95l1.06-1.06M11.89 4.11l1.06-1.06"
        stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <!-- Moon icon (shown in light mode → click to go dark) -->
    <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M13.5 9.5A6 6 0 0 1 6.5 2.5a6 6 0 1 0 7 7z"
        stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>
</template>

<script setup>
import { useThemeStore } from '@/stores/theme'
const themeStore = useThemeStore()
</script>

<style scoped>
.theme-toggle-btn {
  width: 36px; height: 36px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--r-full);
  color: var(--text-secondary);
  border: 1px solid var(--glass-border);
  background: var(--glass-bg-light);
  transition: all var(--t-fast) ease;
  cursor: pointer;
}
.theme-toggle-btn:hover {
  color: var(--text-primary);
  border-color: var(--glass-border-hi);
  background: var(--glass-bg);
  box-shadow: var(--glow-blue);
}
</style>
