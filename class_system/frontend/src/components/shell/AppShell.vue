<template>
  <div class="shell-root" :class="{ collapsed }">
    <!-- ═══ LIGHT GRADIENT BACKDROP — macOS style ═══ -->
    <div class="shell-backdrop" aria-hidden="true">
      <svg class="shell-backdrop__svg" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">
        <defs>
          <radialGradient id="shOrbA" cx="15%" cy="12%" r="40%">
            <stop offset="0%" stop-color="#007aff" stop-opacity="0.07"/>
            <stop offset="100%" stop-color="#007aff" stop-opacity="0"/>
          </radialGradient>
          <radialGradient id="shOrbB" cx="85%" cy="10%" r="30%">
            <stop offset="0%" stop-color="#007aff" stop-opacity="0.04"/>
            <stop offset="100%" stop-color="#007aff" stop-opacity="0"/>
          </radialGradient>
          <radialGradient id="shOrbC" cx="78%" cy="85%" r="35%">
            <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.04"/>
            <stop offset="100%" stop-color="#f59e0b" stop-opacity="0"/>
          </radialGradient>
          <radialGradient id="shOrbD" cx="25%" cy="75%" r="28%">
            <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.02"/>
            <stop offset="100%" stop-color="#f43f5e" stop-opacity="0"/>
          </radialGradient>
          <filter id="shBlur"><feGaussianBlur stdDeviation="70"/></filter>
        </defs>
        <!-- Warm light gray bg + subtle dot pattern via rect -->
        <rect width="1600" height="1000" fill="#ececec"/>
        <rect width="1600" height="1000" fill="url(#shOrbA)" filter="url(#shBlur)"/>
        <rect width="1600" height="1000" fill="url(#shOrbB)" filter="url(#shBlur)"/>
        <rect width="1600" height="1000" fill="url(#shOrbC)" filter="url(#shBlur)"/>
        <rect width="1600" height="1000" fill="url(#shOrbD)" filter="url(#shBlur)"/>
      </svg>
    </div>

    <!-- ═══ SIDEBAR ═══ -->
    <aside class="shell-sidebar">
      <div class="shell-sidebar__glow"></div>

      <div class="shell-sidebar__header">
        <router-link to="/dashboard" class="brand-mark">
          <span class="brand-mark__logo">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <path d="M5 11L11 5L17 11L11 17Z" fill="none" stroke="#2563eb" stroke-width="1.5"/>
              <circle cx="11" cy="11" r="3" fill="#3b82f6"/>
            </svg>
          </span>
          <div v-if="!collapsed" class="brand-mark__text">
            <strong>EduNavigator</strong>
            <span>Search-native AI Classroom OS</span>
          </div>
        </router-link>
        <button class="collapse-trigger" type="button" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '收起'">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path :d="collapsed ? 'M5 2l5 5-5 5' : 'M9 2L4 7l5 5'" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <button class="shell-shortcut" type="button" @click="goToSearch">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span v-if="!collapsed">全局搜索</span>
        <kbd v-if="!collapsed">⌘K</kbd>
      </button>

      <nav class="shell-nav">
        <div v-for="section in navSections" :key="section.label" class="shell-nav__section">
          <p v-if="!collapsed" class="shell-nav__label">{{ section.label }}</p>
          <router-link v-for="item in section.items" :key="item.to" :to="item.to"
            class="shell-nav__item" :class="{ active: isActive(item.to) }"
            :title="collapsed ? item.label : ''">
            <AppIcon :name="item.icon" :size="16"/>
            <span v-if="!collapsed" class="shell-nav__text">{{ item.label }}</span>
            <span v-if="!collapsed && item.badge" class="badge" :class="item.badgeTone">{{ item.badge }}</span>
            <div v-if="isActive(item.to)" class="shell-nav__active-glow"></div>
          </router-link>
        </div>
      </nav>

      <div class="shell-sidebar__footer">
        <div class="shell-user" :class="{ compact: collapsed }">
          <div class="shell-user__avatar">{{ userInitial }}</div>
          <div v-if="!collapsed" class="shell-user__meta">
            <strong>{{ authStore.user?.username || 'User' }}</strong>
            <span>{{ roleLabel }}</span>
          </div>
        </div>
        <button v-if="!collapsed" class="btn-ghost shell-logout" type="button" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <!-- ═══ MAIN STAGE ═══ -->
    <div class="shell-stage">
      <!-- Topbar: 仅在总览页面显示 -->
      <header v-if="isDashboard" class="shell-topbar">
        <div class="shell-topbar__title">
          <p>{{ currentWorkspace }}</p>
          <strong>{{ route.meta?.workspace || 'EduNavigator' }}</strong>
        </div>
        <button class="shell-search" type="button" @click="goToSearch">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ searchPlaceholder }}</span>
          <kbd>⌘K</kbd>
        </button>
        <div class="shell-topbar__status">
          <button class="theme-toggle" type="button" @click="themeStore.toggle()" :title="themeStore.theme === 'dark' ? '切换亮色模式' : '切换暗色模式'">
            <svg v-if="themeStore.theme === 'dark'" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="3.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M3.05 12.95l1.06-1.06M11.89 4.11l1.06-1.06" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 9.5A6 6 0 0 1 6.5 2.5a6 6 0 1 0 7 7z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="status-pill tone-info">{{ roleLabel }}</span>
          <span class="status-pill tone-success">
            <span class="status-dot status-dot--online status-dot--pulse"></span>
            系统在线
          </span>
        </div>
      </header>

      <div class="shell-body" :class="{ 'no-topbar': !isDashboard }">
        <main class="shell-content"><slot/></main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { getUserRole, getWorkspaceLabel } from '@/utils/workspace'
import AppIcon from '@/components/ui/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const collapsed = ref(false)

const role = computed(() => getUserRole(authStore.user))
const currentWorkspace = computed(() => getWorkspaceLabel(role.value))
const searchPlaceholder = computed(() => route.meta?.searchPlaceholder || '搜索课程、知识点、作业、学生或工作流')
const roleLabel = computed(() => {
  if (role.value === 'teacher') return '教师'
  if (role.value === 'admin') return '管理员'
  return '学生'
})
const userInitial = computed(() => (authStore.user?.username || 'U').charAt(0).toUpperCase())

const navSections = computed(() => {
  const sections = [
    { label: 'Workspace', items: [
      { to: '/dashboard', label: '总览', icon: 'layout' },
      { to: '/chat', label: '智能问答', icon: 'spark' },
      { to: '/knowledge', label: '知识资产', icon: 'database' },
      { to: '/graph', label: '知识图谱', icon: 'graph' }
    ]},
    { label: 'Learning Loop', items: [
      { to: '/portrait', label: '学习画像', icon: 'radar' },
      { to: '/homework', label: '作业中心', icon: 'file' },
      { to: '/evaluation', label: '学习评估', icon: 'chart' }
    ]}
  ]
  if (role.value === 'teacher' || role.value === 'admin') {
    sections.push({ label: 'Teacher Ops', items: [
      { to: '/warning', label: '预警驾驶舱', icon: 'alert', badge: 'Hot', badgeTone: 'amber' }
    ]})
  }
  if (role.value === 'admin') {
    sections.push({ label: 'Platform', items: [
      { to: '/studio', label: 'Agent Studio', icon: 'flash' },
      { to: '/integrations', label: '平台接入', icon: 'plug' }
    ]})
  }
  sections.push({ label: 'Settings', items: [
    { to: '/settings', label: '平台设置', icon: 'settings' }
  ]})
  return sections
})

/** 是否为总览页面（topbar 仅在此页面显示） */
const isDashboard = computed(() => route.path === '/dashboard')

function isActive(to) { return route.path === to || route.path.startsWith(`${to}/`) }
function goToSearch() { router.push('/chat') }
async function handleLogout() {
  await authStore.logout()
  authStore.openAuthModal('login')
}
</script>

<style scoped>
.shell-root { position: relative; display: flex; width: 100vw; height: 100vh; overflow: hidden; }

/* Backdrop */
.shell-backdrop { position: absolute; inset: 0; pointer-events: none; z-index: 0; }
.shell-backdrop__svg { width: 100%; height: 100%; }

/* Sidebar */
.shell-sidebar {
  position: relative; z-index: 2;
  flex: 0 0 var(--sidebar-w);
  display: flex; flex-direction: column; gap: 10px;
  padding: 16px 12px 14px;
  border-right: 1px solid rgba(255, 255, 255, 0.65);
  background:
    linear-gradient(160deg, rgba(255,255,255,0.78) 0%, rgba(248,250,252,0.72) 100%);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.90),
    inset 0 0 0 1px rgba(0, 0, 0, 0.04),
    4px 0 24px rgba(0, 0, 0, 0.04);
  transition: flex-basis var(--t-slow) var(--ease-expo);
}
.shell-sidebar__glow {
  display: none;
}
.collapsed .shell-sidebar { flex-basis: var(--sidebar-w-sm); }

.shell-sidebar__header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.brand-mark { display: flex; align-items: center; gap: 10px; }
.brand-mark__logo {
  width: 38px; height: 38px; display: grid; place-items: center;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.10), rgba(0, 122, 255, 0.05));
  flex-shrink: 0;
}
.brand-mark__text strong { display: block; font-family: var(--font-display2); font-size: 15px; }
.brand-mark__text span { display: block; margin-top: 3px; color: var(--text-tertiary); font-size: 11px; }

.collapse-trigger {
  width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: 6px; color: var(--text-tertiary);
  border: 1px solid rgba(0, 0, 0, 0.08); background: rgba(0, 0, 0, 0.04);
  transition: all var(--t-fast) ease; flex-shrink: 0;
}
.collapse-trigger:hover { background: rgba(0, 0, 0, 0.07); color: var(--text-primary); }

.shell-shortcut {
  display: flex; align-items: center; gap: 10px;
  min-height: 40px; padding: 0 12px;
  border-radius: var(--r-full); color: var(--text-secondary);
  border: 1px solid rgba(0, 0, 0, 0.08); background: rgba(0, 0, 0, 0.04);
  transition: all var(--t-base) ease;
}
.shell-shortcut:hover { background: rgba(0, 0, 0, 0.07); border-color: rgba(0, 0, 0, 0.12); }
.shell-shortcut span { flex: 1; text-align: left; font-size: 13px; }
.shell-shortcut kbd, .shell-search kbd {
  padding: 2px 6px; border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.10); background: rgba(0, 0, 0, 0.05);
  color: var(--text-tertiary); font-size: 10px; font-family: var(--font-mono);
}

/* Nav */
.shell-nav { display: flex; flex: 1; flex-direction: column; gap: 12px; min-height: 0; overflow: auto; }
.shell-nav__section { display: flex; flex-direction: column; gap: 2px; }
.shell-nav__label {
  margin: 0 10px 4px; color: var(--text-muted);
  font-size: 10px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
}
.shell-nav__item {
  position: relative; display: flex; align-items: center; gap: 10px;
  min-height: 40px; padding: 0 12px; border-radius: var(--r-lg);
  color: var(--text-secondary); border: 1px solid transparent;
  transition: all var(--t-base) var(--ease-out);
}
.shell-nav__item:hover { color: var(--text-primary); background: rgba(0, 0, 0, 0.05); }

/* ── Liquid Glass active state ── */
.shell-nav__item.active {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(255, 255, 255, 0.80);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 0 0 1px rgba(249, 115, 22, 0.15),
    0 2px 8px rgba(249, 115, 22, 0.10),
    0 8px 24px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  font-weight: 600;
}

/* Liquid glass left accent bar — replaces the solid glow pill */
.shell-nav__active-glow {
  position: absolute; left: -1px; top: 18%; bottom: 18%; width: 2px;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(
    180deg,
    rgba(59, 130, 246, 0.00) 0%,
    rgba(249, 115, 22, 0.70) 30%,
    rgba(239, 68, 68, 0.90) 70%,
    rgba(239, 68, 68, 0.60) 100%
  );
  box-shadow:
    0 0 8px rgba(249, 115, 22, 0.50),
    0 0 16px rgba(239, 68, 68, 0.20),
    inset 0 1px 0 rgba(255, 255, 255, 0.60);
}
.shell-nav__text { flex: 1; font-size: 13px; }

/* Footer */
.shell-sidebar__footer { display: flex; flex-direction: column; gap: 8px; }
.shell-user {
  display: flex; align-items: center; gap: 10px;
  padding: 10px; border-radius: var(--r-lg);
  border: 1px solid rgba(0, 0, 0, 0.07); background: rgba(0, 0, 0, 0.03);
}
.shell-user.compact { justify-content: center; }
.shell-user__avatar {
  width: 36px; height: 36px; display: grid; place-items: center;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #f97316 50%, #ef4444 100%);
  color: #ffffff; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.shell-user__meta strong { display: block; font-size: 13px; }
.shell-user__meta span { display: block; margin-top: 3px; color: var(--text-tertiary); font-size: 11px; }
.shell-logout { width: 100%; min-height: 36px; font-size: 13px; }

/* Stage */
.shell-stage { position: relative; z-index: 1; display: flex; flex: 1; flex-direction: column; min-width: 0; }

/* Topbar */
.shell-topbar {
  display: grid; grid-template-columns: auto minmax(0,1fr) auto;
  align-items: center; gap: 16px;
  min-height: var(--topbar-h); padding: 12px 24px;
  position: relative; z-index: 10;
  border-bottom: 1px solid rgba(0, 0, 0, 0.07);
  background: rgba(255, 255, 255, 0.90);
  backdrop-filter: blur(20px);
}
.shell-topbar__title p {
  margin-bottom: 4px; color: var(--text-muted);
  font-size: 10px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
}
.shell-topbar__title strong { font-size: 16px; font-family: var(--font-display2); }

.shell-search {
  display: flex; align-items: center; gap: 10px;
  min-height: 40px; padding: 0 16px;
  border-radius: var(--r-full); color: var(--text-secondary);
  border: 1px solid rgba(0, 0, 0, 0.09); background: var(--bg-elevated);
  transition: border-color var(--t-base) ease, box-shadow var(--t-base) ease;
}
.shell-search:hover { border-color: rgba(0, 0, 0, 0.16); box-shadow: var(--shadow-xs); }
.shell-search span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; font-size: 13px; }
.shell-topbar__status { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }

/* Body — 无 topbar 时完全填满 */
.shell-body {
  display: flex; flex: 1; min-height: 0;
  padding: 20px;
}
/* 无 topbar 时：填满整个 stage */
.shell-body.no-topbar {
  padding: 0;
}
.shell-body.no-topbar .shell-content {
  padding-top: 0;
}
/* 列方向 flex：子页面根节点可用 flex:1 填满剩余高度，避免仅内容高度导致底部留白 */
.shell-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

/* Theme toggle */
.theme-toggle {
  width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--r-full); color: var(--text-secondary);
  border: 1px solid rgba(0, 0, 0, 0.09); background: var(--bg-elevated);
  transition: all var(--t-fast) ease;
}
.theme-toggle:hover {
  color: var(--text-primary);
  border-color: rgba(0, 0, 0, 0.16);
  box-shadow: var(--shadow-xs);
}

@media (max-width: 900px) {
  .shell-root { flex-direction: column; }
  .shell-sidebar { flex-basis: auto; width: 100%; border-right: 0; border-bottom: 1px solid rgba(0, 0, 0, 0.07); }
  .collapsed .shell-sidebar { flex-basis: auto; }
  .shell-topbar { grid-template-columns: 1fr; }
  .shell-topbar__status { justify-content: flex-start; }
}
</style>
