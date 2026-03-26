<template>
  <div class="homework-page">
    <!-- macOS Window Card -->
    <div class="mac-window" role="application" aria-label="作业中心">

      <!-- Title Bar -->
      <header class="titlebar">
        <div class="titlebar-title">作业中心 — {{ isTeacher ? 'TEACHER MODE' : 'STUDENT MODE' }}</div>
        <span class="titlebar-hint">{{ isTeacher ? '批改队列与文档预览' : '作业列表与批注回看' }}</span>
      </header>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="segmented" role="tablist" aria-label="视图模式">
          <button
            v-for="item in viewModes"
            :key="item.value"
            type="button"
            :aria-pressed="activeView === item.value ? 'true' : 'false'"
            @click="activeView = item.value"
          >
            {{ item.label }}
          </button>
        </div>

        <button type="button" class="tb-btn" title="上传作业" @click="showUpload = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17,8 12,3 7,8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ isTeacher ? '上传示例' : '提交作业' }}
        </button>

        <div class="toolbar-spacer"></div>

        <!-- Search -->
        <div class="search-field">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>
          </svg>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="搜索文件名、课程…"
            autocomplete="off"
          />
        </div>

        <button type="button" class="tb-btn" title="同步数据" @click="loadHomework">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          同步
        </button>
      </div>

      <!-- Main Content: Two-column layout -->
      <div class="split-root">

        <!-- MIDDLE: Homework List -->
        <section class="canvas-pane" aria-label="作业列表">
          <div class="canvas-toolbar">
            <span class="canvas-title">作业列表</span>
            <span class="hint">{{ filteredHomework.length }} 项 · 点击查看详情</span>
          </div>

          <div class="canvas-body">
            <div class="canvas-grid" aria-hidden="true"></div>

            <!-- Homework Items -->
            <div v-if="filteredHomework.length" class="homework-list">
              <button
                v-for="(item, index) in filteredHomework"
                :key="item.id"
                type="button"
                class="homework-card"
                :class="{ active: selectedHomework?.id === item.id }"
                :style="{ animationDelay: index * 50 + 'ms' }"
                @click="selectedHomework = item"
              >
                <div class="homework-card-icon" :class="item.status">
                  <svg v-if="item.status === 'reviewed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                  </svg>
                  <svg v-else-if="item.status === 'pending'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                  </svg>
                </div>

                <div class="homework-card-content">
                  <div class="homework-card-title">{{ item.filename }}</div>
                  <div class="homework-card-meta">
                    <span class="meta-tag">{{ item.course }}</span>
                    <span class="meta-tag">{{ item.uploader }}</span>
                  </div>
                  <div class="homework-card-time">{{ item.uploadTime }}</div>
                </div>

                <div class="homework-card-status">
                  <span class="status-badge" :class="item.status">
                    {{ item.status === 'reviewed' ? '已处理' : '待处理' }}
                  </span>
                  <span v-if="item.score !== null" class="score-badge">{{ item.score }}分</span>
                </div>
              </button>
            </div>

            <!-- Empty State -->
            <div v-else class="canvas-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
              </svg>
              <h3>暂无作业</h3>
              <p>{{ activeFilter === 'all' ? '当前列表为空，点击上方按钮提交作业' : '该筛选条件下没有作业' }}</p>
            </div>
          </div>
        </section>

        <!-- RIGHT: Inspector - Detail & Preview -->
        <aside class="inspector" aria-label="作业详情">
          <div class="inspector-header">{{ isTeacher ? '批改与预览' : '作业详情' }}</div>
          <div class="inspector-body">

            <div v-if="!selectedHomework" class="inspector-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <h4>选择一份作业</h4>
              <p>从左侧列表中选择作业后，这里会展示详细信息、预览区和批注轨。</p>
            </div>

            <div v-else class="homework-detail">
              <div class="group-box">
                <h5>基本信息</h5>
                <div class="row"><span>文件名</span><span>{{ selectedHomework.filename }}</span></div>
                <div class="row"><span>课程</span><span>{{ selectedHomework.course }}</span></div>
                <div class="row"><span>上传者</span><span>{{ selectedHomework.uploader }}</span></div>
                <div class="row"><span>时间</span><span>{{ selectedHomework.uploadTime }}</span></div>
                <div class="row">
                  <span>状态</span>
                  <span class="status-badge" :class="selectedHomework.status">
                    {{ selectedHomework.status === 'reviewed' ? '已处理' : '待处理' }}
                  </span>
                </div>
              </div>

              <!-- Preview Area -->
              <div class="group-box preview-box">
                <h5>{{ isTeacher ? '文档预览' : '作业内容' }}</h5>
                <div class="preview-placeholder">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                  </svg>
                  <p>{{ isTeacher ? 'PDF / 图片 / 代码预览区域' : '学生提交内容展示区' }}</p>
                  <span class="preview-hint">预留完整画布用于文档预览、错误定位和段落级批注</span>
                </div>
              </div>

              <!-- Comments Rail -->
              <div class="group-box">
                <h5>{{ isTeacher ? '批注轨' : 'AI 批注' }}</h5>
                <div class="comments-list">
                  <div v-for="comment in selectedComments" :key="comment.title" class="comment-item">
                    <div class="comment-title">{{ comment.title }}</div>
                    <p class="comment-desc">{{ comment.description }}</p>
                  </div>
                  <div v-if="!selectedComments.length" class="no-comments">
                    暂无批注
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="inspector-actions">
            <button type="button" class="btn" @click="downloadHomework(selectedHomework)">下载</button>
            <button v-if="isTeacher && selectedHomework?.status === 'pending'" type="button" class="btn btn-primary" @click="markReviewed(selectedHomework)">标记已批改</button>
            <button v-if="isTeacher" type="button" class="btn btn-danger" @click="removeHomework(selectedHomework)">删除</button>
          </div>
        </aside>
      </div>

      <!-- Status Bar -->
      <footer class="statusline">
        <span>作业中心</span>
        <span class="sep">|</span>
        <span>总计: {{ stats.total }}</span>
        <span class="sep">|</span>
        <span>待处理: {{ stats.pending }}</span>
        <span class="sep">|</span>
        <span>模式: {{ isTeacher ? '教师' : '学生' }}</span>
      </footer>

      </div>

      <!-- Bottom Floating Ellipse Dock -->
      <div class="dock-bar">
      <div class="dock-inner">
        <button
          v-for="chip in statusChips"
          :key="chip.value"
          type="button"
          class="dock-item"
          :class="{ active: activeFilter === chip.value }"
          @click="activeFilter = chip.value"
        >
          <span class="dock-dot" :style="{ background: chip.color }"></span>
          <span class="dock-label">{{ chip.label }}</span>
          <span class="dock-count">{{ chip.count }}</span>
        </button>
        <div class="dock-divider"></div>
        <div class="dock-stats">
          <span class="stat-item">
            <span class="stat-label">总计</span>
            <span class="stat-value">{{ stats.total }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">待处理</span>
            <span class="stat-value warning">{{ stats.pending }}</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Upload Dialog -->
    <div v-if="showUpload" class="dialog-mask" @click.self="showUpload = false">
      <div class="dialog-card">
        <div class="dialog-header">
          <div class="dialog-title">{{ isTeacher ? '上传示例作业' : '提交作业' }}</div>
          <button type="button" class="dialog-close" @click="showUpload = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="field-block">
            <label>选择文件</label>
            <div class="file-input-wrapper" @click="triggerFileInput">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17,8 12,3 7,8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>{{ selectedFile?.name || '点击选择文件' }}</span>
            </div>
            <input ref="fileInputRef" type="file" @change="onFileChange" />
          </div>
          <div class="field-block">
            <label>课程</label>
            <input v-model="uploadForm.course" type="text" placeholder="例如：算法设计" />
          </div>
          <div class="field-block">
            <label>备注</label>
            <textarea v-model="uploadForm.note" placeholder="补充作业说明"></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button type="button" class="btn" @click="showUpload = false">取消</button>
          <button type="button" class="btn btn-primary" :disabled="uploading" @click="uploadHomework">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { homeworkApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { summarizeHomework } from '@/utils/viewModels'

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.user?.role === 'teacher' || authStore.user?.role === 'admin')

// View modes
const viewModes = [
  { label: '队列', value: 'queue' },
  { label: '网格', value: 'grid' },
  { label: '时间线', value: 'timeline' }
]
const activeView = ref('queue')
const searchQuery = ref('')

// Filter
const activeFilter = ref('all')

// Homework data
const homeworkItems = ref([])
const selectedHomework = ref(null)
const showUpload = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const fileInputRef = ref(null)

const uploadForm = ref({
  course: '',
  note: ''
})

// Status chips
const statusChips = computed(() => [
  { label: '全部', value: 'all', color: '#007AFF', count: homeworkItems.value.length },
  { label: '待处理', value: 'pending', color: '#FF9500', count: homeworkItems.value.filter(i => i.status === 'pending').length },
  { label: '已完成', value: 'reviewed', color: '#34C759', count: homeworkItems.value.filter(i => i.status === 'reviewed').length }
])

// Stats
const stats = computed(() => {
  const total = homeworkItems.value.length
  const pending = homeworkItems.value.filter(i => i.status === 'pending').length
  const reviewed = homeworkItems.value.filter(i => i.status === 'reviewed').length
  return { total, pending, reviewed }
})

// Filtered homework
const filteredHomework = computed(() => {
  return homeworkItems.value.filter(item => {
    const matchesFilter = activeFilter.value === 'all' || item.status === activeFilter.value
    const matchesSearch = !searchQuery.value ||
      item.filename?.includes(searchQuery.value) ||
      item.course?.includes(searchQuery.value)
    return matchesFilter && matchesSearch
  })
})

// Selected comments
const selectedComments = computed(() => {
  if (!selectedHomework.value) return []

  if (isTeacher.value) {
    return [
      { title: '定位错误段落', description: '预留字符级、行级或段落级批注位置。' },
      { title: '给出改进建议', description: '结合静态分析与 LLM 解释生成上下文反馈。' }
    ]
  }

  return [
    { title: 'AI 批注摘要', description: '展示当前作业中识别出的关键问题与改进方向。' },
    { title: '推荐下一步', description: `当前识别到 ${selectedHomework.value.aiCommentCount || 2} 条可继续追问的建议。` }
  ]
})

// Actions
function triggerFileInput() {
  fileInputRef.value?.click()
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function uploadHomework() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件。')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('homework_id', Date.now().toString())
    formData.append('student_id', authStore.user?.id || 'current_user')
    if (uploadForm.value.course) formData.append('course', uploadForm.value.course)
    if (uploadForm.value.note) formData.append('note', uploadForm.value.note)
    await homeworkApi.upload(formData)
    ElMessage.success('作业上传成功。')
    showUpload.value = false
    selectedFile.value = null
    uploadForm.value = { course: '', note: '' }
    await loadHomework()
  } catch {
    ElMessage.error('上传失败。')
  } finally {
    uploading.value = false
  }
}

async function downloadHomework(item) {
  try {
    const res = await homeworkApi.download(item.id)
    if (res?.data?.download_url) {
      window.open(res.data.download_url, '_blank')
    }
  } catch {
    ElMessage.error('下载失败。')
  }
}

async function markReviewed(item) {
  try {
    await homeworkApi.updateStatus(item.id, 'reviewed')
    ElMessage.success('已标记为已批改。')
    await loadHomework()
  } catch {
    ElMessage.error('状态更新失败。')
  }
}

async function removeHomework(item) {
  try {
    await homeworkApi.delete(item.id)
    ElMessage.success('作业已删除。')
    if (selectedHomework.value?.id === item.id) {
      selectedHomework.value = null
    }
    await loadHomework()
  } catch {
    ElMessage.error('删除失败。')
  }
}

async function loadHomework() {
  try {
    const res = await homeworkApi.list({ page: 1, page_size: 50 })
    homeworkItems.value = summarizeHomework(res?.data)
  } catch {
    homeworkItems.value = []
  }

  if (!selectedHomework.value && homeworkItems.value.length > 0) {
    selectedHomework.value = homeworkItems.value[0]
  }
}

onMounted(loadHomework)
</script>

<style scoped>
/* Page wrapper */
.homework-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* Design tokens */
.mac-window {
  --bg-window: #ececec;
  --bg-content: #f5f5f7;
  --bg-panel: rgba(255, 255, 255, 0.72);
  --bg-panel-solid: #ffffff;
  --bg-sidebar: rgba(246, 246, 246, 0.85);
  --border: rgba(0, 0, 0, 0.08);
  --border-strong: rgba(0, 0, 0, 0.12);
  --text: #1d1d1f;
  --text-secondary: rgba(60, 60, 67, 0.72);
  --text-tertiary: rgba(60, 60, 67, 0.48);
  --accent: #007aff;
  --accent-soft: rgba(0, 122, 255, 0.12);
  --shadow-window: 0 22px 70px rgba(0, 0, 0, 0.12);
  --shadow-panel: 0 1px 3px rgba(0, 0, 0, 0.06);
  --radius-window: 14px;
  --radius-panel: 10px;
}

.mac-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-window);
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  font-size: 13px;
  color: var(--text);
  position: relative;
}

/* Title Bar */
.titlebar {
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: linear-gradient(180deg, #fbfbfb 0%, #ececec 100%);
  border-bottom: 1px solid var(--border);
}

.titlebar-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.titlebar-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* Toolbar */
.toolbar {
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  background: linear-gradient(180deg, #ebebed 0%, #e4e4e7 100%);
  border-bottom: 1px solid var(--border);
}

.segmented {
  display: inline-flex;
  background: rgba(0,0,0,0.06);
  border-radius: 6px;
  padding: 2px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
}

.segmented button {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.segmented button[aria-pressed="true"] {
  background: var(--bg-panel-solid);
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.segmented button:hover:not([aria-pressed="true"]) {
  background: rgba(0,0,0,0.04);
}

.toolbar-spacer { flex: 1; }

.search-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 200px;
  max-width: 280px;
  padding: 4px 10px;
  background: rgba(255,255,255,0.85);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  box-shadow: inset 0 1px 1px rgba(0,0,0,0.04);
}

.search-field:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.search-field input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 12px;
  color: var(--text);
}

.search-field input::placeholder { color: var(--text-tertiary); }
.search-field svg { width: 14px; height: 14px; color: var(--text-tertiary); flex-shrink: 0; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
}

.tb-btn:hover {
  background: #fff;
  border-color: var(--border-strong);
}

.tb-btn svg { width: 14px; height: 14px; }

/* Split Root */
.split-root {
  flex: 1;
  display: flex;
  min-height: 0;
  background: var(--bg-content);
  padding-bottom: 80px;
}

/* Middle: Canvas Pane */
.canvas-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: linear-gradient(180deg, #fafafa 0%, #f3f3f5 100%);
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.5);
  flex-shrink: 0;
}

.canvas-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.hint {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-tertiary);
}

.canvas-body {
  flex: 1;
  min-height: 0;
  position: relative;
  background: var(--bg-panel-solid);
  overflow-y: auto;
  padding: 12px;
}

.canvas-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 1px 1px, rgba(0,0,0,0.06) 1px, transparent 0);
  background-size: 18px 18px;
  opacity: 0.7;
  pointer-events: none;
}

/* Homework List */
.homework-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.homework-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
  animation: fadeIn 0.3s ease backwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.homework-card:hover {
  border-color: rgba(0,122,255,0.3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.homework-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.homework-card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  flex-shrink: 0;
}

.homework-card-icon svg { width: 20px; height: 20px; }

.homework-card-icon.reviewed {
  background: rgba(52, 199, 89, 0.15);
  color: #34C759;
}

.homework-card-icon.pending {
  background: rgba(255, 149, 0, 0.15);
  color: #FF9500;
}

.homework-card-icon.default {
  background: rgba(0, 122, 255, 0.15);
  color: #007AFF;
}

.homework-card-content {
  flex: 1;
  min-width: 0;
}

.homework-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.homework-card-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.meta-tag {
  font-size: 11px;
  color: var(--text-tertiary);
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.homework-card-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

.homework-card-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.reviewed {
  background: rgba(52, 199, 89, 0.15);
  color: #34C759;
}

.status-badge.pending {
  background: rgba(255, 149, 0, 0.15);
  color: #FF9500;
}

.score-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

/* Placeholder */
.canvas-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 24px;
  pointer-events: none;
  position: relative;
  z-index: 1;
}

.canvas-placeholder svg { width: 40px; height: 40px; opacity: 0.35; }
.canvas-placeholder h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); }
.canvas-placeholder p { font-size: 12px; max-width: 320px; line-height: 1.5; }

/* Right: Inspector Panel */
.inspector {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(252, 252, 252, 0.92);
  border-left: 1px solid var(--border);
  backdrop-filter: blur(12px);
}

.inspector-header {
  padding: 12px 14px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  text-transform: uppercase;
  flex-shrink: 0;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.inspector-empty {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: var(--text-tertiary);
  padding: 20px;
}

.inspector-empty svg { width: 36px; height: 36px; opacity: 0.4; }
.inspector-empty h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.inspector-empty p { font-size: 12px; line-height: 1.45; }

.group-box {
  background: var(--bg-panel-solid);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.8) inset;
}

.group-box h5 {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.group-box .row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 3px 0;
  color: var(--text-secondary);
}

.group-box .row span:last-child {
  color: var(--text);
  font-weight: 500;
}

.preview-box {
  min-height: 160px;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 120px;
  background: rgba(0,0,0,0.02);
  border-radius: 8px;
  padding: 16px;
}

.preview-placeholder svg { width: 32px; height: 32px; color: var(--text-tertiary); opacity: 0.5; }
.preview-placeholder p { font-size: 12px; color: var(--text-secondary); }
.preview-hint { font-size: 11px; color: var(--text-tertiary); }

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-item {
  padding: 8px;
  background: rgba(0,0,0,0.02);
  border-radius: 6px;
}

.comment-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.comment-desc {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.no-comments {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 12px;
}

.inspector-actions {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn {
  flex: 1;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-strong);
  background: linear-gradient(180deg, #fff 0%, #f2f2f3 100%);
  color: var(--text);
  cursor: pointer;
  transition: filter 0.12s, box-shadow 0.12s;
}

.btn:hover { filter: brightness(1.02); }
.btn:active { filter: brightness(0.98); }

.btn-primary {
  border-color: rgba(0, 122, 255, 0.45);
  background: linear-gradient(180deg, #4da2ff 0%, #007aff 100%);
  color: #fff;
}

.btn-danger {
  border-color: rgba(255, 59, 48, 0.45);
  background: linear-gradient(180deg, #ff6b63 0%, #ff3b30 100%);
  color: #fff;
}

/* Status Bar */
.statusline {
  height: 24px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 11px;
  color: var(--text-tertiary);
  background: linear-gradient(180deg, #e9e9eb 0%, #e2e2e5 100%);
  border-top: 1px solid var(--border);
}

.statusline .sep { margin: 0 8px; opacity: 0.5; }

/* Bottom Floating Ellipse Dock */
.dock-bar {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  padding: 6px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.12),
    0 1px 2px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.dock-inner {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dock-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 18px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.dock-item:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text);
}

.dock-item.active {
  background: #007AFF;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.35);
}

.dock-item.active .dock-count {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.dock-item.active .dock-dot {
  background: #ffffff !important;
}

.dock-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dock-label {
  font-weight: 500;
}

.dock-count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.dock-divider {
  width: 1px;
  height: 24px;
  background: rgba(0, 0, 0, 0.1);
  margin: 0 6px;
}

.dock-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
}

.stat-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.stat-value.warning {
  color: #FF9500;
}

/* Dialog */
.dialog-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.68);
  backdrop-filter: blur(10px);
}

.dialog-card {
  width: min(480px, 100%);
  background: var(--bg-panel-solid);
  border-radius: 14px;
  box-shadow: 0 24px 48px rgba(0,0,0,0.2);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.dialog-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
}

.dialog-close:hover {
  background: rgba(0,0,0,0.05);
}

.dialog-close svg { width: 16px; height: 16px; }

.dialog-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-block label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-block input,
.field-block textarea {
  padding: 8px 12px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  font-family: inherit;
  font-size: 13px;
  color: var(--text);
  background: rgba(255,255,255,0.8);
  transition: border-color 0.15s;
}

.field-block input:focus,
.field-block textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.field-block textarea {
  min-height: 80px;
  resize: vertical;
}

.file-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 2px dashed var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.file-input-wrapper:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.file-input-wrapper svg { width: 20px; height: 20px; color: var(--text-tertiary); }
.file-input-wrapper span { font-size: 13px; color: var(--text-secondary); }

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  background: rgba(0,0,0,0.02);
}

.dialog-footer .btn {
  flex: 0;
  padding: 8px 16px;
}

/* Responsive */
@media (max-width: 900px) {
  .homework-page { padding: 12px; }
  .mac-window { width: 100%; }
  .inspector { width: 260px; }
}

@media (max-width: 720px) {
  .split-root { flex-direction: column; }
  .inspector {
    width: 100%;
    border-left: none;
    border-top: 1px solid var(--border);
  }
  .canvas-pane { min-height: 280px; }
  .dock-bar {
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
  }
  .dock-item { padding: 6px 10px; }
  .dock-stats { display: none; }
}
</style>
