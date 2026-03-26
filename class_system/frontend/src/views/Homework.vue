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
                @click="selectHomework(item)"
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

              <!-- Kimi 批改进度 / 结果 -->
              <div v-if="grading || gradingResult" class="group-box grading-result">
                <h5>Kimi 智能批改</h5>

                <!-- 进度条 -->
                <div v-if="grading" class="grading-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: gradingProgress + '%' }"></div>
                  </div>
                  <div class="progress-text">{{ gradingPhase }}</div>
                </div>

                <!-- 批改结果 -->
                <div v-if="gradingResult && !grading" class="grading-done">
                  <div class="score-row">
                    <span class="score-label">得分</span>
                    <span class="score-value" :class="{
                      excellent: gradingResult.score >= 90,
                      good: gradingResult.score >= 70 && gradingResult.score < 90,
                      medium: gradingResult.score >= 60 && gradingResult.score < 70,
                      poor: gradingResult.score < 60
                    }">
                      {{ gradingResult.score }}/{{ gradingResult.total_score }}
                    </span>
                  </div>
                  <div class="issue-count">
                    共发现 <strong>{{ gradingResult.issue_count }}</strong> 个问题
                  </div>
                  <div class="grading-summary">{{ gradingResult.summary }}</div>
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
            <button type="button" class="btn" @click="downloadHomework(selectedHomework)">
              {{ selectedHomework?.hasReview ? '下载批改文件' : '下载' }}
            </button>
            <!-- 智能批改按钮：仅学生可见，仅 doc/docx 文件 -->
            <button
              v-if="!isTeacher && selectedHomework?.filename"
              type="button"
              class="btn btn-primary"
              :disabled="grading"
              @click="startKimiGrade(selectedHomework)"
            >
              {{ grading ? '批改中…' : 'Kimi 智能批改' }}
            </button>
            <button v-if="isTeacher && selectedHomework?.status === 'pending'" type="button" class="btn btn-primary" @click="markReviewed(selectedHomework)">标记已批改</button>
            <button v-if="isTeacher || (!isTeacher && selectedHomework?.uploader === authStore.user?.id)" type="button" class="btn btn-danger" @click="removeHomework(selectedHomework)">删除</button>
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
    <Teleport to="body">
      <div v-if="showUpload" class="dialog-root">
        <div class="dialog-backdrop" aria-hidden="true" @click="showUpload = false"></div>
        <div class="macos-window" role="dialog" aria-modal="true" @click.stop>
          <!-- Title bar — macOS traffic lights -->
          <div class="macos-titlebar">
            <div class="macos-dots">
              <span class="dot dot--close" @click="showUpload = false"></span>
              <span class="dot dot--minimize"></span>
              <span class="dot dot--maximize"></span>
            </div>
            <span class="macos-title">{{ isTeacher ? '上传示例作业' : '提交作业' }}</span>
            <div class="macos-titlebar-spacer"></div>
          </div>

          <!-- Content -->
          <div class="macos-content auth-form-panel">
            <div class="auth-panel__header">
              <div class="auth-panel__eyebrow">Upload</div>
              <h2 class="auth-panel__title">{{ isTeacher ? '上传示例作业' : '提交作业' }}</h2>
              <p class="auth-panel__sub">{{ isTeacher ? '上传一份示例作业供学生参考' : '上传你的作业文档，AI 将自动批改' }}</p>
            </div>

            <div class="auth-form">
              <!-- File picker -->
              <div class="form-group">
                <label class="input-label">选择文件</label>
                <div class="input-wrap file-input-wrapper" @click="fileInputRef?.click()">
                  <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                    <path d="M14 3H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                    <polyline points="14,3 14,8 19,8" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                  </svg>
                  <span class="file-name">{{ selectedFile?.name || '点击选择文件（支持 doc/docx/pdf）' }}</span>
                  <input ref="fileInputRef" type="file" class="visually-hidden" @change="onFileChange" />
                </div>
              </div>

              <!-- Course -->
              <div class="form-group">
                <label class="input-label">课程名称</label>
                <div class="input-wrap">
                  <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                    <path d="M2 6h16M2 10h10M2 14h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  <input class="input-field input-field--icon" v-model="uploadForm.course" type="text" placeholder="例如：算法设计" />
                </div>
              </div>

              <!-- Note -->
              <div class="form-group">
                <label class="input-label">备注（可选）</label>
                <div class="input-wrap">
                  <textarea class="input-field" v-model="uploadForm.note" placeholder="补充作业说明或要求…" rows="3"></textarea>
                </div>
              </div>

              <!-- Actions -->
              <div class="auth-switch">
                <button type="button" class="btn" @click="showUpload = false">取消</button>
                <button type="button" class="btn btn-primary auth-submit" :disabled="uploading || !selectedFile" @click="uploadHomework">
                  <svg v-if="uploading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="10"/>
                  </svg>
                  {{ uploading ? '上传中…' : '确认上传' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { homeworkApi, reviewApi } from '@/api'
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

// Kimi AI 批改状态
const grading = ref(false)
const gradingProgress = ref(0)
const gradingPhase = ref('')
const gradingResult = ref(null) // { review_id, score, issues, graded_file_url, ... }

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

  // 优先展示 Kimi 批改结果
  if (gradingResult.value?.issues?.length) {
    return gradingResult.value.issues.map((issue, idx) => ({
      title: `[${issue.severity === 'error' ? '错误' : issue.severity === 'warning' ? '警告' : '提示'}] ${issue.location || '全局'}`,
      description: `${issue.description}\n→ ${issue.suggestion}`
    }))
  }

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
// noop — file input 点击事件由其父级 wrapper 自动触发

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function selectHomework(item) {
  selectedHomework.value = item
  gradingResult.value = null
  // 如果作业已被批改，加载批改记录获取 graded_file_url
  if (item?.status === 'reviewed' && item?.id) {
    try {
      const res = await reviewApi.list({ homework_id: item.id })
      const review = res?.data?.items?.[0]
      if (review) {
        gradingResult.value = review
      }
    } catch {
      // 静默失败，不影响选择
    }
  }
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
  const reviewId = gradingResult.value?.review_id
  const gradedUrl = gradingResult.value?.graded_file_url

  if (!reviewId && !gradedUrl) {
    ElMessage.warning('该作业尚未进行智能批改。')
    return
  }

  try {
    let url = gradedUrl
    let filename = item?.graded_filename || '批改结果.docx'

    if (reviewId) {
      const meta = await reviewApi.download(reviewId)
      url = meta?.data?.download_url || url
      filename = meta?.data?.graded_filename || filename
    }

    if (!url) {
      ElMessage.error('没有可用的批改文件链接。')
      return
    }

    const r = await fetch(url, { mode: 'cors' })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const buf = await r.arrayBuffer()

    const u8 = new Uint8Array(buf)
    const isZip = u8.length >= 4 && u8[0] === 0x50 && u8[1] === 0x4b
    if (!isZip) {
      const probe = new TextDecoder('utf-8', { fatal: false }).decode(u8.slice(0, 256))
      if (probe.trimStart().startsWith('<') || probe.includes('Error')) {
        ElMessage.error('下载到的不是 Word 文档，可能是 MinIO 错误页。')
        return
      }
    }

    const blob = new Blob([buf], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename.endsWith('.docx') ? filename : `${filename}.docx`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e) {
    console.error(e)
    ElMessage.error('下载失败。')
  }
}

async function startKimiGrade(item) {
  if (!item?.id) return

  // 重置状态
  grading.value = true
  gradingProgress.value = 0
  gradingPhase.value = '正在连接 Kimi AI...'
  gradingResult.value = null

  try {
    // 模拟进度（实际由后端控制）
    const phases = [
      { progress: 10, text: '正在读取作业文件...' },
      { progress: 30, text: 'Kimi AI 正在分析代码结构...' },
      { progress: 60, text: 'Kimi AI 正在生成批注...' },
      { progress: 80, text: '正在注入 Word 批注...' },
      { progress: 95, text: '正在保存批改结果...' },
    ]
    let phaseIdx = 0
    const tick = setInterval(() => {
      if (phaseIdx < phases.length) {
        gradingProgress.value = phases[phaseIdx].progress
        gradingPhase.value = phases[phaseIdx].text
        phaseIdx++
      }
    }, 2000)

    const res = await reviewApi.grade(item.id)

    clearInterval(tick)
    gradingProgress.value = 100
    gradingPhase.value = '批改完成！'

    if (res?.code === 200 && res?.data) {
      gradingResult.value = res.data
      gradingPhase.value = `完成！得分 ${res.data.score}/${res.data.total_score}，发现 ${res.data.issue_count} 个问题`
      ElMessage.success('Kimi 智能批改完成！')
      await loadHomework()
      const hid = item.id
      const refreshed = homeworkItems.value.find((h) => h.id === hid)
      if (refreshed && selectedHomework.value?.id === hid) {
        selectedHomework.value = refreshed
      }
    } else {
      ElMessage.error(res?.message || '批改失败，请重试。')
    }
  } catch (err) {
    console.error('Kimi grading error:', err)
    ElMessage.error(err?.response?.data?.message || 'Kimi 批改失败，请检查网络和 API 配置。')
  } finally {
    grading.value = false
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
  // 非教师只能删除自己上传的作业
  if (!isTeacher.value && item.uploader !== authStore.user?.id) {
    ElMessage.warning('你只能删除自己上传的作业。')
    return
  }
  if (!confirm(`确定要删除作业「${item.filename}」吗？此操作不可撤销。`)) {
    return
  }
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
    // 后端返回 {items, total, page, page_size}，response拦截器已去掉外层code/message
    homeworkItems.value = summarizeHomework(res?.data?.items ?? [])
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

/* ════════════════════════════════════════════
   Upload Dialog — 完整复用 Login.vue 的 macOS 卡片风格
   ════════════════════════════════════════════ */

/* 根：Teleport to body，脱离侧栏玻璃层叠上下文 */
.dialog-root {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
}

.dialog-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  z-index: 0;
}

/* ── macOS Window 玻璃卡（与 Login.vue .macos-window 完全一致） ── */
.macos-window {
  position: relative;
  z-index: 1;
  width: min(480px, 100%);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset,
    0 1px 0 rgba(255, 255, 255, 0.9) inset;
  overflow: hidden;
  isolation: isolate;
}

.macos-titlebar {
  display: flex;
  align-items: center;
  padding: 11px 14px;
  background: rgba(248, 248, 248, 0.85);
  border-bottom: 1px solid rgba(0, 0, 0, 0.07);
}

.macos-dots {
  display: flex;
  gap: 8px;
  align-items: center;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--close { background: #ff5f57; cursor: pointer; }
.dot--minimize { background: #febc2e; }
.dot--maximize { background: #28c840; }

.macos-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.macos-titlebar-spacer { width: 52px; }

.macos-content {
  padding: 28px 32px;
}

.auth-form-panel {
  width: 100%;
}

.auth-panel__header { margin-bottom: 24px; }

.auth-panel__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--brand-500);
  margin-bottom: 6px;
}

.auth-panel__title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.auth-panel__sub {
  font-size: 13px;
  color: var(--text-muted);
}

/* ── 表单 ── */
.auth-form { display: flex; flex-direction: column; gap: 16px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }

.input-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.input-wrap { position: relative; display: flex; align-items: center; }

.input-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  pointer-events: none;
  flex-shrink: 0;
}

.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: var(--r-md, 8px);
  background: #f8fafc;
  font-size: 14px;
  color: var(--text-primary);
  transition: border-color 150ms ease, box-shadow 150ms ease;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}

.input-field::placeholder { color: var(--text-muted); }
.input-field:focus {
  border-color: var(--brand-400);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
  background: #fff;
}
.input-field--icon { padding-left: 44px; }

textarea.input-field { resize: vertical; min-height: 80px; }

/* 文件选择：与其他 input-field 视觉完全一致 */
.file-input-wrapper {
  /* 继承 .input-wrap 的 position/flex，仅覆盖边距与边框 */
  width: 100%;
  padding: 12px 16px 12px 44px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: var(--r-md, 8px);
  background: #f8fafc;
  cursor: pointer;
  transition: border-color 150ms ease, box-shadow 150ms ease, background 150ms ease;
  box-sizing: border-box;
}

.file-input-wrapper:hover {
  border-color: var(--brand-400);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
  background: #fff;
}

/* 隐藏原生 file input，但保留可点击 */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 文件选择区的图标 */
.file-input-wrapper .input-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  pointer-events: none;
}

/* 文件名文字 */
.file-name { font-size: 14px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-name:empty::before { content: '点击选择文件（支持 doc/docx/pdf）'; color: var(--text-muted); }

/* 操作行 */
.auth-switch {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.auth-submit { min-width: 120px; justify-content: center; }
.auth-submit:disabled { opacity: 0.45; cursor: not-allowed; }
.spin { animation: spin-slow 0.8s linear infinite; }
@keyframes spin-slow { to { transform: rotate(360deg); } }

/* ── 深色模式 ── */
:global([data-theme="dark"]) .macos-window {
  background: rgba(40, 40, 40, 0.88);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.10) inset;
}
:global([data-theme="dark"]) .macos-titlebar {
  background: rgba(30, 30, 30, 0.85);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}
:global([data-theme="dark"]) .macos-title { color: #999; }
:global([data-theme="dark"]) .auth-panel__eyebrow { color: var(--brand-400); }
:global([data-theme="dark"]) .auth-panel__title { color: #f1f5f9; }
:global([data-theme="dark"]) .auth-panel__sub { color: #94a3b8; }
:global([data-theme="dark"]) .input-label { color: #94a3b8; }
:global([data-theme="dark"]) .input-field {
  background: #1f2937;
  border-color: rgba(255, 255, 255, 0.10);
  color: #f1f5f9;
}
:global([data-theme="dark"]) .input-field::placeholder { color: #6b7280; }
:global([data-theme="dark"]) .input-field:focus {
  border-color: var(--brand-400);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.20);
  background: #1f2937;
}
:global([data-theme="dark"]) .input-icon { color: #6b7280; }
:global([data-theme="dark"]) .file-input-wrapper {
  border-color: rgba(255, 255, 255, 0.10);
  background: #1f2937;
}
:global([data-theme="dark"]) .file-input-wrapper:hover {
  border-color: var(--brand-400);
  background: rgba(37, 99, 235, 0.08);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
:global([data-theme="dark"]) .file-input-wrapper .input-icon { color: #6b7280; }
:global([data-theme="dark"]) .file-name { color: #94a3b8; }
:global([data-theme="dark"]) .file-name:empty::before { color: #6b7280; }

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

/* Kimi 智能批改 */
.grading-result {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 14px;
}
:global([data-theme="dark"]) .grading-result {
  background: #0c2444;
  border-color: #1e40af;
}
.grading-progress { margin-bottom: 8px; }
.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}
:global([data-theme="dark"]) .progress-bar { background: #374151; }
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 4px;
  transition: width 0.4s ease;
}
.progress-text {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}
:global([data-theme="dark"]) .progress-text { color: #9ca3af; }
.grading-done { display: flex; flex-direction: column; gap: 8px; }
.score-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.score-label { font-weight: 600; color: var(--text-secondary); }
.score-value { font-size: 22px; font-weight: 700; }
.score-value.excellent { color: #059669; }
.score-value.good { color: #2563eb; }
.score-value.medium { color: #d97706; }
.score-value.poor { color: #dc2626; }
.issue-count { font-size: 13px; color: #6b7280; }
:global([data-theme="dark"]) .issue-count { color: #9ca3af; }
.grading-summary { font-size: 13px; color: #374151; line-height: 1.5; }
:global([data-theme="dark"]) .grading-summary { color: #d1d5db; }
.btn-success {
  background: #059669 !important;
  color: #fff !important;
  border-color: #059669 !important;
}
.btn-success:hover { background: #047857 !important; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.mt-2 { margin-top: 8px; }
</style>
