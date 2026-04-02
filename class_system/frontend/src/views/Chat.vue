<template>
  <div class="workspace-page chat-workspace" :data-mode="selectedMode">

    <!-- Spline background -->
    <div class="spline-bg" aria-hidden="true">
      <iframe
        src="https://my.spline.design/r4xbot-dpye6cAdCqIk9Shjc9Edr4Zw/"
        frameborder="0" width="100%" height="100%"
      ></iframe>
    </div>
    <!-- Central light beam -->
    <div class="center-beam" aria-hidden="true"></div>

    <!-- Decorative glass bubbles (floating question prompts) -->
    <transition name="bubble-out">
      <div v-if="!hasStarted" class="bubble-field" aria-hidden="true">
        <div class="glass-bubble" style="--bx: 30%; --by: 8%; --bw: 250px; --bh: 76px; --br: 22px; --bg-h: 170deg;">
          <span class="bubble-tag"># 章节总结</span>
          <p class="bubble-text">用一句话概括概率论中的贝叶斯定理</p>
        </div>
        <div class="glass-bubble" style="--bx: 8%; --by: 18%; --bw: 220px; --bh: 80px; --br: 18px; --bg-h: 135deg;">
          <span class="bubble-tag"># 课程问题</span>
          <p class="bubble-text">如何理解函数的单调性与导数的关系？</p>
        </div>
        <div class="glass-bubble" style="--bx: 62%; --by: 12%; --bw: 200px; --bh: 72px; --br: 16px; --bg-h: 210deg;">
          <span class="bubble-tag"># 知识检索</span>
          <p class="bubble-text">光的折射定律及其在生活中的应用</p>
        </div>
        <div class="glass-bubble" style="--bx: 70%; --by: 48%; --bw: 230px; --bh: 78px; --br: 20px; --bg-h: 45deg;">
          <span class="bubble-tag"># 作业疑问</span>
          <p class="bubble-text">求函数 y = x³ − 3x 的极值点</p>
        </div>
        <div class="glass-bubble" style="--bx: 5%; --by: 60%; --bw: 210px; --bh: 74px; --br: 16px; --bg-h: 280deg;">
          <span class="bubble-tag"># 概念辨析</span>
          <p class="bubble-text">向量叉积与点积的本质区别是什么？</p>
        </div>
      </div>
    </transition>

    <!-- Chat layout -->
    <div class="chat-layout">
      <div class="chat-col">
        <div class="chat-shell" :class="{ 'is-started': hasStarted }">

          <!-- 持久顶栏 -->
          <div class="top-persistent-bar">
            <!-- 会话轨迹 -->
            <div class="toolbar-dropdown">
              <button class="pill-btn" :class="{ active: showHistory }" @click="showHistory = !showHistory; showSources = false">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6.5 3.5v3l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                会话轨迹
                <span class="history-count" v-if="conversationHistory.length">{{ conversationHistory.length }}</span>
              </button>
              <transition name="dropdown-pop">
                <div v-if="showHistory && conversationHistory.length > 0" class="dropdown-card history-panel">
                  <div class="history-panel-header">
                    <span class="history-panel-title">历史会话</span>
                    <button class="clear-all-btn" @click="conversationHistory = []; showHistory = false; currentConversationIndex = -1; messages = []; hasStarted = false">
                      清空全部
                    </button>
                  </div>
                  <div class="resource-list">
                    <div v-for="(item, index) in conversationHistory" :key="item.id"
                      class="chat-history-item" :class="{ active: currentConversationIndex === index }"
                      @click="loadConversation(index)">
                      <div class="chat-history-item__main">
                        <strong>{{ item.title }}</strong>
                        <span>{{ item.time }}</span>
                      </div>
                      <button class="chat-history-item__delete" @click="deleteConversation(index, $event)" title="删除此会话">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                          <path d="M2 3h8M5 3V2h2v1M4.5 3v6M7.5 3v6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- 引用与动作（仅在对话开始后显示） -->
            <div v-if="hasStarted" class="toolbar-dropdown">
              <button class="pill-btn" :class="{ active: showSources }" @click="showSources = !showSources; if(showSources) showHistory = false">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <path d="M2 2.5h9M2 6.5h6M2 10.5h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                引用与动作
              </button>
              <transition name="dropdown-pop">
                <div v-if="showSources" class="dropdown-card">
                  <div class="timeline-list">
                    <div v-for="source in activeSources" :key="source.title" class="timeline-item">
                      <h4>{{ source.title }}</h4>
                      <p>{{ source.summary }}</p>
                    </div>
                  </div>
                  <div class="chip-list" style="margin-top:12px">
                    <router-link to="/knowledge" class="chip">知识资产</router-link>
                    <router-link to="/graph" class="chip">知识图谱</router-link>
                    <router-link to="/homework" class="chip">作业中心</router-link>
                    <router-link to="/portrait" class="chip">学习画像</router-link>
                  </div>
                </div>
              </transition>
            </div>

            <!-- 新建会话按钮 -->
            <button v-if="hasStarted" class="new-chat-btn" @click="createNewChat" title="新建会话">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Welcome header -->
          <transition name="header-out">
            <div v-if="!hasStarted" class="welcome-header">
              <div class="glow-title-wrap"></div>
            </div>
          </transition>

          <!-- Top spacer -->
          <div class="top-spacer" :class="{ 'top-spacer--gone': hasStarted }"></div>

          <!-- Chat stream + 右侧代码预览面板 -->
          <transition name="stream-in">
            <div v-if="hasStarted" class="chat-main-row">
              <!-- 左侧：聊天消息流 -->
              <div class="chat-stream-box" ref="streamRef">
              <transition name="card-in">
                <div v-if="showPreviewCard" class="question-preview-card">
                  <div class="preview-icon">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M8 5v3M8 10v1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="preview-content">
                    <span class="preview-label">正在分析您的问题</span>
                    <p class="preview-text">{{ lastQuestion }}</p>
                  </div>
                </div>
              </transition>

              <div v-for="(msg, index) in messages" :key="`${msg.role}-${index}`"
                class="chat-message" :class="[msg.role, { streaming: streamingIndex === index }]">
                <div v-if="msg.role === 'user'" class="chat-avatar user">
                  <span>{{ userInitial }}</span>
                </div>
                <div class="chat-bubble" :class="msg.role">
                  <div class="chat-bubble__meta">
                    <strong>{{ msg.role === 'user' ? '提问' : 'AI 回答' }}</strong>
                    <span>{{ msg.time }}</span>
                  </div>
                  <!-- 工具调用卡片（智能体模式下显示在内容之前） -->
                  <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="agent-calls-list">
                    <AgentCallCard
                      v-for="call in msg.toolCalls"
                      :key="call.id"
                      :title="call.title"
                      :tool-name="call.tool"
                      :status="call.status"
                      :args="call.args"
                      :result="call.result"
                      :steps="call.steps || []"
                    />
                  </div>
                  <p class="chat-content">
                    <span
                      class="chat-text"
                      :class="{ 'text-reveal': streamingIndex === index }"
                      v-html="renderContent(msg.content || '')"
                      @click="onRunnableCodeClick"
                    ></span>
                    <span v-if="streamingIndex === index" class="typing-cursor"></span>
                  </p>
                </div>
              </div>

              <div v-if="isLoading && streamingIndex === -1" class="chat-loading">
                <div class="chat-loading__dots"><span></span><span></span><span></span></div>
                <p>AI 正在检索知识库并生成回答</p>
              </div>
            </div>

            <!-- 右侧：代码运行结果面板 -->
            <transition name="code-panel-slide">
              <div v-if="activeCodePreview" class="code-preview-panel">
                <div class="code-preview-panel__header">
                  <div class="code-preview-panel__title">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <rect x="1" y="1" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M5 5.5l-2 2.5 2 2.5M11 5.5l2 2.5-2 2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>{{ activeCodePreview.htmlPreviewUrl ? 'HTML 预览' : (activeCodePreview.langLabel + ' 运行结果') }}</span>
                  </div>
                  <button class="code-preview-panel__close" @click="activeCodePreview = null" title="关闭">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                      <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                  </button>
                </div>

                <!-- HTML 预览：iframe 内嵌 -->
                <iframe
                  v-if="activeCodePreview.htmlPreviewUrl"
                  :src="activeCodePreview.htmlPreviewUrl"
                  class="code-preview-panel__iframe"
                  sandbox="allow-scripts allow-same-origin"
                  title="HTML Preview"
                ></iframe>

                <!-- Python/Java 输出区域 -->
                <template v-else>
                  <div class="code-preview-panel__code">
                    <pre><code>{{ activeCodePreview.code }}</code></pre>
                  </div>
                  <div class="code-preview-panel__output"
                    :class="{
                      success: activeCodePreview.status === 'done' && activeCodePreview.success,
                      error:   activeCodePreview.status === 'done' && !activeCodePreview.success,
                      running: activeCodePreview.status === 'running'
                    }">
                    <div class="code-preview-panel__output-meta">
                      <span class="code-preview-panel__status">
                        <span v-if="activeCodePreview.status === 'running'">⏳ 正在执行...</span>
                        <span v-else-if="activeCodePreview.success">✅ 执行成功</span>
                        <span v-else>❌ 执行出错</span>
                      </span>
                      <span v-if="activeCodePreview.status !== 'running'" class="code-preview-panel__time">⏱ {{ activeCodePreview.executionTime }}s</span>
                    </div>
                    <pre v-if="activeCodePreview.status !== 'running' && activeCodePreview.stdout" class="code-preview-panel__stdout">{{ activeCodePreview.stdout }}</pre>
                    <pre v-if="activeCodePreview.status !== 'running' && (activeCodePreview.stderr || activeCodePreview.error)" class="code-preview-panel__stderr">{{ activeCodePreview.stderr || activeCodePreview.error }}</pre>
                    <div v-if="activeCodePreview.status !== 'running' && !activeCodePreview.stdout && !activeCodePreview.stderr && !activeCodePreview.error" class="code-preview-panel__empty">
                      （无输出）
                    </div>
                  </div>
                </template>
              </div>
            </transition>
          </div>
          </transition>

          <!-- Composer -->
          <div class="composer-wrap">
            <div class="composer-glow" aria-hidden="true"></div>
            <!-- 附件列表 - 显示在 composer-box 上方 -->
            <div v-if="uploadedFiles.length > 0" class="attachments-bar">
              <div v-for="(file, idx) in uploadedFiles" :key="idx" class="attachment-chip">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 7.5L7.5 13.5a4 4 0 01-5.657-5.657l5.657-5.657a2.5 2.5 0 013.536 3.536L5.379 11.47a1 1 0 01-1.414-1.414L9 5" stroke="currentColor" stroke-width="1.4"/>
                </svg>
                <span>{{ file.name }}</span>
                <button class="attachment-remove" @click="removeFile(idx)">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="composer-box">
              <textarea
                ref="inputRef"
                v-model="inputMessage"
                class="composer-input"
                :placeholder="hasStarted ? '输入课程问题、作业疑问或知识检索意图' : '询问任何课程问题'"
                rows="3"
                @keydown.enter.exact.prevent="sendMessage"
                @input="autoResize"
              ></textarea>
              <div class="composer-footer">
                <div class="composer-left">
                  <div class="mode-slider">
                    <div class="mode-slider__track" :data-active="selectedMode"
                      :style="{ '--thumb-x': modeThumbX + 'px', '--thumb-w': modeThumbW + 'px' }">
                      <div class="mode-slider__thumb"></div>
                      <button v-for="(mode, i) in modeOptions" :key="mode.value"
                        :ref="el => modeRefs[i] = el"
                        class="mode-slider__item" :class="{ active: selectedMode === mode.value }"
                        :data-mode="mode.value"
                        @click="selectMode(mode.value, i)" :title="mode.label">
                        <svg v-if="mode.value === 'general'" width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <circle cx="7" cy="7" r="2.5" fill="currentColor"/>
                          <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.2" opacity="0.5"/>
                        </svg>
                        <svg v-else-if="mode.value === 'knowledge'" width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M2 3h10M2 7h7M2 11h5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                        </svg>
                        <svg v-else-if="mode.value === 'agent'" width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <circle cx="7" cy="5" r="2.5" stroke="currentColor" stroke-width="1.2"/>
                          <path d="M2 12c0-2.21 2.239-4 5-4s5 1.79 5 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                          <circle cx="11" cy="4" r="1.5" fill="currentColor" opacity="0.7"/>
                        </svg>
                        <span class="mode-label">{{ mode.label }}</span>
                      </button>
                    </div>
                  </div>
                </div>
                <div class="composer-right">
                  <!-- 隐藏的文件输入框 -->
                  <input
                    ref="fileInputRef"
                    type="file"
                    class="file-input-hidden"
                    :accept="acceptFileTypes"
                    multiple
                    @change="handleFileSelect"
                  />
                  <button class="tool-btn" :class="{ active: isUploading }" title="上传附件" @click="triggerFileSelect">
                    <svg v-if="!isUploading" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 7.5L7.5 13.5a4 4 0 01-5.657-5.657l5.657-5.657a2.5 2.5 0 013.536 3.536L5.379 11.47a1 1 0 01-1.414-1.414L9 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <svg v-else class="spin" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="30" stroke-dashoffset="10"/>
                    </svg>
                  </button>
                  <button class="send-btn" :disabled="!inputMessage.trim() || isLoading" @click="sendMessage">
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                      <path d="M7.5 11.5V3.5M3.5 7.5l4-4 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, onMounted, watch } from 'vue'
import api, { ragApi, agentApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import InfoState from '@/components/ui/InfoState.vue'
import AgentCallCard from '@/components/AgentCallCard.vue'

const authStore = useAuthStore()
const conversationHistory = ref([])

// 页面加载时初始化 thumb 位置 & 加载历史会话
onMounted(() => {
  // 加载历史会话
  try {
    const saved = localStorage.getItem('chat-conversation-history')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed)) {
        conversationHistory.value = parsed
      }
    }
  } catch (e) {
    console.error('Failed to load conversation history:', e)
  }

  nextTick(() => {
    setTimeout(() => {
      const activeIndex = modeOptions.findIndex(m => m.value === selectedMode.value)
      if (activeIndex >= 0) updateThumb(activeIndex)
    }, 100)
  })
})

// 自动保存历史会话到 localStorage
watch(conversationHistory, (val) => {
  try {
    localStorage.setItem('chat-conversation-history', JSON.stringify(val))
  } catch (e) {
    console.error('Failed to save conversation history:', e)
  }
}, { deep: true })

// 加载保存的配置
function loadAgentConfig() {
  try {
    const saved = localStorage.getItem('agent-config-full')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load agent config:', e)
  }
  // 返回默认配置
  return {
    model: 'kimi-k2.5',
    temperature: 70,
    topP: 90,
    maxTokens: 4096,
    frequencyPenalty: 0,
    presencePenalty: 0,
    tools: []
  }
}

const userInitial = computed(() => (authStore.user?.username || 'U').charAt(0).toUpperCase())

const modeOptions = [
  { label: '通用问答', value: 'general' },
  { label: '知识库对话', value: 'knowledge' },
  { label: '智能体', value: 'agent' }
]

const selectedMode = ref('general')
const selectedAgentId = ref('')
const agentList = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const hasStarted = ref(false)
const showHistory = ref(false)
const showSources = ref(false)
const currentConversationIndex = ref(-1)
const messages = ref([])
const inputRef = ref(null)
const streamRef = ref(null)
const modeRefs = ref([])
const modeThumbX = ref(0)
const modeThumbW = ref(0)
const lastQuestion = ref('')
const showPreviewCard = ref(false)
const streamingIndex = ref(-1) // 正在流式输出的消息索引

// 追踪活跃工具调用（key 为消息索引）
const agentCallsMap = ref({}) // { [msgIndex]: AgentCall[] }
const activeToolCalls = ref([]) // 当前正在进行的工具调用列表

// 文件上传相关
const fileInputRef = ref(null)
const uploadedFiles = ref([]) // { name, path, size }
const isUploading = ref(false)
const currentSessionId = ref('')
const acceptFileTypes = '.txt,.pdf,.doc,.docx,.md,.py,.js,.ts,.html,.css,.json,.xml,.csv,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.webp'

function triggerFileSelect() {
  fileInputRef.value?.click()
}

async function handleFileSelect(event) {
  const files = event.target.files
  if (!files || files.length === 0) return

  // 生成或复用 session_id
  if (!currentSessionId.value) {
    currentSessionId.value = `chat_${Date.now()}`
  }

  isUploading.value = true
  try {
    for (const file of files) {
      // 限制文件大小（10MB）
      if (file.size > 10 * 1024 * 1024) {
        alert(`文件 ${file.name} 超过10MB限制`)
        continue
      }

      const res = await agentApi.uploadFile(currentSessionId.value, file)
      if (res.code === 200) {
        uploadedFiles.value.push({
          name: file.name,
          path: res.data.path,
          size: file.size,
          rawFile: file  // 保存原始文件用于读取为 base64
        })
      } else {
        console.error('文件上传失败:', res.message)
        alert(`文件 ${file.name} 上传失败`)
      }
    }
  } catch (e) {
    console.error('文件上传错误:', e)
    alert('文件上传出错，请重试')
  } finally {
    isUploading.value = false
    // 清空文件选择
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

function removeFile(index) {
  uploadedFiles.value.splice(index, 1)
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 读取文件为 base64
function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      // 去掉 data:image/xxx;base64, 前缀
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// 获取文件的 MIME 类型
// 渲染消息内容：支持 LaTeX 公式 + Markdown + 可运行代码卡片
import katex from 'katex'

/** 支持运行的语言 */
const RUNNABLE_LANGS = ['html', 'htm', 'python', 'java', 'py', 'java'] // py -> python

const LANG_LABEL = {
  html: 'HTML', htm: 'HTML',
  python: 'Python', py: 'Python',
  java: 'Java'
}

/** 判断语言是否需要后端执行（Python/Java） */
function needsServerExecute(lang) {
  const l = (lang || '').trim().toLowerCase()
  return l === 'python' || l === 'py' || l === 'java'
}

/** 判断是否为可在浏览器中直接运行的完整 HTML 文档 */
function isRunnableHtml(lang, raw) {
  const trimmed = raw.trim()
  const langLower = (lang || '').trim().toLowerCase()
  if (langLower === 'html' || langLower === 'htm') return true
  if (!langLower && /^(<!DOCTYPE|<html\b)/i.test(trimmed)) return true
  return false
}

/** 通用构建代码卡片函数 */
function buildRunnableCard(lang, raw, rawForPreview) {
  const l = (lang || '').trim().toLowerCase()
  const normalized = (l === 'py') ? 'python' : l
  const label = LANG_LABEL[normalized] || lang.toUpperCase()
  const isServer = needsServerExecute(normalized)

  let b64 = ''
  try {
    b64 = btoa(unescape(encodeURIComponent(rawForPreview)))
  } catch {
    return `<pre class="code-block"><code>${raw}</code></pre>`
  }

  const runAction = isServer ? 'run-code' : 'preview-html'
  const runTitle = isServer ? '在服务器上运行代码' : '在新窗口中运行预览'
  const runBtnClass = isServer ? 'runnable-code-card__btn runnable-code-card__btn--run runnable-code-card__btn--server' : 'runnable-code-card__btn runnable-code-card__btn--run'

  return (
    `<div class="runnable-code-card" data-lang="${normalized}" data-preview-b64="${b64}">` +
    `<pre class="code-block runnable-code-card__pre"><code>${raw}</code></pre>` +
    `<div class="runnable-code-card__footer">` +
    `<span class="runnable-code-card__lang-tag">${label}</span>` +
    `<div class="runnable-code-card__actions">` +
    `<button type="button" class="runnable-code-card__btn" data-action="copy-code" title="复制源代码">` +
    `<svg class="runnable-code-card__icon" width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">` +
    `<rect x="5" y="5" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>` +
    `<path d="M3 11V4h7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>` +
    `</svg>复制</button>` +
    `<button type="button" class="${runBtnClass}" data-action="${runAction}" title="${runTitle}">` +
    `<svg class="runnable-code-card__icon" width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">` +
    `<path d="M5 3.5v9l7-4.5L5 3.5z"/>` +
    `</svg>运行</button>` +
    `</div></div>` +
    `</div>`
  )
}

/** 点击处理：复制、HTML 预览、Python/Java 执行 */
const activeCodePreview = ref(null)

async function handleCardAction(btn, card) {
  const action = btn.getAttribute('data-action')
  const lang = card.getAttribute('data-lang')
  const b64 = card.getAttribute('data-preview-b64')

  if (!b64) return
  let raw = ''
  try {
    raw = decodeURIComponent(escape(window.atob(b64)))
  } catch {
    ElMessage.error('无法解析代码数据')
    return
  }

  if (action === 'copy-code') {
    const ok = await navigator.clipboard.writeText(raw).then(() => true, () => false)
    ElMessage.success(ok ? '已复制到剪贴板' : '复制失败')
    return
  }

  if (action === 'preview-html') {
    // 生成 blob URL，在右侧面板 iframe 中内嵌预览
    const blob = new Blob([raw], { type: 'text/html;charset=utf-8' })
    const blobUrl = URL.createObjectURL(blob)
    const l = (lang || '').trim().toLowerCase()
    const langLabel = (l === 'htm' || l === 'html') ? 'HTML' : lang.toUpperCase()
    activeCodePreview.value = {
      langLabel,
      code: raw,
      htmlPreviewUrl: blobUrl,
      success: true,
      stdout: '',
      stderr: '',
      error: null,
      executionTime: 0,
      status: 'done'
    }
    return
  }

  if (action === 'run-code') {
    const l = (lang || '').trim().toLowerCase()
    const langLabel = LANG_LABEL[l === 'py' ? 'python' : l] || lang.toUpperCase()
    activeCodePreview.value = {
      langLabel,
      code: raw,
      htmlPreviewUrl: null,
      success: false,
      stdout: '',
      stderr: '',
      error: null,
      executionTime: 0,
      status: 'running'
    }

    btn.disabled = true
    btn.textContent = '运行中...'
    try {
      const res = await api.code.execute({
        code: raw,
        language: l === 'py' ? 'python' : l,
        timeout: 30
      })
      if (res && res.code === 200) {
        const data = res.data || {}
        activeCodePreview.value = {
          langLabel,
          code: raw,
          htmlPreviewUrl: null,
          success: !!data.success,
          stdout: data.stdout || '',
          stderr: data.stderr || '',
          error: data.error || null,
          executionTime: data.execution_time || 0,
          status: 'done'
        }
      } else {
        activeCodePreview.value = {
          langLabel, code: raw,
          htmlPreviewUrl: null,
          success: false,
          stdout: '',
          stderr: '',
          error: res?.message || '执行失败',
          executionTime: 0,
          status: 'done'
        }
        ElMessage.error(res?.message || '执行失败')
      }
    } catch (err) {
      console.error('Code execution error:', err)
      activeCodePreview.value = {
        langLabel, code: raw,
        htmlPreviewUrl: null,
        success: false,
        stdout: '',
        stderr: '',
        error: err?.message || '请求失败，请检查后端服务是否启动',
        executionTime: 0,
        status: 'done'
      }
      ElMessage.error('代码执行接口请求失败，请检查后端服务是否启动')
    } finally {
      btn.disabled = false
      btn.innerHTML = `<svg class="runnable-code-card__icon" width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 3.5v9l7-4.5L5 3.5z"/></svg>运行`
    }
  }
}

function onRunnableCodeClick(e) {
  const btn = e.target.closest('[data-action]')
  if (!btn || !(btn instanceof HTMLElement)) return
  const card = btn.closest('.runnable-code-card')
  if (!card) return
  e.preventDefault()
  e.stopPropagation()
  handleCardAction(btn, card)
}

function renderContent(text) {
  if (!text) return ''
  // 1. 处理 $$...$$ 块级公式（优先提取，防止被后续 Markdown 处理破坏）
  let result = text
  const blockMathRegex = /\$\$([\s\S]+?)\$\$/g
  const blockMatches = []
  let m
  while ((m = blockMathRegex.exec(text)) !== null) {
    blockMatches.push({ raw: m[0], latex: m[1], index: m.index })
  }
  // 用占位符替换所有块公式
  for (let i = blockMatches.length - 1; i >= 0; i--) {
    const match = blockMatches[i]
    try {
      katex.renderToString(match.latex.trim(), { displayMode: true, throwOnError: false })
      result = result.slice(0, match.index) + `\x00BLOCK_MATH_${i}\x00` + result.slice(match.index + match.raw.length)
    } catch (e) {
      result = result.slice(0, match.index) + match.raw + result.slice(match.index + match.raw.length)
    }
  }
  // 2. 提取 fenced 代码块（在全局转义之前保留原始 HTML，用于「运行」预览）
  const codeBlocks = []
  result = result.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const raw = String(code).replace(/\r\n/g, '\n')
    const id = codeBlocks.length
    codeBlocks.push({ lang, raw })
    return `\x00CODE_BLOCK_${id}\x00`
  })
  // 3. HTML 转义（防止 XSS）
  result = result.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 4. 还原代码块：可运行卡片包裹，其余为普通 pre
  for (let i = 0; i < codeBlocks.length; i++) {
    const { lang, raw } = codeBlocks[i]
    const escaped = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    const l = (lang || '').trim().toLowerCase()
    const isRunnable = isRunnableHtml(lang, raw) || needsServerExecute(l)
    const inner = isRunnable ? buildRunnableCard(l, escaped, raw) : `<pre class="code-block"><code>${escaped}</code></pre>`
    result = result.replace(`\x00CODE_BLOCK_${i}\x00`, inner)
  }
  // 5. Markdown 处理（代码块已处理，不再匹配 ```）
  result = result
    // 行内代码
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    // 标题
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // 列表
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    // 加粗
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 斜体
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // 行级公式 $...$（行内）
    .replace(/\$([^$\n]+?)\$/g, (_, latex) => {
      try {
        return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false })
      } catch (e) {
        return '$' + latex + '$'
      }
    })
    // 换行
    .replace(/\n/g, '<br>')
  // 4. 恢复块公式
  for (let i = 0; i < blockMatches.length; i++) {
    try {
      const html = katex.renderToString(blockMatches[i].latex.trim(), { displayMode: true, throwOnError: false })
      result = result.replace(`\x00BLOCK_MATH_${i}\x00`, html)
    } catch (e) {
      result = result.replace(`\x00BLOCK_MATH_${i}\x00`, '$$' + blockMatches[i].latex + '$$')
    }
  }
  // 5. 合并连续 <li> 为 <ul>
  result = result.replace(/(<li>.*<\/li>(\s*<li>.*<\/li>)*)/g, match => '<ul>' + match + '</ul>')
  return result
}

function getFileMimeType(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  const mimeTypes = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'bmp': 'image/bmp',
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain',
    'md': 'text/markdown',
    'py': 'text/x-python',
    'js': 'text/javascript',
    'ts': 'text/typescript',
    'html': 'text/html',
    'css': 'text/css',
    'json': 'application/json',
    'xml': 'application/xml',
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  }
  return mimeTypes[ext] || 'application/octet-stream'
}

async function selectMode(value, index) {
  selectedMode.value = value
  nextTick(() => updateThumb(index))

  // 切换到智能体模式时，自动加载并选择智能体
  if (value === 'agent') {
    try {
      const res = await agentApi.list()
      if (res.code === 200 && res.data.agents?.length > 0) {
        selectedAgentId.value = res.data.agents[0].id
        agentList.value = res.data.agents
      } else {
        selectedAgentId.value = ''
        agentList.value = []
      }
    } catch (e) {
      console.error('加载智能体列表失败:', e)
      selectedAgentId.value = ''
      agentList.value = []
    }
  }
}

function updateThumb(index) {
  const el = modeRefs.value[index]
  if (!el) return
  modeThumbX.value = el.offsetLeft
  modeThumbW.value = el.offsetWidth
}

const activeSources = ref([
  { title: '引用来源将在这里显示', summary: '命中文档、知识块和建议动作会伴随回答一起出现。' }
])

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}

function formatTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function loadConversation(index) {
  currentConversationIndex.value = index
  const h = conversationHistory.value[index]
  messages.value = h ? [...h.messages] : []
  activeSources.value = h?.sources?.length ? h.sources : activeSources.value
  hasStarted.value = true
  showHistory.value = false
}

function deleteConversation(index, event) {
  event.stopPropagation()
  conversationHistory.value.splice(index, 1)
  if (currentConversationIndex.value === index) {
    currentConversationIndex.value = -1
    messages.value = []
    hasStarted.value = false
  } else if (currentConversationIndex.value > index) {
    currentConversationIndex.value--
  }
}

function createNewChat() {
  // 保存当前会话到历史（如果当前有内容）
  if (currentConversationIndex.value > -1 && messages.value.length > 0) {
    conversationHistory.value[currentConversationIndex.value].messages = [...messages.value]
  }
  // 重置状态（不清空历史列表）
  messages.value = []
  currentConversationIndex.value = -1
  hasStarted.value = false
  showHistory.value = false
  showSources.value = false
  streamingIndex.value = -1
  activeToolCalls.value = []
  activeSources.value = [
    { title: '引用来源将在这里显示', summary: '命中文档、知识块和建议动作会伴随回答一起出现。' }
  ]
  // 清空上传的文件
  uploadedFiles.value = []
  currentSessionId.value = ''
  // 清空输入框
  inputMessage.value = ''
  if (inputRef.value) {
    inputRef.value.value = ''
    inputRef.value.style.height = 'auto'
  }
  if (streamRef.value) streamRef.value.scrollTop = 0
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return

  if (!hasStarted.value) hasStarted.value = true

  // 加载保存的配置
  const agentConfig = loadAgentConfig()

  // 构建消息内容，如果有附件则转换为多模态格式
  let fullMessage = text
  let filesData = null
  
  if (uploadedFiles.value.length > 0) {
    // 将上传的文件转换为 base64 格式
    filesData = []
    for (const file of uploadedFiles.value) {
      try {
        const fileData = await readFileAsBase64(file.rawFile)
        filesData.push({
          type: getFileMimeType(file.name),
          data: fileData
        })
      } catch (e) {
        console.error('读取文件失败:', e)
      }
    }
    
    // 清空上传的文件（附件只使用一次）
    uploadedFiles.value = []
  }
  
  // 额外提示 - 更明确地告知Agent文件已内嵌在消息中
  let fileHint = ''
  if (filesData && filesData.length > 0) {
    const fileTypes = filesData.map(f => {
      if (f.type.startsWith('image/')) return f.type.replace('image/', '').toUpperCase() + '图片'
      return f.type.split('/').pop().toUpperCase() + '文档'
    }).join('、')
    fileHint = `\n\n【用户上传了 ${filesData.length} 个文件（${fileTypes}），这些文件的内容已经内嵌在上述消息中，请直接查看并回答。】`
  }

  messages.value.push({ role: 'user', content: text, time: formatTime() })
  lastQuestion.value = text
  showPreviewCard.value = false
  if (currentConversationIndex.value === -1) {
    conversationHistory.value.unshift({
      id: `conv_${Date.now()}`,
      title: text.slice(0, 18),
      time: new Date().toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }),
      messages: [], sources: []
    })
    currentConversationIndex.value = 0
  }
  inputMessage.value = ''
  await nextTick()
  if (inputRef.value) inputRef.value.style.height = 'auto'
  if (streamRef.value) streamRef.value.scrollTop = streamRef.value.scrollHeight
  isLoading.value = true

  // 添加一个空的AI消息占位符用于流式更新
  const aiMsgIndex = messages.value.length
  streamingIndex.value = aiMsgIndex
  messages.value.push({ role: 'ai', content: '', time: formatTime() })

  try {
    // 智能体模式 - 使用流式输出
    if (selectedMode.value === 'agent') {
      if (!selectedAgentId.value) {
        messages.value[aiMsgIndex].content = '请先选择一个智能体'
        isLoading.value = false
        streamingIndex.value = -1
        return
      }

      // 【诊断】确认 filesData 是否正确
      const _fd0len = filesData && filesData.length > 0 ? (filesData[0].data ? filesData[0].data.length : 0) : 0
      console.log(`[Agent Chat] === 发送前诊断 ===`)
      console.log(`[Agent Chat] filesData === null ? ${filesData === null}`)
      console.log(`[Agent Chat] filesData.length = ${filesData ? filesData.length : 'N/A'}`)
      console.log(`[Agent Chat] filesData[0].data length = ${_fd0len}`)
      console.log(`[Agent Chat] message = "${(fullMessage + (fileHint || '')).slice(0, 80)}"`)
      if (filesData && filesData.length > 0) {
        console.log(`[Agent Chat] filesData[0].type = ${filesData[0].type}, filesData[0].data前20字 = "${filesData[0].data ? filesData[0].data.slice(0, 20) : 'N/A'}"`)
      } else {
        console.error('[Agent Chat] ⚠️ filesData 为空！uploadedFiles.value.length =', uploadedFiles.value.length)
      }

      const response = await agentApi.chatStream({
        message: fullMessage + (fileHint || ''),
        student_id: authStore.user?.id || 'guest',
        session_id: `agent_${selectedAgentId.value}_${Date.now()}`,
        files: filesData,
        model: agentConfig.model,
        temperature: agentConfig.temperature / 100,
        topP: agentConfig.topP / 100,
        maxTokens: agentConfig.maxTokens,
        frequencyPenalty: agentConfig.frequencyPenalty,
        presencePenalty: agentConfig.presencePenalty,
        use_memory: agentConfig.memoryEnabled !== false,
        agent_type: agentConfig.agentType || 'tutor',
        personality: agentConfig.personality || 'balanced',
        custom_prompt: agentConfig.systemPrompt || ''
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Agent stream response error:', response.status, errorText)
        messages.value[aiMsgIndex].content = `请求失败 (${response.status})：请稍后重试`
        isLoading.value = false
        streamingIndex.value = -1
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''

      // 初始化该消息的工具调用追踪
      activeToolCalls.value = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)

              if (parsed.type === 'tool_start') {
                // 仅对子代理调用（delegate_task）创建卡片，普通工具调用忽略
                if (parsed.tool === 'delegate_task') {
                  const call = {
                    id: `call_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
                    tool: parsed.tool,
                    title: '调用子代理',
                    status: 'running',
                    args: parsed.args,
                    result: undefined,
                    steps: []
                  }
                  activeToolCalls.value.push(call)
                  if (!messages.value[aiMsgIndex].toolCalls) {
                    messages.value[aiMsgIndex].toolCalls = []
                  }
                  messages.value[aiMsgIndex].toolCalls.push(call)
                }
              } else if (parsed.type === 'tool_end') {
                // 仅更新子代理卡片的状态
                const callIndex = activeToolCalls.value.findIndex(c => c.tool === parsed.tool)
                if (callIndex >= 0) {
                  const call = activeToolCalls.value[callIndex]
                  const isError = parsed.result?.error
                  call.status = isError ? 'error' : 'done'
                  call.result = parsed.result
                }
              } else if (parsed.type === 'content') {
                // AI 回复内容
                fullResponse += parsed.content
                messages.value[aiMsgIndex].content = fullResponse
              } else if (parsed.type === 'done') {
                // 完成
              } else if (parsed.type === 'error') {
                fullResponse += `\n⚠️ ${parsed.error}\n`
                messages.value[aiMsgIndex].content = fullResponse
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }

        await nextTick()
        if (streamRef.value) streamRef.value.scrollTop = streamRef.value.scrollHeight
      }

      isLoading.value = false
      streamingIndex.value = -1
      return
    }

    // 普通模式（通用问答 / 知识库对话）
    // agentConfig 的滑块值是 0-100，API 需要 0-1 float 及 snake_case 命名
    // 通用问答和知识库问答不需要 tools
    const response = await ragApi.chatStream({
      query: text,
      student_id: authStore.user?.id || 'guest',
      session_id: `chat_${selectedMode.value}`,
      mode: selectedMode.value === 'general' ? 'general' : 'learning',
      model: agentConfig.model,
      temperature: agentConfig.temperature / 100,
      topP: agentConfig.topP / 100,
      maxTokens: agentConfig.maxTokens,
      frequencyPenalty: agentConfig.frequencyPenalty,
      presencePenalty: agentConfig.presencePenalty
      // 不传 tools，通用问答和知识库问答不需要工具调用
    })

    // 检查响应状态
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Stream response error:', response.status, errorText)
      messages.value[aiMsgIndex].content = `请求失败 (${response.status})：请稍后重试`
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''
    let hasContent = false
    let lastUpdateTime = 0
    const MIN_UPDATE_INTERVAL = 16 // 约60fps

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              hasContent = true
              fullResponse += parsed.content
              const now = Date.now()
              // 节流：限制UI更新频率
              if (now - lastUpdateTime >= MIN_UPDATE_INTERVAL || parsed.content.length > 10) {
                messages.value[aiMsgIndex].content = fullResponse
                lastUpdateTime = now
                await nextTick()
                if (streamRef.value) streamRef.value.scrollTop = streamRef.value.scrollHeight
              }
            }
            if (parsed.done) {
              messages.value[aiMsgIndex].content = fullResponse || '已收到问题，但当前没有返回有效答案。'
            }
            if (parsed.error) {
              console.error('Stream error:', parsed.error)
              messages.value[aiMsgIndex].content = '流式输出出错：' + parsed.error
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 确保最终内容被显示
    if (fullResponse) {
      messages.value[aiMsgIndex].content = fullResponse
    } else if (hasContent) {
      messages.value[aiMsgIndex].content = fullResponse
    } else {
      messages.value[aiMsgIndex].content = '等待响应中，请稍后...'
    }

  } catch (err) {
    console.error('Chat error:', err)
    messages.value[aiMsgIndex].content = '网络或服务异常：' + (err.message || '请稍后重试')
  } finally {
    isLoading.value = false
    streamingIndex.value = -1
    await nextTick()
    if (streamRef.value) streamRef.value.scrollTop = streamRef.value.scrollHeight
    if (currentConversationIndex.value > -1) {
      conversationHistory.value[currentConversationIndex.value].messages = [...messages.value]
    }
  }
}
</script>

<style scoped>
/* ── Page ── */
.chat-workspace {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ── Spline background ── */
.spline-bg {
  position: absolute;
  inset: -24px;
  width: calc(100% + 48px);
  height: calc(100% + 48px);
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.spline-bg iframe {
  width: 100%;
  height: 100%;
  display: block;
}

/* ── Central light beam ── */
.center-beam {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 100%;
  background: radial-gradient(ellipse 160px 100% at 50% 0%,
    rgba(37, 99, 235, 0.12) 0%,
    rgba(245, 158, 11, 0.06) 40%,
    transparent 100%);
  pointer-events: none;
  z-index: 2;
  animation: beam-pulse 4s ease-in-out infinite;
}

@keyframes beam-pulse {
  0%, 100% { opacity: 0.7; }
  50%       { opacity: 1.0; }
}

/* ── Decorative glass bubbles ── */
.bubble-field {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.glass-bubble {
  position: absolute;
  left: var(--bx);
  top: var(--by);
  width: var(--bw);
  min-height: var(--bh);
  border-radius: var(--br);
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.52);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.06),
    0 1px 4px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  gap: 4px;
  animation: float-bubble 6s ease-in-out infinite;
  animation-delay: var(--delay, 0s);
}

@keyframes float-bubble {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-8px); }
}

.bubble-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(99, 102, 241, 0.7);
  background: linear-gradient(135deg,
    rgba(99, 102, 241, 0.15) 0%,
    rgba(59, 130, 246, 0.15) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 20px;
  padding: 2px 8px;
  display: inline-block;
  align-self: flex-start;
}

.bubble-text {
  font-size: 12px;
  line-height: 1.5;
  color: rgba(30, 30, 40, 0.75);
  font-weight: 500;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.glass-bubble:nth-child(1) { --delay: 0s;    animation-duration: 7s; }
.glass-bubble:nth-child(2) { --delay: -1.5s; animation-duration: 5.5s; }
.glass-bubble:nth-child(3) { --delay: -3s;   animation-duration: 8s; }
.glass-bubble:nth-child(4) { --delay: -0.8s; animation-duration: 6.5s; }
.glass-bubble:nth-child(5) { --delay: -4.2s; animation-duration: 7.5s; }

/* ── Chat layout ── */
.chat-layout {
  position: relative;
  z-index: 3;
  display: flex;
  flex: 1;
  min-height: 0;
  height: 100%;
}

.chat-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  flex: 1;
  padding: 0 24px;
}

/* ── Shell ── */
.chat-shell {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

/* ── 聊天主行（左侧消息 + 右侧预览面板并排） ── */
.chat-main-row {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

/* ── Welcome header ── */
.welcome-header {
  text-align: center;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
}

.glow-title-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 60px 80px;
}

/* ── Top spacer ── */
.top-spacer {
  flex: 1;
  min-height: 80px;
  transition: flex 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              min-height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.top-spacer--gone {
  flex: 0 !important;
  min-height: 0 !important;
}

/* ── Chat toolbar ── */
.chat-toolbar {
  display: flex;
  gap: 8px;
  padding: 0 0 12px;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  flex-shrink: 0;
  align-items: flex-start;
}

/* ── New chat button ── */
.new-chat-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  background: linear-gradient(135deg, #3b82f6 0%, #f97316 50%, #ef4444 100%);
  color: #fff;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.35), 0 1px 3px rgba(239, 68, 68, 0.2);
  transition: all 0.2s ease;
}

.new-chat-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.5), 0 2px 6px rgba(239, 68, 68, 0.3);
}

.new-chat-btn:active {
  transform: scale(0.95);
}

/* ── Toolbar dropdown ── */
.toolbar-dropdown {
  position: relative;
}

.dropdown-card {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 280px;
  max-width: 360px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  padding: 12px 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.dropdown-pop-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.dropdown-pop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-pop-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
.dropdown-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

/* ── History panel ── */
.history-panel {
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px) saturate(1.4);
  -webkit-backdrop-filter: blur(18px) saturate(1.4);
  padding: 12px 14px;
}

/* ── Chat stream ── */
.chat-stream-box {
  max-width: none;
  width: 100%;
  margin: 0 0 16px 0;
  padding: 20px 24px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(18px) saturate(1.4);
  -webkit-backdrop-filter: blur(18px) saturate(1.4);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  min-height: 0;
}

/* ── Question preview card ── */
.question-preview-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(1.6);
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 4px 24px rgba(37, 99, 235, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.preview-icon {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(0, 200, 224, 0.15));
  border: 1px solid rgba(37, 99, 235, 0.25);
  color: #2563eb;
  flex-shrink: 0;
  animation: icon-pulse 1.5s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
}

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-label {
  font-size: 11px;
  font-weight: 600;
  color: #2563eb;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

/* ── Sources panel ── */
.sources-panel {
  margin-top: 12px;
  border-radius: 12px;
  border: 1px solid rgba(48, 112, 255, 0.15);
  background: rgba(48, 112, 255, 0.04);
  padding: 14px;
}

/* ── Chat messages ── */
.chat-message {
  display: flex;
  gap: 12px;
  animation: fade-in-up 0.4s ease both;
}
/* AI messages: avatar + bubble on left */
.chat-message.ai {
  flex-direction: row;
  gap: 0;
}
/* User messages: bubble + avatar on right */
.chat-message.user {
  flex-direction: row-reverse;
  gap: 12px;
}
.chat-avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 13px;
}
.chat-avatar.ai {
  background: linear-gradient(135deg, rgba(48,112,255,0.15), rgba(0,200,224,0.10));
  border: 1px solid rgba(48,112,255,0.20);
}
.chat-avatar.user {
  background: linear-gradient(135deg, var(--ink-800), var(--ink-700));
  color: var(--text-primary);
}
.chat-bubble {
  flex: 1;
  max-width: 75%;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
}
.chat-bubble.ai {
  background: rgba(48,112,255,0.06);
  border-color: rgba(48,112,255,0.15);
}
.chat-bubble.user {
  background: rgba(37, 99, 235, 0.12);
  border-color: rgba(37, 99, 235, 0.20);
}
/* AI 消息全宽无气泡 */
.chat-message.ai .chat-bubble {
  flex: 1;
  max-width: 100%;
  background: transparent;
  border: none;
  padding: 0;
}
.chat-message.ai .chat-bubble__meta {
  display: none;
}
.chat-message.ai .chat-bubble p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.8;
}
.chat-bubble__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 11px;
}
.chat-bubble__meta strong { color: var(--text-tertiary); }
.chat-bubble p {
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
  margin: 0;
}

.chat-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(48,112,255,0.04);
  border: 1px solid rgba(48,112,255,0.10);
}
.chat-loading p { color: var(--text-tertiary); font-size: 13px; margin: 0; }
.chat-loading__dots { display: flex; gap: 4px; }
.chat-loading__dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-400);
  animation: pulse-dot 1.4s ease-in-out infinite;
}

/* 流式输出文字渐变动画 */
.chat-content {
  position: relative;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
  min-height: 1.5em;
}

.chat-text {
  display: inline;
  transition: opacity 0.15s ease;
}

/* 流式输出时的打字机光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: linear-gradient(180deg, var(--brand-400) 0%, var(--brand-500) 100%);
  margin-left: 3px;
  vertical-align: text-bottom;
  border-radius: 1px;
  animation: blink-cursor 0.7s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(48, 112, 255, 0.4);
}

@keyframes blink-cursor {
  0%, 100% { opacity: 1; transform: scaleY(1); }
  50% { opacity: 0.5; transform: scaleY(0.8); }
}

/* 流式消息的入场动画 */
.chat-message.streaming {
  animation: message-appear 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes message-appear {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 文字渐现效果 */
.text-reveal {
  background: linear-gradient(
    90deg,
    var(--text-secondary) 0%,
    var(--text-secondary) 100%
  );
  background-size: 200% 100%;
  background-position: 100% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 0.1s ease forwards;
}

/* 正在输出时的文字微微发光 */
.chat-message.streaming .chat-text:not(:empty) {
  text-shadow: 0 0 20px rgba(48, 112, 255, 0.15);
}

/* 流式消息添加柔和光晕效果 */
.chat-message.streaming .chat-bubble {
  box-shadow: 0 0 30px rgba(48, 112, 255, 0.1);
  border-color: rgba(48, 112, 255, 0.25);
}

/* 用户消息入场动画 */
.chat-message.user {
  animation: user-message-in 0.3s ease-out;
}

@keyframes user-message-in {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.chat-loading__dots span:nth-child(2) { animation-delay: 0.2s; }
.chat-loading__dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-dot {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
  40%           { transform: scale(1);   opacity: 1; }
}

/* ── Composer ── */
.composer-wrap {
  position: relative;
  flex-shrink: 0;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  margin-top: auto;
}

.composer-glow {
  position: absolute;
  top: -3px;
  left: 5%;
  right: 5%;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(37, 99, 235, 0.8) 20%,
    rgba(245, 158, 11, 1.0) 50%,
    rgba(37, 99, 235, 0.8) 80%,
    transparent 100%);
  filter: blur(5px);
  animation: glow-breathe 3s ease-in-out infinite;
  pointer-events: none;
  z-index: 1;
}

@keyframes glow-breathe {
  0%, 100% {
    opacity: 0.65;
    left: 10%;
    right: 10%;
  }
  50% {
    opacity: 1;
    left: 2%;
    right: 2%;
  }
}

.composer-box {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(37,99,235,0.14);
  border-radius: 16px;
  padding: 14px 14px 10px;
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--t-base) ease, box-shadow var(--t-base) ease;
}
.composer-box:focus-within {
  border-color: rgba(37,99,235,0.35);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.08), var(--shadow-sm);
}
.composer-input {
  width: 100%;
  min-height: 64px;
  max-height: 200px;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.7;
  font-family: inherit;
  overflow-y: auto;
  box-sizing: border-box;
}
.composer-input::placeholder { color: var(--text-muted); }
.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
}
.composer-left  { display: flex; align-items: center; gap: 8px; }
.composer-right { display: flex; align-items: center; gap: 6px; }

/* 文件上传 */
.file-input-hidden {
  display: none;
}

/* 附件列表 - 显示在 composer-box 上方 */
.attachments-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: rgba(37,99,235,0.04);
  border: 1px dashed rgba(37,99,235,0.2);
  border-radius: 10px;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px 4px 10px;
  background: rgba(37,99,235,0.08);
  border: 1px solid rgba(37,99,235,0.2);
  border-radius: 16px;
  font-size: 11px;
  color: #2563eb;
  max-width: 180px;
}

.attachment-chip svg {
  flex-shrink: 0;
  opacity: 0.7;
}

.attachment-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.attachment-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  transition: all 0.15s;
  opacity: 0.6;
}

.attachment-remove:hover {
  background: rgba(37,99,235,0.15);
  opacity: 1;
}

/* 上传中状态 */
.tool-btn.active {
  border-color: rgba(37,99,235,0.35);
  background: rgba(37,99,235,0.1);
  animation: pulse-upload 1s ease-in-out infinite;
}

@keyframes pulse-upload {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Mode slider */
.mode-slider { display: flex; align-items: center; }
.mode-slider__track {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(37,99,235,0.06);
  border: 1px solid rgba(37,99,235,0.14);
  border-radius: 20px;
  padding: 3px;
}
.mode-slider__thumb {
  position: absolute;
  top: 3px;
  bottom: 3px;
  left: var(--thumb-x, 3px);
  width: var(--thumb-w, 32px);
  background: rgba(37,99,235,0.15);
  border: 1px solid rgba(37,99,235,0.35);
  border-radius: 16px;
  transition: left 0.22s cubic-bezier(0.4,0,0.2,1), width 0.22s cubic-bezier(0.4,0,0.2,1);
  pointer-events: none;
}
.mode-slider__track[data-active="agent"] .mode-slider__thumb {
  background: rgba(62,207,110,0.15);
  border-color: rgba(62,207,110,0.4);
}
.mode-slider__item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.18s ease;
  white-space: nowrap;
}
.mode-slider__item.active { color: #2563eb; }
.mode-slider__item.active[data-mode="agent"] { color: #3ecf6e; }
.mode-slider__item .mode-label { display: none; }
.mode-slider__item.active .mode-label { display: inline; }

.tool-btn {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 1px solid rgba(37,99,235,0.14);
  background: rgba(37,99,235,0.04);
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--t-fast) ease;
}
.tool-btn:hover {
  border-color: rgba(37,99,235,0.28);
  color: var(--text-secondary);
}

.send-btn {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--brand-500);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: all var(--t-fast) ease;
}
.send-btn:hover:not(:disabled) {
  background: var(--brand-400);
  box-shadow: 0 0 10px rgba(37,99,235,0.35);
}
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* ── Pill buttons ── */
.pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(37,99,235,0.14);
  background: rgba(255,255,255,0.90);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--t-fast) ease;
  white-space: nowrap;
  align-self: flex-start;
  box-shadow: var(--shadow-xs);
}
.pill-btn:hover {
  border-color: rgba(37,99,235,0.28);
  color: var(--text-primary);
  background: rgba(255,255,255,0.98);
}
.pill-btn.active {
  border-color: rgba(74,140,255,0.35);
  background: rgba(74,140,255,0.08);
  color: #2563eb;
}
.pill-chevron { transition: transform 0.2s ease; opacity: 0.6; }
.pill-chevron.open { transform: rotate(180deg); }

/* ── Panels ── */
.panel-drop-enter-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.panel-drop-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.panel-drop-enter-from   { opacity: 0; transform: translateY(-6px); }
.panel-drop-leave-to     { opacity: 0; transform: translateY(-6px); }

/* ── History items ── */
.resource-list { display: flex; flex-direction: column; gap: 6px; }
.chat-history-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  padding: 9px 11px;
  border-radius: 9px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.02);
  color: var(--text-secondary);
  transition: all var(--t-fast) ease;
  cursor: pointer;
}
.chat-history-item:hover { background: rgba(255,255,255,0.04); border-color: var(--glass-border-hi); }
.chat-history-item.active {
  border-color: rgba(48,112,255,0.22);
  background: rgba(48,112,255,0.06);
}

.chat-history-item__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.chat-history-item__main strong {
  color: var(--text-primary);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chat-history-item__main span {
  color: var(--text-muted);
  font-size: 11px;
}

.chat-history-item__delete {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 5px;
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.3);
  cursor: pointer;
  opacity: 0.4;
}
.chat-history-item:hover .chat-history-item__delete { opacity: 1; }
.chat-history-item__delete:hover {
  background: rgba(239,68,68,0.15);
  color: #f87171;
}

/* ── Top persistent bar ── */
.top-persistent-bar {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  gap: 8px;
}

.history-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 999px;
  background: rgba(37,99,235,0.2);
  color: #60a5fa;
  font-size: 10px;
  font-weight: 600;
}

/* ── History panel ── */
.history-panel {
  min-width: 260px;
  max-width: 320px;
}

.history-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.history-panel-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #9ca3af;
}

.clear-all-btn {
  background: transparent;
  border: none;
  color: rgba(248,113,113,0.7);
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all var(--t-fast) ease;
}
.clear-all-btn:hover {
  background: rgba(239,68,68,0.12);
  color: #f87171;
}

/* ── Chip links ── */
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(37,99,235,0.08);
  border: 1px solid rgba(37,99,235,0.2);
  color: #2563eb;
  font-size: 11px;
  font-weight: 500;
  text-decoration: none;
  transition: all var(--t-fast) ease;
}
.chip:hover {
  background: rgba(37,99,235,0.15);
  border-color: rgba(37,99,235,0.35);
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ── Timeline/Sources ── */
.timeline-list { display: flex; flex-direction: column; gap: 10px; }
.timeline-item h4 { font-size: 12px; color: var(--text-primary); margin: 0 0 3px; }
.timeline-item p  { font-size: 11px; color: var(--text-muted); margin: 0; line-height: 1.6; }

/* ── Transitions ── */
.header-out-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.header-out-leave-to     { opacity: 0; transform: translateY(-10px); }

.card-in-enter-active {
  transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.card-in-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.card-in-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.96);
}
.card-in-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

.stream-in-enter-active { transition: opacity 0.4s ease 0.05s, transform 0.4s ease 0.05s; }
.stream-in-enter-from   { opacity: 0; transform: translateY(12px); }

.bubble-out-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.bubble-out-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* ── Dark mode ── */
:global([data-theme="dark"]) .composer-box {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}
:global([data-theme="dark"]) .composer-box:focus-within {
  border-color: rgba(74,140,255,0.40);
  box-shadow: 0 0 0 3px rgba(74,140,255,0.10), 0 0 20px rgba(74,140,255,0.08);
}
:global([data-theme="dark"]) .tool-btn {
  border-color: var(--glass-border);
  background: transparent;
}
:global([data-theme="dark"]) .tool-btn:hover {
  border-color: var(--glass-border-hi);
}
:global([data-theme="dark"]) .pill-btn {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}
:global([data-theme="dark"]) .pill-btn:hover {
  border-color: var(--glass-border-hi);
  background: rgba(255,255,255,0.05);
}
:global([data-theme="dark"]) .chat-stream-box {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.10);
}
:global([data-theme="dark"]) .chat-bubble {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}
:global([data-theme="dark"]) .chat-bubble.ai {
  background: rgba(37, 99, 235, 0.06);
}
:global([data-theme="dark"]) .chat-avatar.user {
  background: linear-gradient(135deg, var(--brand-600), var(--emerald-500));
  color: #020a04;
}
:global([data-theme="dark"]) .glow-title {
  background: none;
  -webkit-text-fill-color: #fff;
}
:global([data-theme="dark"]) .mode-slider__track {
  background: rgba(255,255,255,0.04);
  border-color: var(--glass-border);
}

/* 深色模式流式输出 */
:global([data-theme="dark"]) .typing-cursor {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.5);
}
:global([data-theme="dark"]) .chat-message.streaming .chat-bubble {
  box-shadow: 0 0 40px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}
:global([data-theme="dark"]) .chat-message.streaming .chat-text:not(:empty) {
  text-shadow: 0 0 30px rgba(96, 165, 250, 0.2);
}

/* KaTeX 公式样式 */
.katex-display {
  margin: 12px 0 !important;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px 0;
}
.katex { font-size: 1.05em !important; }

/* 工具调用卡片列表 */
.agent-calls-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

/* Markdown 渲染样式 */
.chat-text h1, .chat-text h2, .chat-text h3 {
  margin: 10px 0 6px;
  font-weight: 600;
}
.chat-text h1 { font-size: 1.2em; }
.chat-text h2 { font-size: 1.1em; }
.chat-text h3 { font-size: 1em; }
.chat-text ul {
  list-style: none;
  padding: 0 0 0 16px;
  margin: 6px 0;
}
.chat-text ul > li::before {
  content: '•';
  margin-right: 6px;
  color: var(--brand-400, #60a5fa);
}
.chat-text .inline-code {
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 4px;
  padding: 1px 5px;
  font-family: 'Fira Code', monospace;
  font-size: 0.88em;
  color: var(--violet-400, #a78bfa);
}
.chat-text .code-block {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 12px 14px;
  margin: 8px 0;
  overflow-x: auto;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.85em;
  line-height: 1.5;
}

/* 可运行代码卡片 */
.chat-text .runnable-code-card {
  margin: 10px 0 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.22);
  overflow: hidden;
  max-width: 100%;
}
.chat-text .runnable-code-card__pre {
  margin: 0;
  padding: 12px 14px;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.84em;
  line-height: 1.55;
  overflow-x: auto;
  white-space: pre;
}
.chat-text .runnable-code-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.chat-text .runnable-code-card__lang-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}
.chat-text .runnable-code-card__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chat-text .runnable-code-card__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 999px;       /* 圆角矩形 */
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.88);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  white-space: nowrap;
}
.chat-text .runnable-code-card__btn:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.26);
  transform: translateY(-1px);
}
.chat-text .runnable-code-card__btn:active {
  transform: translateY(0);
}
.chat-text .runnable-code-card__btn--run {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.45), rgba(99, 102, 241, 0.45));
  border-color: rgba(99, 102, 241, 0.55);
  color: #fff;
}
.chat-text .runnable-code-card__btn--run:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.6), rgba(99, 102, 241, 0.6));
  border-color: rgba(99, 102, 241, 0.7);
}
.chat-text .runnable-code-card__btn--server {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.45), rgba(16, 185, 129, 0.45));
  border-color: rgba(16, 185, 129, 0.55);
  color: #fff;
}
.chat-text .runnable-code-card__btn--server:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.6), rgba(16, 185, 129, 0.6));
  border-color: rgba(16, 185, 129, 0.7);
}
.chat-text .runnable-code-card__icon {
  flex-shrink: 0;
  opacity: 0.9;
}

.code-preview-panel {
  width: 380px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 20, 0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  height: 100%;
}
.code-preview-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.code-preview-panel__title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}
.code-preview-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: background 0.15s;
}
.code-preview-panel__close:hover {
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 1);
}
.code-preview-panel__code {
  flex-shrink: 0;
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(0, 0, 0, 0.2);
}
.code-preview-panel__code pre {
  margin: 0;
  padding: 10px 14px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.8em;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.75);
  white-space: pre;
}
.code-preview-panel__output {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.code-preview-panel__output-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.code-preview-panel__output.success .code-preview-panel__output-meta {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}
.code-preview-panel__output.error .code-preview-panel__output-meta {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}
.code-preview-panel__status {
  display: flex;
  align-items: center;
  gap: 5px;
}
.code-preview-panel__time {
  opacity: 0.7;
  font-size: 11px;
}
.code-preview-panel__stdout {
  margin: 0;
  padding: 10px 14px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.82em;
  line-height: 1.55;
  color: #a5f3fc;
  white-space: pre-wrap;
  word-break: break-all;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  flex: 1;
}
.code-preview-panel__stderr {
  margin: 0;
  padding: 10px 14px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.82em;
  line-height: 1.55;
  color: #fca5a5;
  white-space: pre-wrap;
  word-break: break-all;
  background: rgba(239, 68, 68, 0.06);
  flex: 1;
}
.code-preview-panel__empty {
  padding: 20px 14px;
  text-align: center;
  color: rgba(255, 255, 255, 0.35);
  font-size: 12px;
  font-style: italic;
}
.code-preview-panel__output[status="running"] .code-preview-panel__stdout {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}
.code-preview-panel__output[status="running"] .code-preview-panel__stdout::before {
  content: '⏳ 正在执行...';
  display: block;
}

/* HTML 预览 iframe */
.code-preview-panel__iframe {
  flex: 1;
  width: 100%;
  border: none;
  background: #fff;
  border-radius: 0 0 16px 0;
}

/* 右侧面板滑入动画（纯 width 过渡，自然挤压左侧） */
.code-panel-slide-enter-active,
.code-panel-slide-leave-active {
  transition: width 0.32s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.code-panel-slide-enter-from,
.code-panel-slide-leave-to {
  width: 0 !important;
}

:global([data-theme="dark"]) .chat-text .runnable-code-card {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.35);
}
</style>

<style>
/* v-html 动态注入的按钮不受 scoped 影响，需要全局样式 */
.runnable-code-card__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 999px !important;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.88);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.1s, box-shadow 0.15s;
  white-space: nowrap;
  font-family: inherit;
  line-height: 1;
}
.runnable-code-card__btn:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.26);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.runnable-code-card__btn:active {
  transform: translateY(0);
  box-shadow: none;
}
.runnable-code-card__btn--run {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.45), rgba(99, 102, 241, 0.45));
  border-color: rgba(99, 102, 241, 0.55);
  color: #fff;
}
.runnable-code-card__btn--run:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.65), rgba(99, 102, 241, 0.65));
  border-color: rgba(99, 102, 241, 0.7);
}
.runnable-code-card__btn--server {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.45), rgba(16, 185, 129, 0.45));
  border-color: rgba(16, 185, 129, 0.55);
  color: #fff;
}
.runnable-code-card__btn--server:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.65), rgba(16, 185, 129, 0.65));
  border-color: rgba(16, 185, 129, 0.7);
}
.runnable-code-card__btn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}
.runnable-code-card__icon {
  flex-shrink: 0;
}
</style>
