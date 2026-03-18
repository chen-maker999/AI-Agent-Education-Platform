<template>
  <div class="app-container">
    <nav class="navbar">
      <router-link :to="authStore.isAuthenticated ? '/dashboard' : '/'" class="navbar-brand">
        <img :src="brandIcon" alt="AI教育平台" class="brand-logo">
      </router-link>

      <div class="navbar-menu" v-if="authStore.isAuthenticated">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          首页
        </router-link>
        <router-link to="/chat" class="nav-item" :class="{ active: $route.path === '/chat' }">
          <img :src="navIcons.chat" alt="智能问答" class="nav-icon">
          智能问答
        </router-link>
        <router-link to="/knowledge" class="nav-item" :class="{ active: $route.path === '/knowledge' }">
          <img :src="navIcons.knowledge" alt="知识库" class="nav-icon">
          知识库
        </router-link>
        <router-link to="/graph" class="nav-item" :class="{ active: $route.path === '/graph' }">
          <img :src="navIcons.graph" alt="知识图谱" class="nav-icon">
          知识图谱
        </router-link>
        <!-- 学生端菜单 -->
        <template v-if="isStudent">
          <router-link to="/evaluation" class="nav-item" :class="{ active: $route.path === '/evaluation' }">
            <img :src="navIcons.evaluation" alt="智能评估" class="nav-icon">
            智能评估
          </router-link>
          <router-link to="/portrait" class="nav-item" :class="{ active: $route.path === '/portrait' }">
            <img :src="navIcons.portrait" alt="学习画像" class="nav-icon">
            学习画像
          </router-link>
        </template>
        <!-- 教师/管理员端菜单 -->
        <template v-if="isTeacher">
          <router-link to="/evaluation" class="nav-item" :class="{ active: $route.path === '/evaluation' }">
            <img :src="navIcons.evaluation" alt="智能评估" class="nav-icon">
            智能评估
          </router-link>
          <router-link to="/warning" class="nav-item" :class="{ active: $route.path === '/warning' }">
            <img :src="navIcons.warning" alt="预警中心" class="nav-icon">
            预警中心
          </router-link>
          <router-link to="/portrait" class="nav-item" :class="{ active: $route.path === '/portrait' }">
            <img :src="navIcons.portrait" alt="学习画像" class="nav-icon">
            学习画像
          </router-link>
        </template>
      </div>

      <div class="navbar-user" v-if="authStore.isAuthenticated">
        <button class="btn-icon" @click="$router.push('/settings')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
        <div class="user-avatar" @click="showUserMenu = !showUserMenu">
          {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
        </div>
        <div v-if="showUserMenu" class="user-dropdown">
          <a @click="$router.push('/settings'); showUserMenu = false">个人设置</a>
          <a @click="handleLogout">退出登录</a>
        </div>
      </div>
      <div class="navbar-user" v-else>
        <router-link to="/login" class="btn btn-secondary">登录</router-link>
        <router-link to="/register" class="btn btn-primary">注册</router-link>
      </div>
    </nav>

    <!-- 左侧竖向控制条 -->
    <div class="left-sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" v-if="authStore.isAuthenticated">
      <img :src="navIcons.homework" alt="作业" class="toggle-icon">
    </div>

    <!-- 侧边栏 - 作业管理 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }" v-if="authStore.isAuthenticated">
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline :points="sidebarCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"/>
        </svg>
      </div>
      <div class="sidebar-content" v-show="!sidebarCollapsed">
        <div class="sidebar-homework">
          <Homework />
        </div>
      </div>
    </aside>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Homework from '@/views/Homework.vue'
import elementIcon from '../icons/icon_u7adlm4fwln/element.png'
import chatIcon from '../icons/icon_u7adlm4fwln/duihua.png'
import knowledgeIcon from '../icons/icon_u7adlm4fwln/shujia.png'
import graphIcon from '../icons/icon_u7adlm4fwln/fankaishu.png'
import portraitIcon from '../icons/icon_u7adlm4fwln/classroom_teacher_professor_school_students.png'
import homeworkIcon from '../icons/icon_u7adlm4fwln/chengji.png'
import evaluationIcon from '../icons/icon_u7adlm4fwln/tongji.png'
import warningIcon from '../icons/icon_u7adlm4fwln/baozhi.png'

const authStore = useAuthStore()
const router = useRouter()
const showUserMenu = ref(false)
const sidebarCollapsed = ref(true)

const userRole = computed(() => authStore.user?.role || 'student')
const isStudent = computed(() => userRole.value === 'student')
const isTeacher = computed(() => userRole.value === 'teacher' || userRole.value === 'admin')
const brandIcon = elementIcon
const navIcons = {
  chat: chatIcon,
  knowledge: knowledgeIcon,
  graph: graphIcon,
  portrait: portraitIcon,
  homework: homeworkIcon,
  evaluation: evaluationIcon,
  warning: warningIcon
}

const handleLogout = async () => {
  showUserMenu.value = false
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.brand-logo {
  width: 88px;
  height: 88px;
  object-fit: contain;
  margin-left: -5px;
}

.nav-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.nav-item-btn {
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
  text-align: left;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: var(--transition);
}
.btn-icon:hover { background: var(--bg-tertiary); color: var(--text-primary); }

.user-avatar { position: relative; }

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  min-width: 160px;
  z-index: 1000;
}

.user-dropdown a {
  display: block;
  padding: 12px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
}

.user-dropdown a:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.user-dropdown a:first-child { border-radius: var(--radius) var(--radius) 0 0; }
.user-dropdown a:last-child { border-radius: 0 0 var(--radius) var(--radius); }

/* 左侧竖向控制条 */
.left-sidebar-toggle {
  position: fixed;
  top: 80px;
  left: 0;
  width: 24px;
  height: 64px;
  background: var(--primary);
  border: none;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99;
  transition: all 0.2s;
  box-shadow: 2px 0 8px rgba(0,0,0,0.15);
}

.left-sidebar-toggle:hover {
  width: 28px;
  background: var(--primary-dark, #4a6cf7);
}

.left-sidebar-toggle .toggle-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.left-sidebar-toggle .toggle-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  top: 64px;
  left: 0;
  width: 420px;
  height: calc(100vh - 64px);
  background: var(--bg-primary);
  border-right: 1px solid var(--border);
  z-index: 100;
  transition: transform 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  transform: translateX(-100%);
}

.sidebar-toggle {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.2s;
  z-index: 10;
}

.sidebar-toggle:hover {
  background: var(--border);
  color: var(--text-primary);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 48px 8px 12px 8px;
}

/* 侧边栏内作业页面紧凑布局 */
.sidebar-homework :deep(.homework-page) {
  max-width: none;
  padding: 0 4px;
  margin: 0;
}
.sidebar-homework :deep(.page-header-custom) {
  padding: 20px 16px;
  margin-bottom: 16px;
}
.sidebar-homework :deep(.header-text h1) {
  font-size: 20px;
}
.sidebar-homework :deep(.header-text p) {
  font-size: 13px;
}
.sidebar-homework :deep(.stats-grid) {
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.sidebar-homework :deep(.stat-card-custom) {
  padding: 14px 12px;
}
.sidebar-homework :deep(.content-card-modern) {
  overflow-x: auto;
}
.sidebar-homework :deep(.card-header-modern) {
  flex-wrap: wrap;
  gap: 8px;
}
.sidebar-homework :deep(.homework-table-modern) {
  overflow-x: auto;
}
.sidebar-homework :deep(.homework-table-modern table) {
  min-width: 380px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.sidebar-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: var(--primary-light);
  color: var(--primary);
}

.sidebar-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
  flex-shrink: 0;
}
</style>
