import axios from 'axios'

// 工具格式转换：将字符串数组转为字典数组
// 后端 ChatRequest.tools 期望 [{id: "tool_name"}, ...] 格式
// 普通问答和知识库问答不需要 tools，应传 null
function _normalizeTools(tools) {
  if (!tools || tools.length === 0) return null
  // 如果是字符串数组，转为 {id: tool} 格式
  if (typeof tools[0] === 'string') {
    return tools.map(id => ({ id }))
  }
  // 如果已是字典数组，直接返回
  if (typeof tools[0] === 'object') {
    return tools
  }
  return null
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000  // 300秒超时，支持文件上传和大图片AI处理
})

// ===== 代码执行 =====
api.code = {
  execute: (data) => api.post('/code/execute', {
    code: data.code,
    language: data.language,
    timeout: data.timeout || 15,
    stdin: data.stdin || null
  })
}

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
  me: () => api.get('/auth/me'),
  updateProfile: (data) => api.patch('/auth/me', data),
  changePassword: (data) => api.patch('/auth/password', data)
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
    tools: _normalizeTools(data.tools)
  }),

  // 流式对话
  chatStream: (data) => {
    const token = localStorage.getItem('token')

    // kimi-k2.5 只接受固定的 top_p=0.95（强制 0.95，非 0.9）
    const effectiveTopP = (data.model === 'kimi-k2.5' || data.model === undefined)
      ? 0.95
      : (data.topP !== undefined ? data.topP : 0.9)

    const payload = {
      message: data.query || data.message || '',
      student_id: data.student_id || 'guest',
      session_id: data.session_id || `chat_${data.mode || 'general'}`,
      mode: data.mode || 'general',
      context: data.context || {},
      model: data.model || 'kimi-k2.5',
      temperature: data.temperature !== undefined ? data.temperature : 0.7,
      top_p: effectiveTopP,
      max_tokens: data.maxTokens || 4096,
      frequency_penalty: data.frequencyPenalty !== undefined ? data.frequencyPenalty : 0,
      presence_penalty: data.presencePenalty !== undefined ? data.presencePenalty : 0,
      tools: _normalizeTools(data.tools)
    }

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

export const homeworkGenApi = {
  // 生成作业
  generate: (data) => api.post('/homework-gen/generate', data),
  // 下载作业 PDF
  download: (homeworkId) => api.get(`/homework-gen/download/${homeworkId}`),
  // 获取作业列表
  list: (params) => api.get('/homework-gen/list', { params }),
  // 获取作业详情
  detail: (homeworkId) => api.get(`/homework-gen/detail/${homeworkId}`),
  // 获取可选课程列表
  courses: () => api.get('/homework-gen/courses'),
  // 删除作业
  delete: (homeworkId) => api.delete(`/homework-gen/${homeworkId}`)
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

// Agent 智能体 API
export const agentApi = {
  // ===== 基础 CRUD =====
  // 获取智能体列表
  list: () => api.get('/agent'),
  // 获取单个智能体
  get: (agentId) => api.get(`/agent/${agentId}`),
  // 创建智能体（同名则更新）
  create: (data) => api.post('/agent', data),
  // 更新智能体
  update: (agentId, data) => api.put(`/agent/${agentId}`, data),
  // 删除智能体
  delete: (agentId) => api.delete(`/agent/${agentId}`),

  // ===== 对话 =====
  // 与智能体对话（自动使用最新 Agent）
  chat: (data) => api.post('/agent/chat', {
    message: data.message,
    student_id: data.student_id || 'guest',
    session_id: data.session_id,
    files: data.files || null  // 支持多模态：[{type, data}]
  }),

  // Agent 流式对话
  chatStream: (data) => {
    const token = localStorage.getItem('token')
    return fetch('/api/v1/agent/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        message: data.message,
        student_id: data.student_id || 'guest',
        session_id: data.session_id,
        files: data.files || null,
        model: data.model || 'kimi-k2.5',
        temperature: data.temperature,
        max_tokens: data.maxTokens || 4096,
        top_p: data.topP || 0.9,
        frequency_penalty: data.frequencyPenalty || 0,
        presence_penalty: data.presencePenalty || 0,
        use_memory: data.use_memory !== undefined ? data.use_memory : true,
        agent_type: data.agent_type || 'tutor',
        personality: data.personality || 'balanced',
        custom_prompt: data.custom_prompt || ''
      })
    })
  },

  // ===== 工具相关 =====
  // 获取内置工具列表
  listTools: () => api.get('/agent/tools/list'),
  // 获取所有可用工具
  getAvailableTools: () => api.get('/agent/tools/available'),
  // 获取指定类型的工具权限
  getToolPermissions: (agentType) => api.get(`/agent/tools/permissions/${agentType}`),
  // 上传文件到 Agent 工作区
  uploadFile: (sessionId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/agent/tools/upload/${sessionId}`, formData, {
      headers: { 'Content-Type': undefined } // 让浏览器自动设置，包括 boundary
    })
  },
  // 列出会话已上传的文件
  listFiles: (sessionId) => api.get(`/agent/tools/files/${sessionId}`),
  // 知识库检索
  knowledgeSearch: (data) => api.post('/agent/tools/knowledge_search', {
    query: data.query,
    limit: data.limit || 5,
    course_id: data.course_id
  }),
  // Tavily 搜索
  tavilySearch: (data) => api.post('/agent/tools/tavily_search', {
    query: data.query,
    max_results: data.max_results || 5
  }),
  // 阅读工具
  readTool: (data) => api.post('/agent/tools/read', {
    file_path: data.file_path,
    start_line: data.start_line,
    end_line: data.end_line
  }),
  // 编辑工具
  editTool: (data) => api.post('/agent/tools/edit', {
    file_path: data.file_path,
    action: data.action,  // 'create' | 'update' | 'delete'
    content: data.content,
    path: data.path
  }),

  // ===== Agent 类型 =====
  // 获取 Agent 类型列表
  getTypes: () => api.get('/agent/types/list'),

  // ===== 记忆管理 =====
  // 获取会话记忆
  getMemory: (sessionId) => api.get(`/agent/memory/${sessionId}`),
  // 添加记忆
  addMemory: (sessionId, data) => api.post(`/agent/memory/${sessionId}`, {
    content: data.content,
    importance: data.importance || 1.0,
    tags: data.tags || ''
  }),
  // 清除会话记忆
  clearMemory: (sessionId) => api.delete(`/agent/memory/${sessionId}`),

  // ===== 钩子 =====
  // 获取可用钩子
  getHooks: () => api.get('/agent/hooks'),

  // ===== 任务 =====
  // 获取任务列表
  getTasks: () => api.get('/agent/tasks'),
  // 获取任务状态
  getTaskStatus: (taskId) => api.get(`/agent/tasks/${taskId}`),

}

export default api
