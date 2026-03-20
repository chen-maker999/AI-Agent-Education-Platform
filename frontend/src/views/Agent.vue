<template>
  <div class="agent-page">
    <!-- 面包屑 -->
    <div class="agent-breadcrumb">
      <span class="breadcrumb-item">智能体</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-item" :class="{ current: !isEditing, 'link': true }" @click="showHistory">
        {{ isEditing ? '创建智能体' : '历史记录' }}
      </span>
      <template v-if="isEditing">
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-item current">{{ editingAgent ? '编辑' : '创建智能体' }}</span>
      </template>
      <div class="breadcrumb-actions">
        <button type="button" class="breadcrumb-btn" title="历史记录" @click="showHistory">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
        </button>
        <button type="button" class="breadcrumb-btn" title="帮助">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 历史记录列表 -->
    <div v-if="!isEditing" class="agent-history-list">
      <div class="agent-history-header">
        <h3>智能体历史记录</h3>
      </div>
      <div v-if="historyLoading" class="agent-history-loading">加载中...</div>
      <div v-else-if="agentList.length === 0" class="agent-history-empty">
        <p>暂无创建的智能体</p>
      </div>
      <div v-else class="agent-history-items">
        <div
          v-for="agent in agentList"
          :key="agent.id"
          class="agent-history-item"
          @click="editAgent(agent)"
        >
          <div class="agent-history-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8V4H8"/><rect x="2" y="14" width="8" height="8" rx="2" ry="2"/>
              <rect x="14" y="14" width="8" height="8" rx="2" ry="2"/>
              <path d="M18 8h-4V4"/><path d="M6 8H4"/>
            </svg>
          </div>
          <div class="agent-history-info">
            <span class="agent-history-name">{{ agent.name }}</span>
            <span class="agent-history-time">{{ formatDate(agent.updated_at || agent.created_at) }}</span>
          </div>
          <button type="button" class="agent-history-delete" title="删除" @click.stop="deleteAgent(agent.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="agent-history-footer">
        <button type="button" class="btn-create-new" @click="startCreate">
          + 创建新智能体
        </button>
      </div>
    </div>

    <!-- 顶部操作 -->
    <div class="agent-header">
      <div class="header-spacer"></div>
    </div>

    <!-- 基本信息 -->
    <section class="agent-section">

    </section>

    <!-- 创建/编辑表单（仅编辑状态显示） -->
    <template v-if="isEditing">

    <!-- 基本信息 -->
    <section class="agent-section">
      <div class="form-field required">
        <label>名称</label>
        <input
          v-model="form.name"
          type="text"
          placeholder="请输入智能体名称"
          maxlength="20"
          class="agent-input"
        />
        <span class="char-count">{{ form.name.length }}/20</span>
      </div>

      <div class="form-field">
        <label>提示词</label>
        <textarea
          v-model="form.prompt"
          placeholder="请输入智能体的角色、语气、工作流程、工具偏好及规则规范等。（选填）"
          maxlength="10000"
          class="agent-textarea"
          rows="6"
        ></textarea>
        <span class="char-count">{{ form.prompt.length }}/10000</span>
      </div>
    </section>

    <!-- 高级配置 -->
    <section class="agent-section advanced-card">
      <div class="advanced-header">
        <div class="advanced-title-row">
          <h3>可被其他智能体调用</h3>
          <span class="badge-solo">SOLO Only</span>
          <button type="button" class="icon-info" title="帮助文档">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </button>
        </div>
        <div class="toggle-wrap">
          <button
            type="button"
            class="toggle-switch"
            :class="{ on: form.callableByOthers }"
            @click="form.callableByOthers = !form.callableByOthers"
            role="switch"
            :aria-checked="form.callableByOthers"
          >
            <span class="toggle-knob"></span>
          </button>
        </div>
      </div>

      <p class="advanced-desc">
        目前仅可以被SOLO模式中的 SOLO Coder 调用。<a href="#" class="link">帮助文档</a>
      </p>

      <template v-if="form.callableByOthers">
        <div class="form-field required">
          <label>英文标识名</label>
          <input
            v-model="form.englishId"
            type="text"
            placeholder="被调用时的唯一英文标识名称，例如：project-analyzer"
            maxlength="50"
            class="agent-input"
          />
          <span class="char-count">{{ form.englishId.length }}/50</span>
        </div>

        <div class="form-field required">
          <label>何时调用</label>
          <textarea
            v-model="form.whenToCall"
            placeholder="请描述其他智能体调用该智能体的合适场景和时机"
            maxlength="5000"
            class="agent-textarea"
            rows="5"
          ></textarea>
          <span class="char-count">{{ form.whenToCall.length }}/5000</span>
        </div>
      </template>
    </section>

    <!-- 工具 - 内置 -->
    <section class="agent-section tools-section">
      <h3 class="tools-title">工具 - 内置</h3>
      <ul class="tools-list">
        <li
          v-for="tool in builtInTools"
          :key="tool.id"
          class="tool-item"
          @click="toggleTool(tool.id)"
        >
          <label class="tool-checkbox">
            <input type="checkbox" :checked="form.enabledTools.includes(tool.id)" @change.stop="toggleTool(tool.id)">
            <span class="checkmark"></span>
          </label>
          <span class="tool-icon" :aria-label="tool.name">
            <!-- 阅读 -->
            <svg v-if="tool.id === 'reading'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            <!-- 编辑 -->
            <svg v-else-if="tool.id === 'editing'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            <!-- 终端 -->
            <svg v-else-if="tool.id === 'terminal'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
            <!-- 预览 -->
            <svg v-else-if="tool.id === 'preview'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <!-- 联网搜索 -->
            <svg v-else-if="tool.id === 'web_search'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <!-- 下载资料 -->
            <svg v-else-if="tool.id === 'download_to_knowledge'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <!-- 知识库检索 -->
            <svg v-else-if="tool.id === 'knowledge_search'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="m9 9 2 2-2 2"/><path d="M13 13h3"/></svg>
          </span>
          <span class="tool-name">{{ tool.name }}</span>
          <span class="tool-desc">{{ tool.desc }}</span>
        </li>
      </ul>
    </section>

    <!-- 底部操作 -->
    <div class="agent-actions">
      <button type="button" class="btn-cancel" @click="showHistory">取消</button>
      <button type="button" class="btn-submit" @click="handleSubmit">保存</button>
    </div>

    </template>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { agentApi } from '@/api'

const emit = defineEmits(['close'])

const BUILTIN_TOOL_IDS = ['reading', 'editing', 'terminal', 'preview', 'web_search', 'download_to_knowledge', 'knowledge_search']

const builtInTools = [
  { id: 'reading', name: '阅读', desc: '对文件进行检索和查看' },
  { id: 'editing', name: '编辑', desc: '对文件进行增删和编辑' },
  { id: 'terminal', name: '终端', desc: '在终端运行命令并获取状态和结果' },
  { id: 'preview', name: '预览', desc: '在生成前端结果后提供预览入口' },
  { id: 'web_search', name: '联网搜索', desc: '搜索网页内容' },
  { id: 'download_to_knowledge', name: '下载资料', desc: '下载资料（PDF、网页）并保存到知识库' },
  { id: 'knowledge_search', name: '知识库检索', desc: '搜索知识库中的相关资料' }
]

// 页面状态：编辑中 or 历史列表
const isEditing = ref(false)
const editingAgent = ref(null)
const agentList = ref([])
const historyLoading = ref(false)

const form = reactive({
  name: '',
  prompt: '',
  callableByOthers: true,
  englishId: '',
  whenToCall: '',
  enabledTools: [...BUILTIN_TOOL_IDS]
})

function toggleTool(id) {
  const idx = form.enabledTools.indexOf(id)
  if (idx === -1) form.enabledTools.push(id)
  else form.enabledTools.splice(idx, 1)
}

async function loadAgentList() {
  historyLoading.value = true
  try {
    const res = await agentApi.list({})
    if (res.code === 200) {
      agentList.value = res.data?.agents || []
    }
  } catch (e) {
    console.error('加载智能体列表失败', e)
  } finally {
    historyLoading.value = false
  }
}

function showHistory() {
  loadAgentList()
  isEditing.value = false
  editingAgent.value = null
  resetForm()
}

function startCreate() {
  resetForm()
  editingAgent.value = null
  isEditing.value = true
}

function editAgent(agent) {
  editingAgent.value = agent
  form.name = agent.name || ''
  form.prompt = agent.prompt || ''
  form.callableByOthers = agent.callable_by_others ?? true
  form.englishId = agent.english_id || ''
  form.whenToCall = agent.when_to_call || ''
  form.enabledTools = agent.enabled_tools?.length ? agent.enabled_tools : [...BUILTIN_TOOL_IDS]
  isEditing.value = true
}

function resetForm() {
  form.name = ''
  form.prompt = ''
  form.callableByOthers = true
  form.englishId = ''
  form.whenToCall = ''
  form.enabledTools = [...BUILTIN_TOOL_IDS]
}

async function deleteAgent(id) {
  try {
    await agentApi.delete(id)
    ElMessage.success('删除成功')
    loadAgentList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const handleSubmit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入智能体名称')
    return
  }
  if (form.callableByOthers && !form.englishId.trim()) {
    ElMessage.warning('请输入英文标识名')
    return
  }
  if (form.callableByOthers && !form.whenToCall.trim()) {
    ElMessage.warning('请描述何时调用')
    return
  }
  try {
    const payload = {
      name: form.name,
      prompt: form.prompt,
      callable_by_others: form.callableByOthers,
      english_id: form.englishId,
      when_to_call: form.whenToCall,
      enabled_tools: form.enabledTools
    }
    if (editingAgent.value) {
      await agentApi.update(editingAgent.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await agentApi.create(payload)
      ElMessage.success('创建成功')
    }
    showHistory()
  } catch (e) {
    ElMessage.error(editingAgent.value ? '更新失败' : '创建失败')
  }
}

// 初始化时加载列表
loadAgentList()
</script>

<style scoped>
.agent-page {
  background: #ffffff;
  color: #1a1a1a;
  min-height: 100%;
  padding: 20px 24px 24px;
  font-size: 14px;
}

/* 面包屑 */
.agent-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
}

.breadcrumb-item {
  color: #9ca3af;
}

.breadcrumb-item.current {
  color: #1a1a1a;
  font-weight: 500;
}

.breadcrumb-sep {
  color: #d1d5db;
}

.breadcrumb-help {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.breadcrumb-help:hover {
  color: #6b7280;
  background: #f3f4f6;
}

/* 顶部操作 */
.agent-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 24px;
}

.btn-smart-generate {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-smart-generate:hover {
  opacity: 0.95;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-smart-generate svg {
  flex-shrink: 0;
}

/* 区块 */
.agent-section {
  margin-bottom: 24px;
}

.breadcrumb-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.breadcrumb-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.breadcrumb-btn:hover {
  color: #6b7280;
  background: #f3f4f6;
}

/* 历史记录列表 */
.agent-history-list {
  padding-bottom: 16px;
}

.agent-history-header {
  margin-bottom: 16px;
}

.agent-history-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.agent-history-loading,
.agent-history-empty {
  text-align: center;
  padding: 32px;
  color: #9ca3af;
  font-size: 14px;
}

.agent-history-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.agent-history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s;
}

.agent-history-item:hover {
  border-color: #6366f1;
  background: #eef2ff;
}

.agent-history-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #eef2ff;
  color: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.agent-history-info {
  flex: 1;
  min-width: 0;
}

.agent-history-name {
  display: block;
  font-weight: 600;
  font-size: 14px;
  color: #1a1a1a;
  margin-bottom: 2px;
}

.agent-history-time {
  display: block;
  font-size: 12px;
  color: #9ca3af;
}

.agent-history-delete {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #d1d5db;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  flex-shrink: 0;
  transition: all 0.2s;
}

.agent-history-delete:hover {
  background: #fee2e2;
  color: #ef4444;
}

.agent-history-footer {
  margin-top: 16px;
}

.btn-create-new {
  width: 100%;
  padding: 10px;
  background: #ffffff;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  color: #6366f1;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-new:hover {
  border-color: #6366f1;
  background: #eef2ff;
}

.avatar-upload {
  margin-bottom: 20px;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  background: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  color: #9ca3af;
}

.avatar-placeholder:hover {
  border-color: #6366f1;
  color: #6366f1;
}

.avatar-plus {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: #6366f1;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
}

/* 表单 */
.form-field {
  margin-bottom: 20px;
  position: relative;
}

.form-field label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
}

.form-field.required label::after {
  content: '*';
  color: #ef4444;
  margin-left: 2px;
}

.agent-input {
  width: 100%;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #1a1a1a;
  font-size: 14px;
  transition: border-color 0.2s;
}

.agent-input::placeholder {
  color: #9ca3af;
}

.agent-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.char-count {
  position: absolute;
  right: 12px;
  bottom: 12px;
  font-size: 12px;
  color: #9ca3af;
}

.form-field:has(.agent-textarea) .char-count {
  bottom: 8px;
}

.agent-textarea {
  width: 100%;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #1a1a1a;
  font-size: 14px;
  resize: vertical;
  min-height: 120px;
  transition: border-color 0.2s;
}

.agent-textarea::placeholder {
  color: #9ca3af;
}

.agent-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* 工具 - 内置 */
.tools-section {
  margin-bottom: 20px;
}

.tools-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.tools-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: #f9fafb;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background 0.2s;
}

.tool-item:last-child {
  border-bottom: none;
}

.tool-item:hover {
  background: #f3f4f6;
}

.tool-checkbox {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-checkbox input {
  position: absolute;
  opacity: 0;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.tool-checkbox .checkmark {
  position: relative;
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  transition: all 0.2s;
}

.tool-checkbox input:checked + .checkmark {
  background: #6366f1;
  border-color: #6366f1;
}

.tool-checkbox input:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.tool-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #6b7280;
  flex-shrink: 0;
}

.tool-name {
  font-weight: 500;
  color: #1a1a1a;
  min-width: 56px;
}

.tool-desc {
  font-size: 12px;
  color: #6b7280;
  margin-left: auto;
}

/* 高级配置卡片 */
.advanced-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  background: #f9fafb;
}

.advanced-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.advanced-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.advanced-title-row h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.badge-solo {
  padding: 2px 8px;
  background: #dcfce7;
  color: #166534;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.icon-info {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.icon-info:hover {
  color: #6b7280;
  background: #e5e7eb;
}

.toggle-wrap {
  flex-shrink: 0;
}

.toggle-switch {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: #d1d5db;
  border: none;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch.on {
  background: #6366f1;
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle-switch.on .toggle-knob {
  transform: translateX(20px);
}

.advanced-desc {
  margin: 0 0 20px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.advanced-desc .link {
  color: #6366f1;
  text-decoration: none;
}

.advanced-desc .link:hover {
  text-decoration: underline;
}

.advanced-card .form-field {
  margin-bottom: 16px;
}

.advanced-card .form-field:last-of-type {
  margin-bottom: 0;
}

/* 底部操作 */
.agent-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #404040;
}

.btn-cancel {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #d1d5db;
  color: #374151;
}

.btn-submit {
  padding: 10px 20px;
  background: #6366f1;
  border: none;
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit:hover {
  background: #4f46e5;
}
</style>
