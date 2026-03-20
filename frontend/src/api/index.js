import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000  // 120秒超时，适用于生成练习等耗时操作
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  async error => {
    if (error.response?.status === 401) {
      // 登录接口返回 401 表示用户名或密码错误，不尝试 refresh，直接抛出
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      if (isLoginRequest) {
        return Promise.reject(error)
      }
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          // 注意：这里的 res 已经被上一个拦截器提取了 data，所以是 res.data
          const res = await api.post('/auth/refresh', { refresh_token: refreshToken })
          if (res.code === 200) {
            localStorage.setItem('token', res.data.access_token)
            localStorage.setItem('refreshToken', res.data.refresh_token)
            error.config.headers.Authorization = `Bearer ${res.data.access_token}`
            return api.request(error.config)
          }
        } catch (e) {
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (data) => {
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  register: (data) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  refresh: (data) => api.post('/auth/refresh', data),
  me: () => api.get('/auth/me')
}

export const rolesApi = {
  list: () => api.get('/roles'),
  get: (id) => api.get(`/roles/${id}`),
  create: (data) => api.post('/roles', data),
  update: (id, data) => api.put(`/roles/${id}`, data),
  delete: (id) => api.delete(`/roles/${id}`),
  permissions: (id) => api.get(`/roles/${id}/permissions`)
}

export const collectApi = {
  behavior: (data) => api.post('/collect/behavior', data),
  homework: (data) => api.post('/collect/homework', data),
  batch: (data) => api.post('/collect/batch', data),
  status: () => api.get('/collect/status'),
  adapt: (platform, data) => api.post(`/collect/adapt/${platform}`, data)
}

export const homeworkApi = {
  upload: (formData) => api.post('/homework/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  download: (id) => api.get(`/homework/${id}/download`),
  get: (id) => api.get(`/homework/${id}`),
  delete: (id) => api.delete(`/homework/${id}`),
  // 避免 FastAPI 对尾斜杠的 307 重定向触发跨域
  list: (params) => api.get('/homework', { params }),
  presigned: (id) => api.get(`/homework/${id}/presigned`),
  statistics: () => api.get('/homework/statistics/summary'),
  updateStatus: (id, status) => api.patch(`/homework/${id}/status`, { status })
}

// 练习文件生成 API
export const worksheetApi = {
  // 生成练习文件
  generate: (data) => api.post('/worksheet/generate', data),

  // 获取练习文件列表
  list: (params) => api.get('/worksheet/list', { params }),

  // 获取练习文件详情
  get: (worksheetId) => api.get(`/worksheet/${worksheetId}`),

  // 下载练习文件PDF
  download: (worksheetId) => api.get(`/worksheet/${worksheetId}/download`, {
    responseType: 'blob'
  }),

  // 预览练习内容
  preview: (worksheetId) => api.get(`/worksheet/preview/${worksheetId}`),

  // 删除练习文件
  delete: (worksheetId) => api.delete(`/worksheet/${worksheetId}`)
}

// Agent 内置工具 API（与创建智能体中的「工具-内置」对应，需真实调用后端）
export const agentToolsApi = {
  list: () => api.get('/agent/tools/list'),
  read: (data) => api.post('/agent/tools/read', data),
  edit: (data) => api.post('/agent/tools/edit', data),
  editWrite: (data) => api.post('/agent/tools/edit/write', data),
  terminal: (data) => api.post('/agent/tools/terminal', data),
  preview: (data) => api.post('/agent/tools/preview', data),
  webSearch: (data) => api.post('/agent/tools/web_search', data)
}

// Agent CRUD + 对话
export const agentApi = {
  list: (params) => api.get('/agent', { params }),
  get: (id) => api.get(`/agent/${id}`),
  create: (data) => api.post('/agent', data),
  update: (id, data) => api.put(`/agent/${id}`, data),
  delete: (id) => api.delete(`/agent/${id}`),
  chat: (data) => api.post('/agent/chat', data)
}

export const portraitApi = {
  generate: (data) => api.post('/portrait/generate', data),
  get: (studentId) => api.get(`/portrait/${studentId}`),
  group: (data) => api.post('/portrait/group', data),
  pattern: (data) => api.post('/portrait/pattern', data),
  strengths: (studentId) => api.get(`/portrait/${studentId}/strengths`),
  weaknesses: (studentId) => api.get(`/portrait/${studentId}/weaknesses`),
  progress: (studentId) => api.get(`/portrait/${studentId}/progress`),
  compare: (data) => api.post('/portrait/compare', data),
  update: (studentId, data) => api.put(`/portrait/${studentId}`, data)
}

export const knowledgeApi = {
  points: {
    create: (data) => api.post('/knowledge/points', data),
    get: (id) => api.get(`/knowledge/points/${id}`),
    update: (id, data) => api.put(`/knowledge/points/${id}`, data),
    delete: (id) => api.delete(`/knowledge/points/${id}`),
    list: (params) => api.get('/knowledge/points', { params }),
    search: (q) => api.get('/knowledge/points/search', { params: { q } })
  },
  graph: {
    create: (data) => api.post('/knowledge/graph', data),
    get: (id) => api.get(`/knowledge/graph/${id}`),
    update: (id, data) => api.put(`/knowledge/graph/${id}`, data),
    delete: (id) => api.delete(`/knowledge/graph/${id}`),
    list: () => api.get('/knowledge/graph'),
    nodes: (id) => api.get(`/knowledge/graph/${id}/nodes`),
    edges: (id) => api.get(`/knowledge/graph/${id}/edges`),
    query: (data) => api.post('/knowledge/graph/query', data)
  },
  vector: {
    create: (data) => api.post('/knowledge/vector', data),
    search: (data) => api.post('/knowledge/vector/search', data),
    stats: () => api.get('/knowledge/vector/stats')
  },
  chunk: {
    create: (data) => api.post('/knowledge/chunk', data),
    list: (params) => api.get('/knowledge/chunk', { params }),
    get: (id) => api.get(`/knowledge/chunk/${id}`)
  },
  embedding: {
    encode: (data) => api.post('/knowledge/embedding/encode', data),
    batch: (data) => api.post('/knowledge/embedding/batch', data)
  },
  faiss: {
    create: (data) => api.post('/knowledge/faiss', data),
    search: (data) => api.post('/knowledge/faiss/search', data),
    stats: () => api.get('/knowledge/faiss/stats')
  },
  es: {
    index: (data) => api.post('/knowledge/es/index', data),
    search: (data) => api.post('/knowledge/es/search', data),
    stats: () => api.get('/knowledge/es/stats')
  },
  queryRewrite: (data) => api.post('/knowledge/query_rewrite', data),
  router: (data) => api.post('/knowledge/router', data),
  search: (data) => api.post('/knowledge/search', data),
  fusion: (data) => api.post('/knowledge/fusion', data),
  rerank: (data) => api.post('/knowledge/rerank', data)
}

export const libraryApi = {
  create: (data) => api.post('/knowledge/library', data),
  my: (ownerId, page = 1, pageSize = 50) =>
    api.get('/knowledge/library/my', { params: { owner_id: ownerId, page, page_size: pageSize } }),
  get: (kbId) => api.get(`/knowledge/library/${kbId}`),
  update: (kbId, data) => api.put(`/knowledge/library/${kbId}`, data),
  delete: (kbId) => api.delete(`/knowledge/library/${kbId}`)
}

export const ragApi = {
  chat: (data) => api.post('/knowledge/rag/chat', data),
  health: () => api.get('/knowledge/rag/health'),
  history: (sessionId) => api.get(`/knowledge/rag/history/${sessionId}`),
  clearHistory: (sessionId) => api.delete(`/knowledge/rag/history/${sessionId}`),

  // 知识库文件上传（自动分块、向量化、索引）
  upload: (formData) => api.post('/knowledge/rag/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  // 获取已上传的文档列表；opts.allCourses=true 时列出所有 course_id（脚本/Agent 导入的专题库也会显示）
  listDocuments: (courseId = 'default', opts = {}) => {
    const params = {
      course_id: courseId,
      page: opts.page ?? 1,
      page_size: opts.pageSize ?? 100
    }
    if (opts.allCourses) params.all_courses = true
    return api.get('/knowledge/rag/documents', { params })
  },

  // 从URL抓取文档
  fetchDocument: (url, courseId = 'default') => {
    const formData = new FormData()
    formData.append('url', url)
    formData.append('course_id', courseId)
    return api.post('/knowledge/rag/fetch', formData)
  },

  // 删除文档
  deleteDocument: (docId) => api.delete(`/knowledge/rag/documents/${docId}`),

  // 按文件名删除所有文档块
  deleteDocumentByFilename: (filename) => api.delete(`/knowledge/rag/documents/by-filename/${encodeURIComponent(filename)}`)
}

// 智能问答 Chat API
export const chatApi = {
  // 发送消息
  message: (data) => api.post('/chat/message', data),
  
  // 获取历史记录
  history: (sessionId, limit = 50) => api.get(`/chat/history/${sessionId}`, { params: { limit } }),
  
  // 获取学生的所有会话
  sessions: (studentId, page = 1, pageSize = 20) => api.get(`/chat/sessions/${studentId}`, { params: { page, page_size: pageSize } }),
  
  // 提交反馈
  feedback: (data) => api.post('/chat/feedback', data),
  
  // 获取统计
  stats: (studentId) => api.get(`/chat/stats/${studentId}`),
  
  // 获取推荐问题
  suggest: (sessionId) => api.get(`/chat/suggest/${sessionId}`),
  
  // 知识点问答
  knowledge: (knowledgePointId, studentId) => api.get(`/chat/knowledge/${knowledgePointId}`, { params: { student_id: studentId } }),
  
  // 错误纠正
  correct: (data) => api.post('/chat/correct', data)
}

export const feedbackApi = {
  submit: (data) => api.post('/feedback/submit', data),
  list: (params) => api.get('/feedback', { params }),
  stats: () => api.get('/feedback/stats')
}

export const evaluationApi = {
  assess: (data) => api.post('/intelligence/evaluate/assess', data),
  history: (studentId) => api.get(`/intelligence/evaluate/history/${studentId}`),
  summary: (studentId) => api.get(`/intelligence/evaluate/summary/${studentId}`)
}

export const warningApi = {
  list: (params) => api.get('/intelligence/warning', { params }),
  create: (data) => api.post('/intelligence/warning', data),
  update: (id, data) => api.put(`/intelligence/warning/${id}`, data),
  delete: (id) => api.delete(`/intelligence/warning/${id}`),
  stats: () => api.get('/intelligence/warning/stats'),
  analyze: (data) => api.post('/intelligence/warning/analyze', data),
  studentWarnings: (studentId) => api.get(`/intelligence/warning/student/${studentId}`),
  notify: (studentId, warningId, channel) => api.post(`/intelligence/warning/notify?student_id=${studentId}&warning_id=${warningId}&channel=${channel}`)
}

export const configApi = {
  get: (key) => api.get(`/config/${key}`),
  set: (key, value) => api.put(`/config/${key}`, { value }),
  list: () => api.get('/config')
}

export default api
