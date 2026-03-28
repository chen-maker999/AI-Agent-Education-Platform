export function toList(payload) {
  if (Array.isArray(payload)) {
    return payload
  }
  if (Array.isArray(payload?.items)) {
    return payload.items
  }
  if (Array.isArray(payload?.data)) {
    return payload.data
  }
  return []
}

export function summarizeDocuments(items = []) {
  const list = toList(items)
  return list.map((doc, index) => ({
    id: doc.doc_id || doc.id || `doc_${index}`,
    title: doc.metadata?.filename || doc.filename || `知识文档 ${index + 1}`,
    course: doc.course || doc.metadata?.course_id || '默认课程',
    chunks: doc.metadata?.chunk_count || (doc.metadata?.chunk_index ?? -1) + 1 || doc.chunk_count || 0,
    status: doc.status || '已索引',
    updatedAt: doc.updated_at || doc.created_at || '刚刚'
  }))
}

export function summarizeKnowledgePoints(items = []) {
  return toList(items).map((item, index) => ({
    id: item.id || item.point_id || `kp_${index}`,
    name: item.name || item.title || `知识点 ${index + 1}`,
    description: item.description || item.summary || '暂无说明',
    mastery: item.mastery ?? 76 + (index % 4) * 5,
    course: item.course_name || item.course_id || '通用课程'
  }))
}

export function summarizeGraphs(graphs = [], nodes = [], edges = []) {
  const graphList = toList(graphs)
  const nodeList = toList(nodes)
  const edgeList = toList(edges)
  const domains = ['Python', 'Java', '算法', '数据结构', 'Web']

  return {
    totalGraphs: graphList.length,
    totalNodes: nodeList.length,
    totalEdges: edgeList.length,
    domains: domains.map((name, index) => ({
      name,
      count: Math.max(1, Math.floor(nodeList.length / domains.length) + (index % 2))
    }))
  }
}

export function summarizeHomework(items = []) {
  return toList(items).map((item, index) => {
    const raw = item.status || 'pending'
    const uiStatus = raw === 'reviewed' ? 'reviewed' : 'pending'
    return {
      id: item.homework_id || item.id || `hw_${index}`,
      filename: item.filename || item.title || item.name || `作业_${index + 1}.pdf`,
      mimeType: item.mime_type || item.mimeType || '',
      uploader: item.student_id || item.uploader || item.user_name || item.student_name || item.created_by || '未知用户',
      course: item.course || item.course_name || '未分类课程',
      uploadTime: item.upload_time || item.created_at || '刚刚',
      status: uiStatus,
      score: item.score ?? null,
      aiCommentCount: item.ai_comment_count ?? 0,
      // AI 生成作业的字段
      isGenerated: item.isGenerated || false,
      hasReview: item.hasReview || item.ai_comment_count > 0 || false,
      generatedFileUrl: item.generatedFileUrl || item.file_url || null,
      generatedHomeworkId: item.generatedHomeworkId || item.homework_id || null
    }
  })
}

export function summarizeEvaluation(summary = {}, history = []) {
  const summaryData = summary || {}
  return {
    mastery: summaryData.mastery ?? 84,
    progress: summaryData.progress ?? 67,
    grade: summaryData.grade || 'A-',
    trend: summaryData.trend || 'up',
    change: summaryData.change || '+4.8%',
    history: toList(history).map((item, index) => ({
      id: item.id || `eh_${index}`,
      title: item.type || item.title || '阶段评估',
      date: item.date || item.created_at || '本周',
      score: typeof item.score === 'number' ? `${item.score} 分` : item.score || '88 分'
    }))
  }
}

export function summarizeWarnings(items = [], stats = {}) {
  const list = toList(items).map((item, index) => ({
    id: item.id || `warn_${index}`,
    studentId: item.student_id || item.user_id || `student_${index}`,
    student: item.student || item.student_name || `学生 ${index + 1}`,
    course: item.course || item.course_name || '程序设计基础',
    level: item.level || 'medium',
    levelText: item.levelText || levelText(item.level || 'medium'),
    description: item.description || item.reason || '近期学习行为和成绩波动出现异常。',
    trigger: item.trigger || '成绩波动',
    date: item.date || item.created_at || '今日',
    status: item.status || 'active'
  }))

  return {
    list,
    stats: [
      { title: '高风险', value: stats.high ?? list.filter((item) => item.level === 'high').length, tone: 'danger' },
      { title: '中风险', value: stats.medium ?? list.filter((item) => item.level === 'medium').length, tone: 'warning' },
      { title: '低风险', value: stats.low ?? list.filter((item) => item.level === 'low').length, tone: 'info' },
      { title: '已处理', value: stats.resolved ?? list.filter((item) => item.status === 'resolved').length, tone: 'success' }
    ]
  }
}

export function summarizePortrait(payload = {}, extras = {}) {
  const data = payload || {}
  return {
    name: data.name || data.username || '学习者',
    roleTitle: data.role_title || '跨课程学习者',
    mastery: data.mastery ?? 82,
    focus: data.focus ?? 74,
    completion: data.completion ?? 69,
    risk: data.risk ?? '中等',
    strengths: toList(extras.strengths).length
      ? toList(extras.strengths)
      : ['概念理解快', '复盘积极', '知识连接能力强'],
    weaknesses: toList(extras.weaknesses).length
      ? toList(extras.weaknesses)
      : ['复杂题拆解能力待提升', '代码规范性波动'],
    progress: toList(extras.progress).length
      ? toList(extras.progress)
      : [
          { label: '近 7 天学习时长', value: '11.5h' },
          { label: '完成练习数', value: '26' },
          { label: '错题回看率', value: '78%' }
        ]
  }
}

export function summarizeSettings(user) {
  return {
    username: user?.username || '未命名用户',
    email: user?.email || '未绑定',
    phone: user?.phone || '未绑定',
    role: user?.role || 'student'
  }
}

function levelText(level) {
  if (level === 'high') return '高风险'
  if (level === 'low') return '低风险'
  return '中风险'
}
