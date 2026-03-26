<template>
  <div class="app-root">
    <AppShell v-if="showShell">
      <router-view v-slot="{ Component, route }">
        <transition name="app-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </AppShell>

    <router-view v-else v-slot="{ Component, route }">
      <transition name="app-fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>

    <AuthModal />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from '@/components/shell/AppShell.vue'
import AuthModal from '@/components/ui/AuthModal.vue'
import { isShellLayout } from '@/utils/workspace'

const route = useRoute()
const showShell = computed(() => isShellLayout(route))
</script>

<style scoped>
.app-root {
  height: 100vh;
  overflow: hidden;
}

.app-root > .router-view,
.app-root > [class*="intro"] {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.app-fade {
  display: flex;
  min-width: 0;
}

.app-fade-enter-active,
.app-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.app-fade-enter-from,
.app-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
