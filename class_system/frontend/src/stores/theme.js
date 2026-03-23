import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref(localStorage.getItem('edunav-theme') || 'light')

  function apply(t) {
    document.documentElement.setAttribute('data-theme', t)
    document.body.style.background = t === 'light' ? '#dde4ee' : '#070d1c'
  }

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  watch(theme, (t) => {
    localStorage.setItem('edunav-theme', t)
    apply(t)
  }, { immediate: true })

  return { theme, toggle }
})
