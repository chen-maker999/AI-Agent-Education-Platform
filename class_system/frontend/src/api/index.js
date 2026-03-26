import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
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
          const res = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
          if (res.data.code === 200) {
            localStorage.setItem('token', res.data.data.access_token)
            localStorage.setItem('refreshToken', res.data.data.refresh_token)
            error.config.headers.Authorization = `Bearer ${res.data.data.access_token}`
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
  list: (params) => api.get('/homework/', { params }),
  presigned: (id) => api.get(`/homework/${id}/presigned`),
  statistics: () => api.get('/homework/statistics/summary'),
  updateStatus: (id, status) =>
    api.patch(`/homework/${id}/status`, null, { params: { status } })
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

export const ragApi = {
  // 通用对话接口 - 用于通用问答（非流式）
  chat: (data) => api.post('/chat/message', {
    message: data.query || data.message,
    student_id: data.student_id || 'guest',
    session_id: data.session_id,
    mode: data.mode || 'general',
    context: data.context || {},
    tools: data.tools || null
  }),

  // 流式对话
  chatStream: (data) => {
    const token = localStorage.getItem('token')
    const payload = {
      message: data.query || data.message || '',
      student_id: data.student_id || 'guest',
      session_id: data.session_id || `chat_${data.mode || 'general'}`,
      mode: data.mode || 'general',
      context: data.context || {}
    }
    
    // Debug log
    console.log('chatStream request:', payload)
    
    return fetch('/api/v1/chat/message/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(payload)
    })
  },

  health: () => api.get('/knowledge/rag/health'),
  history: (sessionId) => api.get(`/knowledge/rag/history/${sessionId}`),
  clearHistory: (sessionId) => api.delete(`/knowledge/rag/history/${sessionId}`),

  // RAG知识库对话 - 用于知识库检索
  ragChat: (data) => api.post('/knowledge/rag/chat', {
    query: data.query || data.message,
    student_id: data.student_id,
    session_id: data.session_id,
    use_rewrite: data.use_rewrite !== false,
    use_rerank: data.use_rerank || false,
    top_k: data.top_k || 5
  }),

  // 知识库文件上传（自动分块、向量化、索引）
  upload: (formData) => api.post('/knowledge/rag/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  // 获取已上传的文档列表
  listDocuments: (courseId = 'default') => api.get('/knowledge/rag/documents', { params: { course_id: courseId } }),

  // 删除文档
  deleteDocument: (docId) => api.delete(`/knowledge/rag/documents/${docId}`)
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

export const reviewApi = {
  // Kimi AI 智能批改（GET，返回批改结果）
  grade: (homeworkId) => api.get(`/homework_review/ai-grade/${homeworkId}`),
  // 获取批改详情
  get: (reviewId) => api.get(`/homework_review/${reviewId}`),
  // 下载批改后文件
  download: (reviewId) => api.get(`/homework_review/${reviewId}/download`),
  // 列出批改记录
  list: (params) => api.get('/homework_review/list', { params }),
  // 删除批改记录
  delete: (reviewId) => api.delete(`/homework_review/${reviewId}`),
  // 轮询批改状态（支持 SSE 流式进度）
  gradeStream: (homeworkId) => {
    const token = localStorage.getItem('token')
    return fetch(`/api/v1/homework_review/ai-grade/${homeworkId}`, {
      method: 'GET',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    })
  }
}

export default api
