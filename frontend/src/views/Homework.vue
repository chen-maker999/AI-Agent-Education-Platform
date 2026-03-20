<template>
  <div class="homework-page">
    <!-- 页面头部 -->
    <div class="page-header-custom">
      <div class="header-content">
        <div class="header-text">
          <h1>作业管理</h1>
          <p v-if="isTeacher">上传、管理和批改学生作业，生成练习文件</p>
          <p v-else>查看和提交作业</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="showGenerateModal = true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            生成练习
          </button>
          <button class="btn btn-primary" @click="showUploadModal = true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            提交作业
          </button>
        </div>
      </div>
    </div>

    <!-- 生成练习弹窗 -->
    <div v-if="showGenerateModal" class="modal-overlay" @click.self="showGenerateModal = false">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>生成练习文件</h3>
          <button class="close-btn" @click="showGenerateModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>练习标题</label>
            <input type="text" v-model="generateForm.title" placeholder="输入练习标题（可选）" class="input-field">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>知识库/课程</label>
              <select v-model="generateForm.course_id" class="input-field">
                <option value="">选择知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.kb_id" :value="kb.kb_id">
                  {{ kb.name || kb.kb_id }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>题目数量</label>
              <select v-model="generateForm.exercise_count" class="input-field">
                <option :value="5">5题</option>
                <option :value="10">10题</option>
                <option :value="15">15题</option>
                <option :value="20">20题</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>难度级别</label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="generateForm.difficulty" value="easy">
                  <span>简单</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="generateForm.difficulty" value="medium">
                  <span>中等</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="generateForm.difficulty" value="hard">
                  <span>困难</span>
                </label>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>题型（可多选）</label>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="generateForm.exercise_types" value="choice">
                <span>选择题</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="generateForm.exercise_types" value="blank">
                <span>填空题</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="generateForm.exercise_types" value="short_answer">
                <span>简答题</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="generateForm.exercise_types" value="coding">
                <span>编程题</span>
              </label>
            </div>
          </div>
          <div class="info-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <p>练习将根据所选知识库的文档内容自动生成，生成后可在下方查看并下载PDF文件。</p>
          </div>
          <div v-if="generating" class="generating-tip">
            <div class="spinner"></div>
            <span>正在生成练习，请稍候...</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showGenerateModal = false">取消</button>
          <button class="btn btn-outline" @click="generateInBackground" :disabled="generating || !generateForm.course_id">
            {{ generating ? '生成中...' : '后台生成' }}
          </button>
          <button class="btn btn-primary" @click="generateWorksheet" :disabled="generating || !generateForm.course_id">
            {{ generating ? '生成中...' : '立即生成' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 练习预览弹窗 -->
    <div v-if="showPreviewModal" class="modal-overlay" @click.self="showPreviewModal = false">
      <div class="modal-content modal-preview">
        <div class="modal-header">
          <h3>{{ previewData.title || '练习预览' }}</h3>
          <button class="close-btn" @click="showPreviewModal = false">&times;</button>
        </div>
        <div class="modal-body preview-body">
          <div v-if="previewLoading" class="preview-loading">
            <div class="spinner"></div>
            <span>加载中...</span>
          </div>
          <template v-else>
          <div class="preview-info">
            <span class="info-tag">{{ previewData.exercise_count || 0 }}题</span>
            <span class="info-tag difficulty-tag">{{ getDifficultyText(previewData.difficulty) }}</span>
          </div>
          <div class="exercise-list">
            <div v-for="(ex, idx) in previewData.exercises" :key="idx" class="exercise-item">
              <div class="exercise-header">
                <span class="exercise-num">{{ idx + 1 }}.</span>
                <span class="exercise-type">[{{ getExerciseTypeName(ex.exercise_type) }}]</span>
              </div>
              <div class="exercise-question">{{ ex.question }}</div>
              <div v-if="ex.options" class="exercise-options">
                <div v-for="(opt, optIdx) in ex.options" :key="optIdx" class="option-item">{{ opt }}</div>
              </div>
              <div class="exercise-answer">
                <strong>答案：</strong>{{ ex.answer }}
              </div>
            </div>
          </div>
          </template>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPreviewModal = false">关闭</button>
          <button class="btn btn-primary" @click="downloadWorksheet(previewData.worksheet_id)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            下载PDF
          </button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card-custom" v-for="stat in stats" :key="stat.title">
        <div class="stat-icon-wrapper" :style="{ background: stat.gradient }">
          <component :is="stat.icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.title }}</span>
        </div>
      </div>
    </div>

    <div class="content-card-modern">
      <div class="card-header-modern">
        <div class="filter-tabs-modern">
          <button :class="['tab-modern', { active: filter === 'all' }]" @click="filter = 'all'">
            <span class="tab-dot" v-if="filter === 'all'"></span>
            全部
          </button>
          <button :class="['tab-modern', { active: filter === 'pending' }]" @click="filter = 'pending'">
            <span class="tab-dot" v-if="filter === 'pending'"></span>
            待批改
          </button>
          <button :class="['tab-modern', { active: filter === 'reviewed' }]" @click="filter = 'reviewed'">
            <span class="tab-dot" v-if="filter === 'reviewed'"></span>
            已批改
          </button>
          <button :class="['tab-modern', { active: filter === 'worksheets' }]" @click="filter = 'worksheets'; loadWorksheets()">
            <span class="tab-dot" v-if="filter === 'worksheets'"></span>
            练习文件
          </button>
        </div>
        <div class="search-box-modern">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input type="text" placeholder="搜索作业..." v-model="searchQuery">
        </div>
      </div>

      <div class="homework-table-modern">
        <!-- 作业列表 -->
        <table v-if="filter !== 'worksheets'">
          <thead>
            <tr>
              <th>文件名</th>
              <th>上传者</th>
              <th>课程</th>
              <th>上传时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="hw in filteredHomework" :key="hw.id">
              <td>
                <div class="file-info">
                  <div class="file-icon-wrapper">
                    <svg v-if="hw.type === 'pdf'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                  </div>
                  <span class="file-name">{{ hw.filename }}</span>
                </div>
              </td>
              <td>
                <div class="user-cell">
                  <div class="user-avatar-small">{{ hw.uploader.charAt(0) }}</div>
                  {{ hw.uploader }}
                </div>
              </td>
              <td><span class="course-tag">{{ hw.course }}</span></td>
              <td class="time-cell">{{ hw.uploadTime }}</td>
              <td>
                <span :class="['status-badge-modern', hw.status]">
                  <span class="status-dot"></span>
                  {{ hw.status === 'pending' ? '待批改' : '已批改' }}
                </span>
              </td>
              <td>
                <div class="action-buttons-modern">
                  <button class="action-btn-modern" @click="downloadHomework(hw)" title="下载">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                  </button>
                  <button class="action-btn-modern edit" @click="reviewHomework(hw)" title="批改" v-if="isTeacher">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="action-btn-modern delete" @click="deleteHomework(hw)" title="删除" v-if="isTeacher">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 练习文件列表 -->
        <table v-else>
          <thead>
            <tr>
              <th>标题</th>
              <th>课程</th>
              <th>题目数</th>
              <th>题型</th>
              <th>难度</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ws in worksheetList" :key="ws.worksheet_id">
              <td>
                <div class="file-info">
                  <div class="file-icon-wrapper worksheet-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                    </svg>
                  </div>
                  <span class="file-name">{{ ws.title }}</span>
                </div>
              </td>
              <td><span class="course-tag">{{ ws.course || '通用' }}</span></td>
              <td>{{ ws.exercise_count }}题</td>
              <td>
                <span class="exercise-type-tag">{{ formatExerciseType(ws.exercise_type) }}</span>
              </td>
              <td>
                <span :class="['difficulty-badge', ws.difficulty]">
                  {{ getDifficultyText(ws.difficulty) }}
                </span>
              </td>
              <td class="time-cell">{{ formatDate(ws.created_at) }}</td>
              <td>
                <div class="action-buttons-modern">
                  <button class="action-btn-modern preview" @click="previewWorksheet(ws)" title="预览">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                  </button>
                  <button class="action-btn-modern" @click="downloadWorksheet(ws.worksheet_id)" title="下载">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                  </button>
                  <button class="action-btn-modern delete" @click="deleteWorksheet(ws.worksheet_id)" title="删除" v-if="isTeacher">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="worksheetList.length === 0">
              <td colspan="7" class="empty-cell">
                <div class="empty-state-inline">
                  <p>暂无练习文件</p>
                  <button class="btn-link" @click="showGenerateModal = true">点击生成</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isTeacher ? '上传作业' : '提交作业' }}</h3>
          <button class="close-btn" @click="showUploadModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <p>拖拽文件到此处，或 <label for="file-input">点击选择</label></p>
            <span class="hint">支持 PDF、DOC、DOCX 格式</span>
            <input type="file" id="file-input" @change="handleFileSelect" hidden accept=".pdf,.doc,.docx">
          </div>
          <div v-if="selectedFile" class="selected-file">
            <span>{{ selectedFile.name }}</span>
            <button @click="selectedFile = null">&times;</button>
          </div>
          <div class="form-group">
            <label>课程</label>
            <select v-model="uploadForm.course">
              <option value="">选择课程</option>
              <option value="python">Python编程</option>
              <option value="java">Java开发</option>
              <option value="algorithm">算法设计</option>
            </select>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="uploadForm.note" placeholder="添加备注信息（可选）" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showUploadModal = false">取消</button>
          <button class="btn btn-primary" @click="uploadHomework" :disabled="uploading">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { homeworkApi, worksheetApi, ragApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const BookIcon = {
  template: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>`
}
const ClockIcon = {
  template: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>`
}
const CheckIcon = {
  template: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
  </svg>`
}
const UploadIcon = {
  template: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
  </svg>`
}
const WorksheetIcon = {
  template: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
  </svg>`
}

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.user?.role === 'teacher' || authStore.user?.role === 'admin')

const filter = ref('all')
const searchQuery = ref('')
const showUploadModal = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadForm = ref({ course: '', note: '' })

// 练习文件相关状态
const showGenerateModal = ref(false)
const showPreviewModal = ref(false)
const generating = ref(false)
const previewLoading = ref(false)
const knowledgeBases = ref([])
const worksheetList = ref([])
const previewData = ref({})

const generateForm = ref({
  title: '',
  course_id: '',
  exercise_count: 5,
  difficulty: 'medium',
  exercise_types: ['choice']
})

const stats = ref([
  { title: '总作业数', value: '0', icon: 'BookIcon', gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
  { title: '待批改', value: '0', icon: 'ClockIcon', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
  { title: '已批改', value: '0', icon: 'CheckIcon', gradient: 'linear-gradient(135deg, #10b981, #34d399)' },
  { title: '本周上传', value: '0', icon: 'UploadIcon', gradient: 'linear-gradient(135deg, #3b82f6, #60a5fa)' }
])

const homeworkList = ref([])

const loadHomeworkList = async () => {
  try {
    const res = await homeworkApi.list({ page: 1, page_size: 100 })
    if (res.code === 200) {
      homeworkList.value = res.data.items || res.data || []
      updateStats()
    }
  } catch (error) {
    console.error('加载作业列表失败:', error)
  }
}

const loadStats = async () => {
  try {
    const res = await homeworkApi.statistics()
    if (res.code === 200 && res.data) {
      const data = res.data
      stats.value = [
        { title: '总作业数', value: String(data.total_files || 0), icon: 'BookIcon', gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
        { title: '待批改', value: String(data.by_status?.pending || 0), icon: 'ClockIcon', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
        { title: '已批改', value: String(data.by_status?.reviewed || data.by_status?.uploaded || 0), icon: 'CheckIcon', gradient: 'linear-gradient(135deg, #10b981, #34d399)' },
        { title: '本周上传', value: '0', icon: 'UploadIcon', gradient: 'linear-gradient(135deg, #3b82f6, #60a5fa)' }
      ]
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const updateStats = () => {
  const total = homeworkList.value.length
  const pending = homeworkList.value.filter(h => h.status === 'pending').length
  const reviewed = homeworkList.value.filter(h => h.status === 'reviewed').length
  stats.value = [
    { title: '总作业数', value: String(total), icon: 'BookIcon', gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
    { title: '待批改', value: String(pending), icon: 'ClockIcon', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
    { title: '已批改', value: String(reviewed), icon: 'CheckIcon', gradient: 'linear-gradient(135deg, #10b981, #34d399)' },
    { title: '本周上传', value: '0', icon: 'UploadIcon', gradient: 'linear-gradient(135deg, #3b82f6, #60a5fa)' }
  ]
}

onMounted(() => {
  loadHomeworkList()
  loadStats()
  loadKnowledgeBases()
})

const filteredHomework = computed(() => {
  let list = homeworkList.value
  if (filter.value !== 'all') {
    list = list.filter(h => h.status === filter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(h => h.filename.toLowerCase().includes(q) || h.uploader.includes(q))
  }
  return list
})

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file) selectedFile.value = file
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) selectedFile.value = file
}

const uploadHomework = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('homework_id', Date.now().toString())
    formData.append('student_id', 'current_user')
    if (uploadForm.value.course) formData.append('course', uploadForm.value.course)
    if (uploadForm.value.note) formData.append('note', uploadForm.value.note)

    const res = await homeworkApi.upload(formData)
    if (res.code === 200) {
      ElMessage.success('上传成功')
      showUploadModal.value = false
      selectedFile.value = null
      uploadForm.value = { course: '', note: '' }
      loadHomeworkList()
    }
  } catch (error) {
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}

const downloadHomework = async (hw) => {
  try {
    const res = await homeworkApi.download(hw.homework_id || hw.id)
    if (res.code === 200 && res.data.download_url) {
      window.open(res.data.download_url, '_blank')
    }
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const reviewHomework = async (hw) => {
  try {
    await homeworkApi.updateStatus(hw.homework_id || hw.id, 'reviewed')
    ElMessage.success('批改完成')
    loadHomeworkList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteHomework = async (hw) => {
  try {
    await homeworkApi.delete(hw.homework_id || hw.id)
    ElMessage.success('删除成功')
    loadHomeworkList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// ==================== 练习文件相关方法 ====================

// 加载知识库列表 - 从 RAG 知识库获取文档
const loadKnowledgeBases = async () => {
  try {
    const res = await ragApi.listDocuments('default', { allCourses: true })
    if (res.code === 200) {
      const items = res.data?.items || []
      // 按课程分组
      const courseMap = new Map()
      items.forEach(item => {
        const courseId = item.course_id || 'default'
        if (!courseMap.has(courseId)) {
          courseMap.set(courseId, {
            kb_id: courseId,
            name: courseId === 'default' ? '默认知识库' : courseId,
            doc_count: 0
          })
        }
        const course = courseMap.get(courseId)
        course.doc_count += item.doc_count || 1
      })
      knowledgeBases.value = Array.from(courseMap.values())
    }
  } catch (error) {
    console.error('加载知识库失败:', error)
    knowledgeBases.value = [{ kb_id: 'default', name: '默认知识库', doc_count: 0 }]
  }
}

// 加载练习文件列表
const loadWorksheets = async (courseId = null) => {
  try {
    const params = { page: 1, page_size: 100 }
    if (courseId) {
      params.course_id = courseId
    }
    console.log('[Homework] 加载练习文件, params:', params)
    const res = await worksheetApi.list(params)
    console.log('[Homework] 练习文件返回:', res)
    if (res.code === 200) {
      worksheetList.value = res.data?.items || []
      console.log('[Homework] 设置 worksheetList:', worksheetList.value.length, '条')
    }
  } catch (error) {
    console.error('加载练习文件失败:', error)
    worksheetList.value = []
  }
}

// 生成练习文件
const generateWorksheet = async () => {
  if (!generateForm.value.course_id) {
    ElMessage.warning('请选择知识库')
    return
  }
  if (generateForm.value.exercise_types.length === 0) {
    ElMessage.warning('请至少选择一种题型')
    return
  }

  generating.value = true
  try {
    const userId = authStore.user?.id || authStore.user?.user_id || 'default'
    const payload = {
      course_id: generateForm.value.course_id,
      title: generateForm.value.title || `练习题_${new Date().toLocaleDateString()}`,
      exercise_count: generateForm.value.exercise_count,
      difficulty: generateForm.value.difficulty,
      exercise_types: generateForm.value.exercise_types,
      created_by: userId
    }
    console.log('[Homework] 开始生成练习, payload:', payload)
    const res = await worksheetApi.generate(payload)
    console.log('[Homework] 生成练习返回:', res)

    if (res.code === 200) {
      ElMessage.success('练习文件生成成功')
      showGenerateModal.value = false
      // 重置表单
      const selectedCourse = generateForm.value.course_id
      generateForm.value = {
        title: '',
        course_id: selectedCourse,
        exercise_count: 5,
        difficulty: 'medium',
        exercise_types: ['choice']
      }
      // 切换到练习文件标签并刷新列表
      filter.value = 'worksheets'
      // 使用 nextTick 确保 DOM 更新后再刷新
      setTimeout(() => {
        loadWorksheets(selectedCourse)
      }, 100)
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error) {
    console.error('生成练习失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '生成失败')
  } finally {
    generating.value = false
  }
}

// 后台生成练习（不阻塞，可关闭弹窗）
const generateInBackground = async () => {
  if (!generateForm.value.course_id) {
    ElMessage.warning('请选择知识库')
    return
  }
  if (generateForm.value.exercise_types.length === 0) {
    ElMessage.warning('请至少选择一种题型')
    return
  }

  generating.value = true
  const selectedCourse = generateForm.value.course_id

  try {
    const userId = authStore.user?.id || authStore.user?.user_id || 'default'
    const payload = {
      course_id: generateForm.value.course_id,
      title: generateForm.value.title || `练习题_${new Date().toLocaleDateString()}`,
      exercise_count: generateForm.value.exercise_count,
      difficulty: generateForm.value.difficulty,
      exercise_types: generateForm.value.exercise_types,
      created_by: userId
    }

    // 关闭弹窗
    showGenerateModal.value = false
    ElMessage.info('练习正在后台生成中，完成后会显示在列表中')

    // 重置表单
    generateForm.value = {
      title: '',
      course_id: selectedCourse,
      exercise_count: 5,
      difficulty: 'medium',
      exercise_types: ['choice']
    }

    // 发送请求但不等待结果
    worksheetApi.generate(payload).then(res => {
      if (res.code === 200) {
        ElMessage.success('练习文件生成成功')
        // 刷新列表
        loadWorksheets(selectedCourse)
      } else {
        ElMessage.error(res.message || '生成失败')
      }
      generating.value = false
    }).catch(error => {
      console.error('后台生成失败:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '生成失败')
      generating.value = false
    })
  } catch (error) {
    console.error('后台生成失败:', error)
    ElMessage.error('后台生成失败')
    generating.value = false
  }
}

// 预览练习
const previewWorksheet = async (ws) => {
  previewLoading.value = true
  showPreviewModal.value = true
  previewData.value = {}
  try {
    const res = await worksheetApi.preview(ws.worksheet_id)
    if (res.code === 200) {
      previewData.value = res.data
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
    showPreviewModal.value = false
  } finally {
    previewLoading.value = false
  }
}

// 下载练习文件
const downloadWorksheet = async (worksheetId) => {
  try {
    const response = await worksheetApi.download(worksheetId)
    // 创建下载链接
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `练习题_${worksheetId}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    // 尝试通过URL直接打开
    ElMessage.info('正在打开下载链接...')
    window.open(`/api/v1/worksheet/${worksheetId}/download`, '_blank')
  }
}

// 删除练习文件
const deleteWorksheet = async (worksheetId) => {
  try {
    await worksheetApi.delete(worksheetId)
    ElMessage.success('删除成功')
    loadWorksheets()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 格式化题型
const formatExerciseType = (type) => {
  if (!type) return '-'
  const typeMap = {
    'choice': '选择',
    'blank': '填空',
    'short_answer': '简答',
    'coding': '编程'
  }
  return type.split('/').map(t => typeMap[t] || t).join('/')
}

// 获取题型名称
const getExerciseTypeName = (type) => {
  const typeMap = {
    'choice': '选择题',
    'blank': '填空题',
    'short_answer': '简答题',
    'coding': '编程题'
  }
  return typeMap[type] || '题目'
}

// 获取难度文本
const getDifficultyText = (difficulty) => {
  const map = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  }
  return map[difficulty] || '中等'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.homework-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 - 渐变背景 */
.page-header-custom {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 32px 36px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}

.page-header-custom::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 300px;
  height: 300px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.page-header-custom::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: 10%;
  width: 200px;
  height: 200px;
  background: rgba(255,255,255,0.08);
  border-radius: 50%;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.header-text h1 {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin-bottom: 6px;
}

.header-text p {
  color: rgba(255,255,255,0.85);
  font-size: 15px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions .btn {
  padding: 8px 16px;
  font-size: 13px;
  min-width: 100px;
}

.header-actions .btn-primary {
  background: white;
  color: #667eea;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
}

.header-actions .btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

/* 统计卡片 - 现代风格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card-custom {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.stat-card-custom:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}

/* 练习文件图标 */
.worksheet-icon {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
}

/* 练习文件表格样式 */
.exercise-type-tag {
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
}

.difficulty-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.difficulty-badge.easy {
  background: #dcfce7;
  color: #16a34a;
}

.difficulty-badge.medium {
  background: #fef3c7;
  color: #d97706;
}

.difficulty-badge.hard {
  background: #fee2e2;
  color: #dc2626;
}

/* 空状态 */
.empty-state-inline {
  padding: 40px;
  text-align: center;
}

.empty-state-inline p {
  color: #9ca3af;
  margin-bottom: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}

.btn-link:hover {
  text-decoration: underline;
}

.empty-cell {
  padding: 20px;
}

/* 大尺寸弹窗 */
.modal-large {
  max-width: 600px;
}

.modal-preview {
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.preview-body {
  overflow-y: auto;
  max-height: calc(90vh - 150px);
}

.preview-info {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.info-tag {
  padding: 6px 14px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 13px;
  color: #4b5563;
}

.difficulty-tag {
  background: #fef3c7;
  color: #d97706;
}

/* 预览加载样式 */
.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px;
  color: #666;
}

.preview-loading .spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #667eea30;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 练习列表样式 */
.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.exercise-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.exercise-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.exercise-num {
  font-weight: 600;
  color: #1a1a2e;
}

.exercise-type {
  font-size: 12px;
  color: #6b7280;
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 4px;
}

.exercise-question {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin-bottom: 12px;
}

.exercise-options {
  margin-left: 10px;
}

.option-item {
  font-size: 13px;
  color: #4b5563;
  padding: 4px 0;
}

.exercise-answer {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e5e7eb;
  font-size: 13px;
  color: #059669;
}

/* 生成提示样式 */
.generating-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea20, #764ba220);
  border: 1px solid #667eea40;
  border-radius: 8px;
  color: #667eea;
  font-size: 14px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #667eea30;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 表单样式 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #374151;
}

.input-field {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s;
  background: white;
}

.input-field:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

/* 单选按钮组 */
.radio-group {
  display: flex;
  gap: 20px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
}

.radio-item input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
  padding: 8px 14px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.checkbox-item:hover {
  border-color: #3b82f6;
}

.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox-item input:checked + span {
  color: #3b82f6;
  font-weight: 500;
}

/* 信息提示框 */
.info-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: #eff6ff;
  border-radius: 10px;
  border: 1px solid #bfdbfe;
}

.info-box svg {
  color: #3b82f6;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-box p {
  font-size: 13px;
  color: #1e40af;
  line-height: 1.5;
  margin: 0;
}

/* 预览按钮样式 */
.action-btn-modern.preview {
  color: #8b5cf6;
}

.action-btn-modern.preview:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #f5f3ff;
}

/* 按钮次要样式 */
.btn-secondary {
  background: white;
  color: #4b5563;
  border: 1px solid #e5e7eb;
  padding: 12px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f0f7ff;
}

/* 内容卡片 - 现代风格 */
.content-card-modern {
  background: white;
  border-radius: 20px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid #f1f5f9;
}

.filter-tabs-modern {
  display: flex;
  gap: 4px;
  background: #f8fafc;
  padding: 4px;
  border-radius: 12px;
}

.tab-modern {
  padding: 10px 20px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-modern:hover {
  color: #1a1a2e;
}

.tab-modern.active {
  background: white;
  color: #3b82f6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.tab-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
}

.search-box-modern {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  width: 260px;
  transition: all 0.2s;
}

.search-box-modern:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.search-box-modern svg {
  color: #94a3b8;
  flex-shrink: 0;
}

.search-box-modern input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
  color: #1a1a2e;
}

.search-box-modern input::placeholder {
  color: #94a3b8;
}

/* 表格样式 */
.homework-table-modern {
  overflow-x: auto;
}

.homework-table-modern table {
  width: 100%;
  border-collapse: collapse;
}

.homework-table-modern th,
.homework-table-modern td {
  padding: 18px 24px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.homework-table-modern th {
  background: #fafbfc;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.homework-table-modern td {
  font-size: 14px;
  color: #374151;
}

.homework-table-modern tr:hover {
  background: #fafbfc;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
}

.file-name {
  font-weight: 500;
  color: #1a1a2e;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 13px;
}

.course-tag {
  padding: 4px 12px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 13px;
  color: #475569;
}

.time-cell {
  color: #64748b;
  font-size: 13px;
}

/* 状态标签 - 现代风格 */
.status-badge-modern {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge-modern.pending {
  background: #fef3c7;
  color: #d97706;
}

.status-badge-modern.pending .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d97706;
}

.status-badge-modern.reviewed {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge-modern.reviewed .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #16a34a;
}

/* 操作按钮 - 现代风格 */
.action-buttons-modern {
  display: flex;
  gap: 8px;
}

.action-btn-modern {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s;
}

.action-btn-modern:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f0f7ff;
}

.action-btn-modern.edit:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #f5f3ff;
}

.action-btn-modern.delete:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: #fef2f2;
}

/* 弹窗样式 - 现代风格 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 520px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid #f1f5f9;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8fafc;
  border-radius: 10px;
  font-size: 22px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #1a1a2e;
}

.modal-body {
  padding: 28px;
}

.upload-area {
  border: 2px dashed #e2e8f0;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafbfc;
}

.upload-area:hover {
  border-color: #3b82f6;
  background: #f0f7ff;
}

.upload-area svg {
  color: #94a3b8;
  margin-bottom: 16px;
}

.upload-area p {
  margin-bottom: 8px;
  color: #374151;
  font-size: 15px;
}

.upload-area label {
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}

.upload-area .hint {
  font-size: 13px;
  color: #94a3b8;
}

.selected-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #f0f7ff;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #bfdbfe;
}

.selected-file span {
  color: #1e40af;
  font-weight: 500;
}

.selected-file button {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  color: #64748b;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.selected-file button:hover {
  background: #dbeafe;
  color: #1e40af;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #374151;
}

.form-group select,
.form-group textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.2s;
  background: white;
}

.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 28px;
  border-top: 1px solid #f1f5f9;
}

.btn {
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
  color: #1a1a2e;
}

.btn-outline {
  background: transparent;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover {
  background: #667eea10;
}

.btn-outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header-custom {
    padding: 24px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-text h1 {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .card-header-modern {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .search-box-modern {
    width: 100%;
  }

  .filter-tabs-modern {
    width: 100%;
    overflow-x: auto;
  }

  .homework-table-modern {
    font-size: 13px;
  }

  .homework-table-modern th,
  .homework-table-modern td {
    padding: 12px 16px;
  }
}
</style>
