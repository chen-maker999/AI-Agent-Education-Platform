export const ROLE_ORDER = ['guest', 'student', 'teacher', 'admin']

export function getUserRole(user) {
  const role = user?.role
  if (ROLE_ORDER.includes(role)) {
    return role
  }
  return 'guest'
}

export function canAccessRole(user, roles = []) {
  if (!roles?.length) {
    return true
  }

  const currentRole = getUserRole(user)
  if (roles.includes(currentRole)) {
    return true
  }

  if (currentRole === 'admin') {
    return roles.includes('teacher') || roles.includes('admin')
  }

  return false
}

export function getWorkspaceLabel(role) {
  switch (role) {
    case 'teacher':
      return '教学工作台'
    case 'admin':
      return '平台工作台'
    case 'student':
      return '学习工作台'
    default:
      return 'EduNavigator'
  }
}

export function isShellLayout(route) {
  return route?.meta?.layout === 'shell'
}

export function mapSearchType(type) {
  const labels = {
    course: '课程',
    knowledge: '知识点',
    document: '文档',
    student: '学生',
    homework: '作业',
    warning: '预警'
  }

  return labels[type] || '资源'
}
