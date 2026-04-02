import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { canAccessRole } from '@/utils/workspace'

const shellMeta = (workspace, roles, contextPanel, extra = {}) => ({
  layout: 'shell',
  requiresAuth: true,
  roles,
  workspace,
  contextPanel,
  ...extra
})

const routes = [
  {
    path: '/',
    name: 'Intro',
    component: () => import('@/views/Intro.vue'),
    meta: {
      layout: 'guest',
      title: 'EduNavigator | 搜索原生 AI 教学平台',
      guest: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: shellMeta(
      '智学总览',
      ['student', 'teacher', 'admin'],
      '把答疑、知识、作业、画像和预警信号拉到同一条搜索驱动的工作流中。'
    )
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: shellMeta(
      '智能问答',
      ['student', 'teacher', 'admin'],
      '统一承载课程答疑、知识库对话、作业追问和行动建议。',
      {
        searchPlaceholder: '搜索问题、课程、知识点或对话上下文'
      }
    )
  },
  {
    path: '/agent-config',
    name: 'AgentConfig',
    component: () => import('@/views/AgentConfig.vue'),
    meta: shellMeta(
      'Agent配置',
      ['student', 'teacher', 'admin'],
      '配置 AI Agent 的行为模式、工具能力、响应风格和安全边界。'
    )
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/Knowledge.vue'),
    meta: shellMeta(
      '知识资产台',
      ['student', 'teacher', 'admin'],
      '集中管理课程文档、知识点、向量索引和可追问素材。',
      {
        searchPlaceholder: '搜索文档、知识点、课程或索引状态'
      }
    )
  },
  {
    path: '/graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraph.vue'),
    meta: shellMeta(
      '知识图谱',
      ['student', 'teacher', 'admin'],
      '从先修关系、跨课连接和学习路径理解知识网络。'
    )
  },
  {
    path: '/portrait',
    name: 'Portrait',
    component: () => import('@/views/Portrait.vue'),
    meta: shellMeta(
      '学习画像',
      ['student', 'teacher', 'admin'],
      '围绕掌握度、薄弱点、投入度与练习建议构建全景学情画像。'
    )
  },
  {
    path: '/portrait/:studentId',
    name: 'StudentDetail',
    component: () => import('@/views/StudentDetail.vue'),
    meta: shellMeta(
      '学生洞察',
      ['teacher', 'admin'],
      '从预警、画像、作业和练习联动到单个学生的精准干预。'
    )
  },
  {
    path: '/homework',
    name: 'Homework',
    component: () => import('@/views/Homework.vue'),
    meta: shellMeta(
      '作业中心',
      ['student', 'teacher', 'admin'],
      '支持上传、批改、批注回看与上下文级作业反馈。'
    )
  },
  {
    path: '/evaluation',
    name: 'Evaluation',
    component: () => import('@/views/Evaluation.vue'),
    meta: shellMeta(
      '学习评估',
      ['student', 'teacher', 'admin'],
      '把测评结果、趋势分析和后续练习组织成闭环。'
    )
  },
  {
    path: '/warning',
    name: 'Warning',
    component: () => import('@/views/Warning.vue'),
    meta: shellMeta(
      '预警驾驶舱',
      ['teacher', 'admin'],
      '聚合高风险学生、群体异常和可执行的教学干预动作。'
    )
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: shellMeta(
      '平台设置',
      ['student', 'teacher', 'admin'],
      '管理账号、通知偏好、主题表现和平台级个性化选项。'
    )
  },
  {
    path: '/studio',
    name: 'Studio',
    component: () => import('@/views/Studio.vue'),
    meta: shellMeta(
      'Agent Studio',
      ['admin'],
      '为课程 Agent 的构建、编排、调试和复用预留统一工作台。'
    )
  },
  {
    path: '/integrations',
    name: 'Integrations',
    component: () => import('@/views/Integrations.vue'),
    meta: shellMeta(
      '平台接入',
      ['admin'],
      '统一管理超星、钉钉等主流教学平台的嵌入能力与适配状态。'
    )
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (authStore.token && !authStore.user) {
    await authStore.fetchUserInfo()
  }

  if (to.meta.requiresAuth && authStore.token && !authStore.user) {
    await authStore.logout()
    authStore.openAuthModal('login')
    return false
  }

  if (to.path === '/' && authStore.isAuthenticated) {
    return '/dashboard'
  }

  // 如果已经显示了登录弹窗（用户主动退出），则允许停留在当前页面
  if (authStore.showAuthModal && !authStore.isAuthenticated) {
    return true
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    authStore.openAuthModal('login')
    return false
  }

  if (to.meta.guest && authStore.isAuthenticated) {
    return '/dashboard'
  }

  if (to.meta.roles && !canAccessRole(authStore.user, to.meta.roles)) {
    return '/dashboard'
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta?.title || (to.meta?.workspace ? `${to.meta.workspace} | EduNavigator` : 'EduNavigator')
})

export default router
