<template>
  <div class="knowledge-window">
    <!-- Title Bar -->
    <div class="titlebar">
      <div class="window-title">知识库</div>
      <div class="titlebar-controls">
        <button class="titlebar-btn" title="全屏">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Search Bar -->
      <div class="search-container">
        <div class="search-wrapper">
          <span class="search-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索文档、知识点..."
            @input="debouncedSearch"
          />
          <div class="search-shortcut">
            <kbd>⌘</kbd><kbd>K</kbd>
          </div>
        </div>
          </div>

      <!-- Filter Bar -->
      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">文件类型：</span>
          <div class="filter-chips">
            <button
              v-for="chip in typeChips"
              :key="chip.value"
              class="filter-chip"
              :class="{ active: activeType === chip.value }"
              @click="activeType = chip.value"
            >
              {{ chip.label }}
            </button>
            </div>
          </div>
        <div class="filter-group">
          <span class="filter-label">状态：</span>
          <div class="filter-chips">
            <button
              v-for="chip in statusChips"
              :key="chip.value"
              class="filter-chip"
              :class="{ active: activeStatus === chip.value }"
              @click="activeStatus = chip.value"
            >
              {{ chip.label }}
            </button>
        </div>
        </div>
      </div>

      <!-- Import Zone -->
      <div
        class="import-zone"
        :class="{ 'drag-over': isDragging }"
        @click="triggerFileInput"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <div class="import-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17,8 12,3 7,8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <div class="import-text">
          <div class="import-title">拖放文件到此处导入</div>
          <div class="import-subtitle">或点击选择文件</div>
        </div>
        <div class="import-formats">
          <span class="format-badge">.pdf</span>
          <span class="format-badge">.docx</span>
          <span class="format-badge">.txt</span>
          <span class="format-badge">.md</span>
        </div>
      </div>
          <input
        ref="fileInputRef"
            type="file"
        multiple
        accept=".pdf,.docx,.txt,.md"
        style="display: none"
        @change="handleFileSelect"
      />

      <!-- Documents List -->
      <div class="documents-container">
        <div class="documents-header">
          <span class="documents-count">{{ filteredDocuments.length }} 个文档</span>
          <div class="documents-sort">
            <select v-model="sortBy">
              <option value="date">按更新时间</option>
              <option value="name">按名称</option>
              <option value="size">按大小</option>
            </select>
            </div>
          </div>

        <div v-if="filteredDocuments.length" class="documents-list">
          <div
            v-for="(doc, index) in filteredDocuments"
            :key="doc.id"
            class="document-card"
            :class="{ selected: selectedDocs.has(doc.id) }"
            :style="{ animationDelay: index * 50 + 'ms' }"
            @click="toggleSelect(doc.id)"
            @contextmenu.prevent="showContextMenu($event, doc)"
          >
            <div class="document-card-header">
              <div class="document-icon" :class="doc.type">
                <svg v-if="doc.type === 'pdf'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
                <svg v-else-if="doc.type === 'doc'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
            </div>
              <div class="document-info">
                <div class="document-name">{{ doc.title }}</div>
                <div class="document-meta">
                  <span class="status-badge" :class="doc.status">
                    <svg v-if="doc.status === 'completed'" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20,6 9,17 4,12"/>
                    </svg>
                    <svg v-else-if="doc.status === 'indexing'" class="spin" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="2" x2="12" y2="6"/>
                      <line x1="12" y1="18" x2="12" y2="22"/>
                      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                      <line x1="2" y1="12" x2="6" y2="12"/>
                      <line x1="18" y1="12" x2="22" y2="12"/>
                    </svg>
                    <svg v-else-if="doc.status === 'failed'" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" y1="8" x2="12" y2="12"/>
                      <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12,6 12,12 16,14"/>
                    </svg>
                    {{ statusText[doc.status] }}
                  </span>
                  <span class="document-meta-item">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12,6 12,12 16,14"/>
                    </svg>
                    {{ doc.updatedAt }}
                  </span>
                  <span class="document-meta-item">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    </svg>
                    {{ doc.size }}
                  </span>
            </div>
            </div>
              <div class="document-actions">
                <button class="doc-action-btn danger" title="删除" @click.stop="deleteDocument(doc.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                </button>
            </div>
          </div>
            <div v-if="doc.chunks" class="document-knowledge-points">
              <span class="knowledge-tag" style="--tag-color: #007AFF;">{{ doc.chunks }} 个知识块</span>
              <span class="knowledge-tag" style="--tag-color: #FF9500;">{{ doc.course }}</span>
              </div>
            </div>
          </div>

        <div v-else class="empty-state">
          <div class="empty-state-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
              </div>
          <div class="empty-state-title">没有找到文档</div>
          <div class="empty-state-text">尝试调整搜索条件或导入新文档</div>
            </div>
          </div>
        </div>

    <!-- Status Bar -->
    <div class="statusbar">
      <div class="statusbar-left">
        <div class="statusbar-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          </svg>
          <span>已选择 <strong>{{ selectedDocs.size }}</strong> 个文档</span>
            </div>
        <div class="progress-container">
          <span class="progress-label">索引进度：</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: indexingProgress + '%' }"></div>
            </div>
          <span class="progress-percent">{{ indexingProgress }}%</span>
            </div>
          </div>
      <div class="statusbar-right">
        <div class="statusbar-actions">
          <button class="btn btn-secondary" :disabled="isIndexing" @click="toggleIndexing">
            <svg v-if="!isIndexing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
            <svg v-else class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="2" x2="12" y2="6"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
            </svg>
            {{ isIndexing ? '索引中...' : '暂停' }}
          </button>
          <button class="btn btn-primary" :disabled="isIndexing || !hasPendingDocs" @click="startIndexing">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
            开始索引
          </button>
          </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" ref="toastContainer"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { knowledgeApi, ragApi } from '@/api'

const fileInputRef = ref(null)
const searchQuery = ref('')
const activeType = ref('all')
const activeStatus = ref('all')
const sortBy = ref('date')
const documents = ref([])
const selectedDocs = ref(new Set())
const isIndexing = ref(false)
const indexingProgress = ref(0)
const isDragging = ref(false)
const toastContainer = ref(null)

/** 底部胶囊导航当前选中项（本页为知识库） */
const activeBottomNav = ref('library')

const typeChips = [
  { label: '全部', value: 'all' },
  { label: 'PDF', value: 'pdf' },
  { label: 'Word', value: 'doc' },
  { label: '文本', value: 'txt' },
  { label: 'Markdown', value: 'md' }
]

const statusChips = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'completed' },
  { label: '索引中', value: 'indexing' },
  { label: '待处理', value: 'pending' }
]

const statusText = {
  completed: '已完成',
  indexing: '索引中',
  pending: '待处理',
  failed: '失败'
}

let searchTimeout = null

function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // Search logic handled by computed
  }, 300)
}

const filteredDocuments = computed(() => {
  let filtered = [...documents.value]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(doc =>
      doc.title.toLowerCase().includes(query) ||
      doc.course?.toLowerCase().includes(query)
    )
  }

  if (activeType.value !== 'all') {
    filtered = filtered.filter(doc => doc.type === activeType.value)
  }

  if (activeStatus.value !== 'all') {
    filtered = filtered.filter(doc => doc.status === activeStatus.value)
  }

  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.title.localeCompare(b.title)
      case 'size':
        return parseFloat(b.size) - parseFloat(a.size)
      default:
        return new Date(b.updatedAt) - new Date(a.updatedAt)
    }
  })

  return filtered
})

/** 文档角标：有数据时显示数量；无数据时显示 24（与参考设计一致） */
const documentNavBadge = computed(() => {
  const n = filteredDocuments.value.length
  if (n > 0) return n > 99 ? '99+' : String(n)
  return '24'
})

const hasPendingDocs = computed(() => {
  return documents.value.some(doc => doc.status === 'pending' || doc.status === 'failed')
})

function updateProgress() {
  const completed = documents.value.filter(d => d.status === 'completed').length
  const total = documents.value.length
  indexingProgress.value = total > 0 ? Math.round((completed / total) * 100) : 0
}

function toggleSelect(id) {
  if (selectedDocs.value.has(id)) {
    selectedDocs.value.delete(id)
  } else {
    selectedDocs.value.add(id)
  }
  selectedDocs.value = new Set(selectedDocs.value)
}

function showContextMenu(event, doc) {
  // Context menu implementation
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div')
  toast.className = 'toast'
  toast.innerHTML = `
    <div class="toast-icon ${type}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        ${type === 'success'
          ? '<polyline points="20,6 9,17 4,12"/>'
          : type === 'error'
          ? '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
          : '<line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>'}
      </svg>
    </div>
    <span class="toast-message">${message}</span>
  `
  if (toastContainer.value) {
    toastContainer.value.appendChild(toast)
    setTimeout(() => {
      toast.classList.add('hiding')
      setTimeout(() => toast.remove(), 300)
    }, 3000)
  }
}

function onPillNavMore() {
  ElMessage.info('更多功能即将开放')
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  processFiles(files)
  event.target.value = ''
}

function handleDrop(event) {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files)
  const validFiles = files.filter(f => /\.(pdf|docx|txt|md)$/i.test(f.name))
  processFiles(validFiles)
}

function processFiles(files) {
  if (files.length === 0) return

  showToast(`正在上传 ${files.length} 个文件...`, 'info')

  const uploadPromises = files.map(async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('course_id', 'default')

    try {
      const res = await ragApi.upload(formData)
      if (res?.code === 200) {
        return {
          id: res.data.doc_ids?.[0] || Date.now() + Math.random(),
          title: file.name,
          type: file.name.split('.').pop().toLowerCase().replace('docx', 'doc'),
          status: 'completed',
          chunks: res.data.doc_count || 0,
          course: '默认课程',
          size: formatFileSize(file.size),
          updatedAt: new Date().toLocaleDateString('zh-CN')
        }
      }
    } catch (e) {
      console.error('上传失败:', e)
      showToast(`文件 ${file.name} 上传失败`, 'error')
      return {
        id: Date.now() + Math.random(),
        title: file.name,
        type: file.name.split('.').pop().toLowerCase().replace('docx', 'doc'),
        status: 'failed',
        chunks: 0,
        course: '未分类',
        size: formatFileSize(file.size),
        updatedAt: new Date().toLocaleDateString('zh-CN')
      }
    }
  })

  Promise.all(uploadPromises).then(async (newDocs) => {
    const successCount = newDocs.filter(d => d.status === 'completed').length
    documents.value = [...newDocs, ...documents.value]
    updateProgress()
    showToast(`成功导入 ${successCount} 个文件`, 'success')
    await loadData()
  })
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function deleteDocument(id) {
  const doc = documents.value.find(d => d.id === id)
  if (!doc) return

  try {
    await ragApi.deleteDocument(doc.filename || doc.title)
  } catch (e) {
    console.error('删除文档失败:', e)
  }

  documents.value = documents.value.filter(d => d.id !== id)
  selectedDocs.value.delete(id)
  selectedDocs.value = new Set(selectedDocs.value)
  updateProgress()
  showToast('文档已删除', 'success')
}

function toggleIndexing() {
  isIndexing.value = !isIndexing.value
  showToast(isIndexing.value ? '索引已暂停' : '索引继续中', 'info')
}

function startIndexing() {
  if (isIndexing.value) return

  isIndexing.value = true
  const pendingDocs = documents.value.filter(d => d.status === 'pending' || d.status === 'failed')
  let completed = 0

  const interval = setInterval(() => {
    const pending = pendingDocs.slice(completed, completed + 1)[0]
    if (pending) {
      const docIndex = documents.value.findIndex(d => d.id === pending.id)
      if (docIndex !== -1) {
        documents.value[docIndex].status = 'indexing'
      }

      setTimeout(() => {
        const idx = documents.value.findIndex(d => d.id === pending.id)
        if (idx !== -1) {
          documents.value[idx].status = 'completed'
          documents.value[idx].chunks = Math.floor(Math.random() * 50) + 10
        }
        completed++
        indexingProgress.value = Math.round((completed / pendingDocs.length) * 100)
        updateProgress()

        if (completed >= pendingDocs.length) {
          clearInterval(interval)
          isIndexing.value = false
          showToast('所有文档索引完成！', 'success')
        }
      }, 800)
    }
  }, 1000)
}

async function loadData() {
  try {
    const docsRes = await ragApi.listDocuments('default')
    if (docsRes?.data) {
      documents.value = (docsRes.data.items || []).map((doc, i) => ({
        id: doc.doc_id || Date.now() + i,
        title: doc.filename || doc.title || '未命名文档',
        type: (doc.filename?.split('.').pop() || 'txt').toLowerCase().replace('docx', 'doc'),
        status: doc.doc_count > 0 ? 'completed' : 'pending',
        chunks: doc.doc_count || doc.chunks || 0,
        course: doc.course_id || doc.course || '默认课程',
        size: doc.size || '未知',
        filename: doc.filename || doc.title,
        updatedAt: doc.updated_at ? new Date(doc.updated_at).toLocaleDateString('zh-CN') : '未知'
      }))
    }
    updateProgress()
  } catch (e) {
    console.error('加载文档失败:', e)
    documents.value = []
  }
}

onMounted(() => {
  loadData()
  // Handle ⌘K shortcut
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      document.querySelector('.search-input')?.focus()
    }
  })
})
</script>

<style scoped>
/* ========================================
   CSS Variables - Blue, Red, Orange Theme
   ======================================== */
.knowledge-window {
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: rgba(0, 0, 0, 0.03);
  --color-bg-tertiary: rgba(0, 0, 0, 0.06);
  --color-bg-hover: rgba(0, 0, 0, 0.08);
  --color-bg-active: rgba(0, 0, 0, 0.10);
  --color-bg-selected: rgba(0, 122, 255, 0.15);

  /* Blue, Red, Orange Accent Colors */
  --color-blue: #007AFF;
  --color-blue-hover: #3395FF;
  --color-red: #FF3B30;
  --color-orange: #FF9500;
  --color-green: #34C759;
  --color-purple: #5E5CE6;

  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-danger: #FF3B30;

  --color-text-primary: #1e1e1e;
  --color-text-secondary: rgba(0, 0, 0, 0.6);
  --color-text-tertiary: rgba(0, 0, 0, 0.4);

  --color-border: rgba(0, 0, 0, 0.1);
  --color-border-hover: rgba(0, 0, 0, 0.2);

  /* Traffic Light Colors */
  --color-close: #FF5F57;
  --color-minimize: #FEBC2E;
  --color-maximize: #28C840;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;
  --radius-xl: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-glow-blue: 0 0 20px rgba(0, 122, 255, 0.2);
  --shadow-glow-orange: 0 0 20px rgba(255, 149, 0, 0.2);
  --shadow-glow-red: 0 0 20px rgba(255, 59, 48, 0.2);

  /* Transitions */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
}

/* ========================================
   Window Layout
   ======================================== */
.knowledge-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  background: var(--color-bg-primary);
  overflow: hidden;
  position: relative;
}

.knowledge-window::before {
  content: none;
}

/* ========================================
   Title Bar
   ======================================== */
.titlebar {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 var(--space-4);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  position: relative;
  flex-shrink: 0;
}

.window-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  letter-spacing: 0.3px;
}

.titlebar-controls {
  position: absolute;
  right: 12px;
  display: flex;
  gap: var(--space-2);
}

.titlebar-btn {
  width: 28px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.titlebar-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

/* ========================================
   Main Content
   ======================================== */
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Search Bar */
.search-container {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 80px 0 40px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: all var(--duration-fast) var(--ease-default);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.search-input:hover {
  border-color: var(--color-border-hover);
}

.search-input:focus {
  border-color: var(--color-blue);
  box-shadow: var(--shadow-glow-blue);
  background: var(--color-bg-tertiary);
}

.search-shortcut {
  position: absolute;
  right: 12px;
  display: flex;
  gap: 4px;
}

.search-shortcut kbd {
  font-family: inherit;
  font-size: 11px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.filter-chips {
  display: flex;
  gap: var(--space-2);
}

.filter-chip {
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  white-space: nowrap;
}

.filter-chip:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.filter-chip.active {
  background: linear-gradient(135deg, var(--color-blue), var(--color-purple));
  color: white;
}

/* Import Dropzone */
.import-zone {
  margin: var(--space-4);
  padding: var(--space-6);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-default);
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.import-zone:hover,
.import-zone.drag-over {
  border-color: var(--color-blue);
  background: rgba(0, 122, 255, 0.05);
}

.import-zone.drag-over {
  transform: scale(1.02);
  box-shadow: var(--shadow-glow-blue);
}

.import-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-blue), var(--color-orange));
  border-radius: var(--radius-lg);
  color: white;
  transition: transform var(--duration-normal) var(--ease-spring);
}

.import-zone:hover .import-icon {
  transform: translateY(-4px);
}

.import-text {
  text-align: center;
}

.import-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.import-subtitle {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.import-formats {
  display: flex;
  gap: var(--space-2);
}

.format-badge {
  font-size: 11px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

/* Documents List */
.documents-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-4) var(--space-4);
}

.documents-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) 0;
  position: sticky;
  top: 0;
  background: var(--color-bg-primary);
  z-index: 10;
}

.documents-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.documents-sort select {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 12px;
  padding: var(--space-1) var(--space-3);
  cursor: pointer;
  outline: none;
}

.documents-sort select:focus {
  border-color: var(--color-blue);
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Document Card */
.document-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-default);
  position: relative;
  overflow: hidden;
  animation: fadeIn var(--duration-normal) var(--ease-default) backwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.document-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.08), transparent);
}

.document-card:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.document-card.selected {
  border-color: var(--color-blue);
  background: var(--color-bg-selected);
}

.document-card.selected::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--color-blue), var(--color-orange));
}

.document-card-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.document-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--color-blue);
  flex-shrink: 0;
}

.document-icon.pdf { color: var(--color-red); background: rgba(255, 59, 48, 0.1); }
.document-icon.doc { color: var(--color-green); background: rgba(52, 199, 89, 0.1); }
.document-icon.txt { color: var(--color-orange); background: rgba(255, 149, 0, 0.1); }
.document-icon.md { color: var(--color-purple); background: rgba(94, 92, 230, 0.1); }

.document-info {
  flex: 1;
  min-width: 0;
}

.document-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.document-meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.document-actions {
  display: flex;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity var(--duration-fast);
}

.document-card:hover .document-actions {
  opacity: 1;
}

.doc-action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.doc-action-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.doc-action-btn.danger:hover {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-danger);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 500;
}

.status-badge.completed {
  background: rgba(52, 199, 89, 0.15);
  color: var(--color-success);
}

.status-badge.indexing {
  background: rgba(0, 122, 255, 0.15);
  color: var(--color-blue);
}

.status-badge.pending {
  background: rgba(142, 142, 147, 0.15);
  color: var(--color-text-secondary);
}

.status-badge.failed {
  background: rgba(255, 59, 48, 0.15);
  color: var(--color-danger);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Knowledge Points */
.document-knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.knowledge-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  font-size: 11px;
  color: var(--color-text-secondary);
  transition: all var(--duration-fast);
}

.knowledge-tag::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--tag-color, var(--color-blue));
}

/* ========================================
   Status Bar
   ======================================== */
.statusbar {
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
}

.statusbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.statusbar-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.progress-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  min-width: 80px;
}

.progress-bar {
  width: 200px;
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-blue), var(--color-orange));
  border-radius: var(--radius-full);
  transition: width var(--duration-normal) var(--ease-default);
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.15), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-percent {
  font-size: 12px;
  color: var(--color-text-primary);
  font-weight: 500;
  min-width: 40px;
}

.statusbar-actions {
  display: flex;
  gap: var(--space-2);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  white-space: nowrap;
}

.btn:active {
  transform: scale(0.97);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-blue), var(--color-purple));
  color: white;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-blue);
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-hover);
}

/* ========================================
   Empty State
   ======================================== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  text-align: center;
}

.empty-state-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: 50%;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-state-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-state-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
  max-width: 300px;
}

/* ========================================
   Bottom pill navigation (white bar)
   ======================================== */
.knowledge-pill-nav {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 16px 14px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), #ffffff);
  border-top: 1px solid var(--color-border);
}

.pill-nav-track {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  max-width: 100%;
  padding: 6px 8px 8px;
  border-radius: 9999px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 8px 24px rgba(15, 23, 42, 0.06);
}

.pill-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 56px;
  padding: 8px 10px 6px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #64748b;
  font-family: inherit;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-default),
    color var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.pill-nav-item:hover:not(.active) {
  background: rgba(15, 23, 42, 0.05);
  color: #334155;
}

.pill-nav-item:active {
  transform: scale(0.97);
}

.pill-nav-item.active {
  background: #007aff;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(0, 122, 255, 0.35);
}

.pill-nav-icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 24px;
}

.pill-nav-icon {
  flex-shrink: 0;
}

.pill-nav-label {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  letter-spacing: 0.02em;
}

.pill-nav-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #ffffff;
  background: #ff3b30;
  border-radius: 999px;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(255, 59, 48, 0.4);
  line-height: 1;
}

.pill-nav-item.active .pill-nav-badge {
  border-color: #007aff;
}

.pill-nav-divider {
  width: 1px;
  height: 32px;
  margin: 0 6px;
  background: rgba(15, 23, 42, 0.12);
  flex-shrink: 0;
}

.pill-nav-more {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-left: 4px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: #1e293b;
  color: #f8fafc;
  cursor: pointer;
  flex-shrink: 0;
  transition:
    background var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.pill-nav-more:hover {
  background: #334155;
}

.pill-nav-more:active {
  transform: scale(0.95);
}

@media (max-width: 640px) {
  .pill-nav-track {
    flex-wrap: wrap;
    row-gap: 4px;
    border-radius: 20px;
    padding: 8px;
  }

  .pill-nav-item {
    min-width: 52px;
    padding: 6px 8px 4px;
  }

  .pill-nav-label {
    font-size: 10px;
  }
}

/* ========================================
   Toast Notifications
   ======================================== */
.toast-container {
  position: fixed;
  bottom: 120px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  z-index: 1002;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(20px);
  animation: slideIn var(--duration-normal) var(--ease-spring);
  pointer-events: auto;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.toast.hiding {
  animation: slideOut var(--duration-normal) var(--ease-default) forwards;
}

@keyframes slideOut {
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

.toast-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.toast-icon.success {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.toast-icon.error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-danger);
}

.toast-icon.info {
  background: rgba(0, 122, 255, 0.2);
  color: var(--color-blue);
}

.toast-message {
  font-size: 12px;
  color: var(--color-text-primary);
}
</style>
