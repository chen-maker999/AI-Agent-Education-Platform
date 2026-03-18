<template>
  <div class="knowledge-page">
    <aside class="knowledge-sidebar">
      <div class="logo-block">
        <div class="logo-icon">AI</div>
        <span class="logo-text">Agent</span>
      </div>

      <div class="sidebar-buttons">
        <input
          type="file"
          ref="fileInput"
          @change="handleFileUpload"
          accept=".txt,.md,.py,.js,.html,.css,.json,.pdf"
          style="display: none"
        />
        <button class="btn btn-outline" @click="triggerFilePicker">导入</button>
        <button class="btn btn-primary" @click="openCreateDialog">新建</button>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-item" :class="{ active: activeTab === 'square' }" @click="switchTab('square')">
          <span class="nav-icon">📚</span>
          <span>知识库广场</span>
        </div>
        <div class="nav-item" :class="{ active: activeTab === 'my' }" @click="switchTab('my')">
          <span class="nav-icon">🗂️</span>
          <span>我的知识库</span>
        </div>
      </nav>

      <div class="sidebar-section" v-if="activeTab === 'my'">
        <h3>我的知识库</h3>
        <div class="kb-card" v-for="kb in myKbs" :key="kb.kb_id" @click="selectKb(kb)" :style="selectedKB?.kb_id === kb.kb_id ? 'border:1px solid #3b82f6' : ''">
          <div class="kb-card-header">
            <span>{{ kb.name }}</span>
            <span class="count">ID: {{ kb.kb_id }}</span>
          </div>
          <p>{{ kb.description || '暂无描述' }}</p>
        </div>
        <div class="kb-card">
          <div class="kb-card-header">
            <span>创建的知识库</span>
            <span class="count">{{ myKbs.length }}</span>
          </div>
          <p>共 {{ myKbs.length }} 个知识库</p>
        </div>
        <div class="kb-card">
          <div class="kb-card-header">
            <span>上传的文档</span>
            <span class="count">{{ documents.length }}</span>
          </div>
          <p>共 {{ documents.length }} 个文档</p>
        </div>
      </div>
    </aside>

    <main class="knowledge-main">
      <!-- 上传区域 -->
      <div v-if="isUploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <p>{{ uploadStatus === 'exception' ? '上传失败' : '正在处理文档...' }}</p>
      </div>

      <!-- 已上传文档列表 -->
      <div v-if="documents.length > 0" class="documents-section">
        <h3>已上传文档</h3>
        <div class="document-list">
          <div v-for="doc in documents" :key="doc.doc_id" class="document-item">
            <span class="doc-icon">📄</span>
            <span class="doc-name">{{ doc.metadata?.filename || '未知文件' }}</span>
            <span class="doc-chunks">块数: {{ doc.metadata?.chunk_index + 1 || '-' }}</span>
            <button class="btn-icon" @click="deleteDoc(doc.doc_id)" title="删除">
              🗑️
            </button>
          </div>
        </div>
      </div>

      <div class="kb-icon-bg" aria-hidden="true">
        <div class="kb-icon-bg-inner">
          <img v-for="(src, idx) in bgIcons" :key="idx" :src="src" alt="" />
        </div>
      </div>
      <div class="main-header">
        <h1>欢迎来到 <span class="highlight">知识库</span></h1>
        <p>上传文档后，可以在智能问答中选择"知识库对话"模式，基于文档内容进行问答。</p>
        <p v-if="selectedKB" style="margin-top: 6px; font-size: 13px; color:#6b7280;">
          当前知识库：<b>{{ selectedKB.name }}</b>（{{ selectedKB.kb_id }}）
        </p>
      </div>

      <!-- 上传提示区域 -->
      <div class="upload-area" @click="triggerFilePicker">
        <div class="upload-icon">📤</div>
        <p>点击上传文档 (支持 .txt, .md, .py, .js, .pdf 等文本文件和 PDF)</p>
        <p class="upload-hint">上传后自动进行分块、向量化，可用于RAG智能问答</p>
      </div>

      <!-- 知识点列表 -->
      <section class="section-card" v-if="knowledgePoints.length > 0">
        <h3>知识点</h3>
        <div class="knowledge-list">
          <div v-for="point in knowledgePoints" :key="point.id" class="knowledge-item">
            <h4>{{ point.name }}</h4>
            <p>{{ point.description }}</p>
          </div>
        </div>
      </section>

      <section class="section-card">
        <h3>知识库广场</h3>
        <p>统一管理个人与团队知识，支持导入、搜索、协作与共享。</p>
      </section>
    </main>

    <!-- 新建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="520px">
      <el-form :model="newKb" label-width="90px">
        <el-form-item label="名称">
          <el-input v-model="newKb.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newKb.description" type="textarea" :rows="3" placeholder="知识库描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createKb">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi, ragApi, libraryApi } from '@/api'
import { ElMessage, ElNotification } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const iconModules = import.meta.glob(
  '../../icons/icon_u7adlm4fwln/professional/**/*.png',
  { eager: true, query: '?url', import: 'default' }
)

const iconUrls = Object.values(iconModules)
// 背景图标：使用 professional 目录下所有图标，不够铺满则重复
const bgIcons = Array.from(
  { length: Math.max(160, iconUrls.length * 10) },
  (_, i) => iconUrls[i % iconUrls.length]
)

const knowledgePoints = ref([])
const knowledgeGraphs = ref([])
const selectedKB = ref(null)
const activeTab = ref('square')
const myKbs = ref([])
const authStore = useAuthStore()

// 上传相关状态
const fileInput = ref(null)
const documents = ref([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const showCreateDialog = ref(false)
const newKb = ref({ name: '', description: '' })

// 点击"导入"按钮 - 触发文件选择器
const triggerFilePicker = () => {
  const el = fileInput.value
  if (!el) {
    console.error('fileInput ref 未就绪')
    return
  }
  el.click()
}

// 点击"新建"按钮 - 打开创建对话框
const openCreateDialog = () => {
  showCreateDialog.value = true
}

// 加载已上传的文档列表
const loadDocuments = async () => {
  try {
    const courseId = selectedKB.value?.kb_id || 'default'
    const res = await ragApi.listDocuments(courseId)
    if (res.code === 200) {
      documents.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载文档列表失败:', error)
  }
}

const loadMyKbs = async () => {
  try {
    const ownerId = authStore.user?.id || 'default'
    const res = await libraryApi.my(ownerId, 1, 50)
    if (res.code === 200) {
      myKbs.value = res.data?.items || []
    }
  } catch (e) {
    console.error('加载我的知识库失败:', e)
  }
}

// 处理文件上传
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型（包括 PDF）
  const allowedTypes = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.ts', '.vue', '.java', '.c', '.cpp', '.go', '.rs', '.pdf']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedTypes.includes(ext)) {
    ElMessage.error('不支持的文件类型，仅支持文本文件和 PDF')
    return
  }

  // 验证文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return
  }

  isUploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('course_id', selectedKB.value?.kb_id || 'default')

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const res = await ragApi.upload(formData)

    clearInterval(progressInterval)
    uploadProgress.value = 100
    uploadStatus.value = 'success'

    if (res.code === 200) {
      ElMessage.success(`文档上传成功，已分块为 ${res.data?.doc_count || 0} 个知识块`)
      loadDocuments()
    } else {
      uploadStatus.value = 'exception'
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    uploadStatus.value = 'exception'
    ElMessage.error('文件处理失败: ' + (error.message || '未知错误'))
  } finally {
    isUploading.value = false
    // 清空input
    event.target.value = ''
    setTimeout(() => {
      uploadProgress.value = 0
      uploadStatus.value = ''
    }, 2000)
  }
}

// 删除文档
const deleteDoc = async (docId) => {
  try {
    const res = await ragApi.deleteDocument(docId)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadDocuments()
    }
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 新建知识库
const createKb = async () => {
  if (!newKb.value.name) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  try {
    // 后端知识库接口当前不强制鉴权；未登录时也允许创建到默认 owner_id 下
    const ownerId =
      authStore.user?.id ??
      authStore.user?.user_id ??
      authStore.user?.uid ??
      (authStore.isAuthenticated ? undefined : 'default')

    if (!ownerId && authStore.isAuthenticated) {
      await authStore.fetchUserInfo()
    }

    const finalOwnerId =
      authStore.user?.id ??
      authStore.user?.user_id ??
      authStore.user?.uid ??
      'default'

    const res = await libraryApi.create({
      owner_id: finalOwnerId,
      name: newKb.value.name,
      description: newKb.value.description || '',
      settings: { top_k: 5, use_rewrite: true, use_rerank: true }
    })
    if (res.code === 200) {
      ElNotification({
        title: '新建成功',
        message: `知识库「${newKb.value.name}」已创建`,
        type: 'success',
        duration: 3000
      })
      showCreateDialog.value = false
      newKb.value = { name: '', description: '' }
      await loadMyKbs()
      // 创建后切到「我的知识库」，并默认选中新建项
      activeTab.value = 'my'
      // 默认选中新建的知识库
      if (res.data?.kb_id) {
        selectKb(res.data)
      }
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    console.error('创建失败:', error)
    const msg = error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message
    ElMessage.error(typeof msg === 'string' ? msg : '创建失败')
  }
}

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'my') {
    loadMyKbs()
  }
}

const selectKb = async (kb) => {
  selectedKB.value = kb
  await loadDocuments()
}

const loadKnowledgePoints = async () => {
  try {
    const res = await knowledgeApi.points.list({ page: 1, page_size: 50 })
    if (res.code === 200) {
      knowledgePoints.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载知识点失败:', error)
  }
}

const loadKnowledgeGraphs = async () => {
  try {
    const res = await knowledgeApi.graph.list()
    if (res.code === 200) {
      knowledgeGraphs.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
  }
}

const createKnowledge = async (type) => {
  try {
    if (type === 'point') {
      await knowledgeApi.points.create({
        title: '新知识点',
        content: '知识点内容'
      })
      ElMessage.success('知识点创建成功')
      loadKnowledgePoints()
    } else if (type === 'graph') {
      await knowledgeApi.graph.create({
        name: '新知识图谱',
        description: '知识图谱描述'
      })
      ElMessage.success('知识图谱创建成功')
      loadKnowledgeGraphs()
    }
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const searchKnowledge = async (query) => {
  try {
    const res = await knowledgeApi.points.search(query)
    if (res.code === 200) {
      knowledgePoints.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('搜索失败:', error)
  }
}

onMounted(() => {
  loadKnowledgePoints()
  loadKnowledgeGraphs()
  loadMyKbs()
  loadDocuments()
})
</script>

<style scoped>
.knowledge-page {
  height: calc(100vh - 64px);
  display: flex;
  overflow: hidden;
  background: #fafbfc;
}

/* 左侧边栏 */
.knowledge-sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 20px;
  flex-shrink: 0;
}

.logo-block {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  padding: 0 8px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1e1b4b;
}

.sidebar-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.btn {
  flex: 1;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-outline {
  background: white;
  border: 1px solid #e5e7eb;
  color: #4b5563;
}

.btn-outline:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.btn-primary {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1d4ed8;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #6b7280;
  font-size: 14px;
}

.nav-item:hover {
  background: #f9fafb;
}

.nav-item.active {
  background: #f3f4f6;
  color: #1f2937;
  font-weight: 500;
}

.nav-icon {
  font-size: 16px;
}

.sidebar-section h3 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  margin-bottom: 12px;
  padding: 0 8px;
}

.kb-card {
  background: #f9fafb;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  background: #f3f4f6;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.count {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 400;
}

.kb-card p {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.4;
}

/* 右侧主内容 */
.knowledge-main {
  flex: 1;
  padding: 40px 48px;
  overflow-y: auto;
  position: relative;
  isolation: isolate;
}

/* 背景：professional 图标网格 + 向左上倾斜 */
.kb-icon-bg {
  position: fixed;
  top: 64px;
  left: 240px;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.kb-icon-bg-inner {
  position: absolute;
  inset: -260px;
  opacity: 0.18;
  transform: rotate(-18deg) scale(1.02);
  transform-origin: center;

  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-auto-rows: 60px;
  gap: 40px;
  align-content: start;
  justify-items: center;
}

.kb-icon-bg img {
  width: 45px;
  height: 45px;
  object-fit: contain;
}

.knowledge-main > :not(.kb-icon-bg) {
  position: relative;
  z-index: 1;
}

.main-header {
  margin-bottom: 32px;
}

.main-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1e1b4b;
  margin-bottom: 12px;
}

.highlight {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.main-header p {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 600px;
}

/* 空状态 */
.empty-state {
  background: white;
  border: 1px dashed #e5e7eb;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  margin-bottom: 24px;
}

.empty-illustration {
  margin-bottom: 16px;
}

.empty-icon {
  font-size: 56px;
}

.empty-text {
  font-size: 16px;
  color: #6b7280;
  margin-bottom: 20px;
}

.btn-lg {
  padding: 12px 32px;
  font-size: 15px;
}

/* 知识库广场 */
.section-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  min-height: 168px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-bottom: 16px;
}

.section-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.section-card p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}

/* 上传进度 */
.upload-progress {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.upload-progress p {
  margin-top: 10px;
  color: #6b7280;
  font-size: 14px;
}

/* 文档列表 */
.documents-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.documents-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 14px;
}

.doc-icon {
  font-size: 18px;
}

.doc-name {
  flex: 1;
  color: #1f2937;
  font-weight: 500;
}

.doc-chunks {
  color: #6b7280;
  font-size: 12px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-icon:hover {
  background: #fee2e2;
}

/* 上传区域 */
.upload-area {
  background: white;
  border: 2px dashed #3b82f6;
  border-radius: 16px;
  padding: 40px;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  margin-bottom: 24px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  background: #eff6ff;
  border-color: #2563eb;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.upload-area p {
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 13px;
  color: #6b7280 !important;
}

@media (max-width: 768px) {
  .upload-area {
    min-height: 240px;
    padding: 28px;
  }

  .section-card {
    min-height: 140px;
    padding: 18px;
  }
}

/* 知识列表 */
.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.knowledge-item h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.knowledge-item p {
  font-size: 13px;
  color: #6b7280;
}
</style>
