import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/chat', name: 'Chat', component: () => import('@/views/Chat.vue'), meta: { requiresAuth: true } },
  { path: '/knowledge', name: 'Knowledge', component: () => import('@/views/Knowledge.vue'), meta: { requiresAuth: true } },
  { path: '/graph', name: 'KnowledgeGraph', component: () => import('@/views/KnowledgeGraph.vue'), meta: { requiresAuth: true } },
  { path: '/portrait', name: 'Portrait', component: () => import('@/views/Portrait.vue'), meta: { requiresAuth: true } },
  { path: '/portrait/:studentId', name: 'StudentDetail', component: () => import('@/views/StudentDetail.vue'), meta: { requiresAuth: true } },
  { path: '/homework', name: 'Homework', component: () => import('@/views/Homework.vue'), meta: { requiresAuth: true } },
  { path: '/evaluation', name: 'Evaluation', component: () => import('@/views/Evaluation.vue'), meta: { requiresAuth: true } },
  { path: '/warning', name: 'Warning', component: () => import('@/views/Warning.vue'), meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: () => import('@/views/Settings.vue'), meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // 未登录时重定向到首页，首页会自动弹出登录框
    next('/')
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
