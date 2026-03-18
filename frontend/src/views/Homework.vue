<template>
  <div class="homework-page">
    <!-- 页面头部 -->
    <div class="page-header-custom">
      <div class="header-content">
        <div class="header-text">
          <h1>作业管理</h1>
          <p v-if="isTeacher">上传、管理和批改学生作业</p>
          <p v-else>查看和提交作业</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" @click="showUploadModal = true" v-if="!isTeacher">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            提交作业
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
        </div>
        <div class="search-box-modern">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input type="text" placeholder="搜索作业..." v-model="searchQuery">
        </div>
      </div>

      <div class="homework-table-modern">
        <table>
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
import { homeworkApi } from '@/api'
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

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.user?.role === 'teacher' || authStore.user?.role === 'admin')

const filter = ref('all')
const searchQuery = ref('')
const showUploadModal = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadForm = ref({ course: '', note: '' })

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
