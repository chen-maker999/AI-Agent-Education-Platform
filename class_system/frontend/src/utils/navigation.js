export const shellNavigation = {
  student: [
    { label: '工作台', to: '/dashboard', icon: 'compass' },
    { label: '智能问答', to: '/chat', icon: 'spark' },
    { label: '知识资产', to: '/knowledge', icon: 'database' },
    { label: '知识图谱', to: '/graph', icon: 'graph' },
    { label: '作业中心', to: '/homework', icon: 'file' },
    { label: '学习评估', to: '/evaluation', icon: 'chart' },
    { label: '学习画像', to: '/portrait', icon: 'user' },
    { label: '设置', to: '/settings', icon: 'settings' }
  ],
  teacher: [
    { label: '工作台', to: '/dashboard', icon: 'compass' },
    { label: '智能问答', to: '/chat', icon: 'spark' },
    { label: '知识资产', to: '/knowledge', icon: 'database' },
    { label: '知识图谱', to: '/graph', icon: 'graph' },
    { label: '作业中心', to: '/homework', icon: 'file' },
    { label: '学习评估', to: '/evaluation', icon: 'chart' },
    { label: '预警中心', to: '/warning', icon: 'alert' },
    { label: '学习画像', to: '/portrait', icon: 'user' },
    { label: '设置', to: '/settings', icon: 'settings' }
  ],
  admin: [
    { label: '工作台', to: '/dashboard', icon: 'compass' },
    { label: '智能问答', to: '/chat', icon: 'spark' },
    { label: '知识资产', to: '/knowledge', icon: 'database' },
    { label: '知识图谱', to: '/graph', icon: 'graph' },
    { label: '作业中心', to: '/homework', icon: 'file' },
    { label: '学习评估', to: '/evaluation', icon: 'chart' },
    { label: '预警中心', to: '/warning', icon: 'alert' },
    { label: '学习画像', to: '/portrait', icon: 'user' },
    { label: 'Agent Studio', to: '/studio', icon: 'layout' },
    { label: '平台接入', to: '/integrations', icon: 'plug' },
    { label: '设置', to: '/settings', icon: 'settings' }
  ]
}

export const workspaceTabs = {
  student: [
    { label: '今日总览', to: '/dashboard' },
    { label: '答疑工作台', to: '/chat' },
    { label: '知识资产', to: '/knowledge' },
    { label: '作业中心', to: '/homework' },
    { label: '学习画像', to: '/portrait' }
  ],
  teacher: [
    { label: '班级驾驶舱', to: '/dashboard' },
    { label: '课程问答', to: '/chat' },
    { label: '知识资产', to: '/knowledge' },
    { label: '批改队列', to: '/homework' },
    { label: '预警干预', to: '/warning' }
  ],
  admin: [
    { label: '平台总览', to: '/dashboard' },
    { label: '知识资产', to: '/knowledge' },
    { label: 'Agent Studio', to: '/studio' },
    { label: '平台接入', to: '/integrations' },
    { label: '预警态势', to: '/warning' }
  ]
}

export const globalSearchSamples = [
  { type: 'course', value: 'Python 编程' },
  { type: 'knowledge', value: '递归与动态规划' },
  { type: 'document', value: '高等数学期末复习讲义.pdf' },
  { type: 'student', value: '张三' },
  { type: 'homework', value: '算法设计作业 3' },
  { type: 'warning', value: '成绩波动预警' }
]
