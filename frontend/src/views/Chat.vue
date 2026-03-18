<template>
  <div class="chat-page">
    <!-- 模糊背景层 -->
    <div class="chat-blur-background"></div>

    <!-- 历史记录侧边栏 -->
    <aside v-if="hasStartedConversation" class="chat-history-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h3>历史记录</h3>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline :points="sidebarCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"></polyline>
          </svg>
        </button>
      </div>
      <div class="history-list" v-if="conversationHistory.length > 0">
        <div
          v-for="(conv, idx) in conversationHistory"
          :key="idx"
          class="history-item"
          :class="{ active: idx === currentConversationIndex }"
          @click="loadConversation(idx)"
        >
          <span class="history-title">{{ conv.title }}</span>
          <span class="history-time">{{ conv.time }}</span>
        </div>
      </div>
      <div class="history-empty" v-else>
        <p>暂无对话</p>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="chat-main-container">
      <!-- 粒子效果 -->
      <vue-particles
        id="chat-particles"
        class="chat-particles"
        :class="{ 'particles-hidden': hasStartedConversation }"
        :options="particlesOptions"
      />

      <!-- 英雄区 + 输入框 + 模式按钮 -->
      <div class="chat-hero" :class="{ 'hero-hidden': hasStartedConversation }">
        <h1 class="hero-title">有新的学习问题了吗？</h1>

        <div class="hero-input-card">
          <div class="hero-input-inner">
            <input
              v-model="inputMessage"
              type="text"
              placeholder="&#35810;&#38382;&#20219;&#20309;&#23398;&#20064;&#38382;&#39064;"
              @keydown.enter="sendMessage(inputMessage)"
            />
            <div class="hero-input-chips">
              <div class="hero-mode-group" ref="modeButtonsGroup">
                <div class="hero-mode-slider" :style="modeSliderStyle"></div>
                <button type="button" class="hero-mode-btn" :class="{ active: selectedMode === 0 }" @click="selectMode(0)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                  <span class="hero-mode-label">通用问答</span>
                  <span class="hero-mode-width-calc">通用问答</span>
                </button>
                <button type="button" class="hero-mode-btn" :class="{ active: selectedMode === 1 }" @click="selectMode(1)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  <span class="hero-mode-label">知识库对话</span>
                  <span class="hero-mode-width-calc">知识库对话</span>
                </button>
              </div>
              <button type="button" class="hero-attach-btn" title="上传文件">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                </svg>
              </button>
              <button type="button" class="hero-send-btn" :disabled="!inputMessage.trim()" :class="{ active: inputMessage.trim() }" @click="sendMessage(inputMessage)">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m22 2-7 20-4-9-9-4 20-7z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="hero-suggestions">
          <p class="hero-suggest-label">&#25512;&#33616;&#38382;&#39064;</p>
          <div class="hero-actions">
            <button
              v-for="tag in heroTags"
              :key="tag"
              class="hero-pill"
              @click="sendMessage(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>
      </div>

      <!-- ???????????????????? + ?????? -->
      <div v-show="hasStartedConversation" class="chat-content">
        <div class="chat-messages" ref="messagesContainer">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-wrapper"
            :class="{ 'ai-message': msg.role === 'ai', 'user-message': msg.role === 'user' }"
          >
            <div class="message-avatar">
              <span v-if="msg.role === 'ai'">AI</span>
              <span v-else>&#25105;</span>
            </div>
            <div class="message-content">
              <div class="message-bubble" v-html="formatMessage(msg.content)"></div>
              <div class="message-meta">
                <span class="message-time">{{ msg.time }}</span>
                <span v-if="msg.sources && msg.sources.length" class="source-count">
                  &#21442;&#32771;: {{ msg.sources.length }} &#26465;
                </span>
              </div>
              <div v-if="msg.role === 'ai'" class="message-actions">
                <button class="action-btn" @click="copyMessage(msg.content)" title="&#22797;&#21046;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                  </svg>
                </button>
                <button class="action-btn" @click="showFeedback(msg)" title="&#21453;&#39304;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <div v-if="isLoading" class="message-wrapper ai-message">
            <div class="message-avatar">AI</div>
            <div class="message-content">
              <div class="message-bubble typing">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <div class="input-mode-group" ref="inputModeGroup">
              <div class="input-mode-slider" :style="inputModeSliderStyle"></div>
              <button type="button" class="input-mode-btn" :class="{ active: selectedMode === 0 }" @click="selectMode(0)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                <span>通用问答</span>
              </button>
              <button type="button" class="input-mode-btn" :class="{ active: selectedMode === 1 }" @click="selectMode(1)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                <span>知识库对话</span>
              </button>
            </div>
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="sendMessage(inputMessage)"
              rows="1"
              ref="inputRef"
            ></textarea>
            <div class="input-actions">
              <button class="attach-btn" title="上传文件">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                </svg>
              </button>
              <button
                class="send-btn"
                @click="sendMessage(inputMessage)"
                :disabled="!inputMessage.trim() || isLoading"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- ???? -->
    <div v-if="showFeedbackModal" class="modal-overlay" @click.self="showFeedbackModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>&#35780;&#20215;</h3>
          <button class="modal-close" @click="showFeedbackModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>&#35831;&#36873;&#25321;&#24744;&#30340;&#21453;&#39304;&#31867;&#22411;&#65306;</p>
          <div class="feedback-options">
            <button
              v-for="type in feedbackTypes"
              :key="type.value"
              class="feedback-btn"
              :class="{ active: feedbackType === type.value }"
              @click="feedbackType = type.value"
            >
              {{ type.label }}
            </button>
          </div>
          <textarea
            v-model="feedbackComment"
            placeholder="&#36873;&#22635;&#65306;&#34917;&#20805;&#35828;&#26126;..."
            rows="3"
          ></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showFeedbackModal = false">&#21462;&#28040;</button>
          <button class="btn btn-primary" @click="submitFeedback">&#25552;&#20132;&#21453;&#39304;</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ragApi, chatApi, feedbackApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const particlesOptions = {
  fullScreen: { enable: false },
  background: { color: { value: 'transparent' } },
  fpsLimit: 60,
  detectRetina: true,
  interactivity: {
    events: { onHover: { enable: false }, onClick: { enable: false }, resize: true }
  },
  // ????
  particles: {
    number: { value: 30, density: { enable: true, area: 800 } },
    color: { value: '#93c5fd' },
    shape: { type: 'circle' },
    opacity: { value: 0.4 },
    size: { value: 70 },
    move: {
      enable: true,
      speed: { min: 0.5, max: 1.5 },
      direction: 'random',
      random: true,
      straight: false
    }
  },
  emitters: [
    {
      position: { x: 50, y: 50 },
      rate: { quantity: 2, delay: 0.4 },
      size: { width: 0, height: 0 },
      particles: {
        number: { value: 1 },
        color: { value: '#93c5fd' },
        shape: {
          type: 'circle',
          stroke: { width: 3, color: '#93c5fd' }
        },
        fill: false,
        opacity: {
          value: 1,
          animation: { enable: true, speed: 8, startValue: 'max', destroy: 'min', sync: true }
        },
        size: {
          value: { min: 30, max: 35 },
          animation: { enable: true, speed: 30, startValue: 'min', destroy: 100, sync: true }
        },
        move: { enable: false },
        life: { duration: { sync: true, value: 2.5 }, count: 1 }
      }
    }
  ]
}

const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)
const showFeedbackModal = ref(false)
const feedbackType = ref('')
const feedbackComment = ref('')
const currentFeedbackMsg = ref(null)

// ???????????????????????????????+???+?????
const hasStartedConversation = computed(() => messages.value.length > 0)

const sidebarCollapsed = ref(false)
const conversationHistory = ref([])
const currentConversationIndex = ref(-1)

const loadConversation = (index) => {
  currentConversationIndex.value = index
  const conv = conversationHistory.value[index]
  if (conv) {
    messages.value = conv.messages
  }
}

const heroTags = [
  'Python \u5165\u95E8',
  '\u673A\u5668\u5B66\u4E60',
  '\u6570\u636E\u7ED3\u6784',
  '\u7B97\u6CD5\u9898',
  'Web \u5F00\u53D1'
]

const selectedMode = ref(0)
const modeButtonsGroup = ref(null)
const modeSliderStyle = ref({})
const inputModeSliderStyle = ref({})
const inputModeGroup = ref(null)

function updateSliderStyle() {
  if (!modeButtonsGroup.value) return
  const buttons = modeButtonsGroup.value.querySelectorAll('.hero-mode-btn')
  const activeIdx = selectedMode.value
  const activeBtn = buttons[activeIdx]
  if (!activeBtn) return
  const wasActive = activeBtn.classList.contains('active')
  activeBtn.classList.add('active')
  const width = activeBtn.offsetWidth
  const left = activeBtn.offsetLeft
  if (!wasActive) activeBtn.classList.remove('active')
  modeSliderStyle.value = {
    width: `${width}px`,
    left: `${left}px`,
    transform: 'none'
  }
}

function updateInputModeSliderStyle() {
  if (!inputModeGroup.value) return
  const buttons = inputModeGroup.value.querySelectorAll('.input-mode-btn')
  const activeIdx = selectedMode.value
  const activeBtn = buttons[activeIdx]
  if (!activeBtn) return
  const wasActive = activeBtn.classList.contains('active')
  activeBtn.classList.add('active')
  const width = activeBtn.offsetWidth
  const left = activeBtn.offsetLeft
  if (!wasActive) activeBtn.classList.remove('active')
  inputModeSliderStyle.value = {
    width: `${width}px`,
    left: `${left}px`,
    transform: 'none'
  }
}

watch(selectedMode, () => {
  nextTick(() => {
    updateSliderStyle()
    updateInputModeSliderStyle()
  })
})

onMounted(() => {
  nextTick(() => {
    updateSliderStyle()
    updateInputModeSliderStyle()
  })
})
const selectMode = (idx) => {
  selectedMode.value = idx
  nextTick(() => {
    updateSliderStyle()
  })
}

const sidebarSections = ref([
  { title: '\u4F7F\u7528\u8BF4\u660E', content: '\u8F93\u5165\u95EE\u9898\u540E\uFF0CAI \u5C06\u57FA\u4E8E\u77E5\u8BC6\u5E93\u56DE\u7B54\u3002' },
  { title: '\u5EFA\u8BAE', content: '\u95EE\u9898\u5C3D\u91CF\u5177\u4F53\uFF0C\u4FBF\u4E8E\u83B7\u5F97\u66F4\u51C6\u786E\u7684\u7B54\u6848\u3002' }
])

const feedbackTypes = [
  { value: 'like', label: '\u6709\u5E2E\u52A9' },
  { value: 'dislike', label: '\u65E0\u5E2E\u52A9' },
  { value: 'correct', label: '\u7B54\u6848\u6709\u8BEF' },
  { value: 'additional', label: '\u9700\u8865\u5145' }
]

const sendMessage = async (text) => {
  if (!text.trim() || isLoading.value) return

  const userMsg = {
    role: 'user',
    content: text,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  messages.value.push(userMsg)

  // ???????????????
  const isNewConversation = messages.value.length === 1
  if (isNewConversation) {
    conversationHistory.value.unshift({
      title: text.slice(0, 20) + (text.length > 20 ? '...' : ''),
      time: new Date().toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }),
      messages: [...messages.value]
    })
    currentConversationIndex.value = 0
  }

  inputMessage.value = ''

  isLoading.value = true
  await nextTick()
  scrollToBottom()

  try {
    let res
    // 根据模式选择API：0=通用问答(chatApi)，1=知识库问答(ragApi)
    if (selectedMode.value === 1) {
      // 知识库问答模式
      res = await ragApi.chat({
        query: text,
        student_id: authStore.user?.id || 'default',
        session_id: 'default',
        use_rewrite: true,
        use_rerank: true,
        top_k: 5
      })

      if (res.code === 200 && res.data?.answer) {
        const aiMsg = {
          role: 'ai',
          content: res.data.answer,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          sources: res.data.sources || []
        }
        messages.value.push(aiMsg)
      } else {
        messages.value.push({
          role: 'ai',
          content: '\u62B1\u6B49\uFF0C\u672A\u80FD\u83B7\u53D6\u5230\u6709\u6548\u7B54\u6848\uFF0C\u8BF7\u68C0\u67E5\u77E5\u8BC6\u5E93\u6216\u7A0D\u540E\u91CD\u8BD5\u3002',
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          sources: []
        })
      }
    } else {
      // 通用问答模式 - 使用智能问答Chat API
      res = await chatApi.message({
        message: text,
        mode: 'general',
        student_id: authStore.user?.id || 'default',
        session_id: localStorage.getItem('chatSessionId') || undefined,
        course_id: undefined
      })

      if (res.code === 200 && res.data?.response) {
        // 保存session_id用于后续对话
        if (res.data.session_id) {
          localStorage.setItem('chatSessionId', res.data.session_id)
        }
        
        const aiMsg = {
          role: 'ai',
          content: res.data.response,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          sources: res.data.sources || [],
          knowledgePointIds: res.data.knowledge_point_ids || []
        }
        messages.value.push(aiMsg)
      } else {
        messages.value.push({
          role: 'ai',
          content: '\u62B1\u6B49\uFF0C\u672A\u80FD\u83B7\u53D6\u5230\u6709\u6548\u7B54\u6848\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002',
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          sources: []
        })
      }
    }
  } catch (error) {
    console.error('AI \u8BF7\u6C42\u5931\u8D25:', error)
    messages.value.push({
      role: 'ai',
      content: '\u7F51\u7EDC\u6216\u670D\u52A1\u5F02\u5E38\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      sources: []
    })
  }

  isLoading.value = false
  await nextTick()
  scrollToBottom()

  // ?????????????
  if (currentConversationIndex.value >= 0 && conversationHistory.value[currentConversationIndex.value]) {
    conversationHistory.value[currentConversationIndex.value].messages = [...messages.value]
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content) => {
  return content
    .replace(/\n/g, '<br>')
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

const copyMessage = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
  } catch (err) {
    console.error('\u590D\u5236\u5931\u8D25:', err)
  }
}

const showFeedback = (msg) => {
  currentFeedbackMsg.value = msg
  showFeedbackModal.value = true
  feedbackType.value = ''
  feedbackComment.value = ''
}

const submitFeedback = async () => {
  if (!feedbackType.value) return
  
  try {
    await feedbackApi.submit({
      answer_id: 'default',
      feedback_type: feedbackType.value,
      comment: feedbackComment.value,
      student_id: 'user_001'
    })
    showFeedbackModal.value = false
  } catch (error) {
    console.error('\u63D0\u4EA4\u53CD\u9988\u5931\u8D25:', error)
  }
}

onMounted(() => {
  scrollToBottom()
  nextTick(() => {
    modeSliderStyle.value
  })
})
</script>

<style scoped>
.chat-page {
  position: relative;
  overflow: hidden;
  display: flex;
  min-height: calc(100vh - 64px);
  background: white;
}

/* 模糊背景层 - 模仿登录弹窗效果 */
.chat-blur-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: white;
  filter: blur(20px);
  transform: scale(1.1);
}

.chat-particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  transition: opacity 0.6s ease;
  filter: blur(3px);
}

.chat-particles.particles-hidden {
  opacity: 0;
}

/* ?????? */
.chat-history-sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  transition: width 0.3s ease, transform 0.3s ease;
}

.chat-history-sidebar.collapsed {
  width: 0;
  transform: translateX(-260px);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e1b4b;
  margin: 0;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #6b7280;
  border-radius: 4px;
  transition: background 0.2s;
}

.collapse-btn:hover {
  background: #f3f4f6;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f3f4f6;
}

.history-item.active {
  background: #eff6ff;
}

.history-title {
  display: block;
  font-size: 14px;
  color: #374151;
  margin-bottom: 4px;
}

.history-time {
  font-size: 12px;
  color: #9ca3af;
}

.history-empty {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}

/* ??? */
.chat-main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.chat-hero.hero-hidden {
  display: none;
}

/* ???????/?????? */
.chat-hero {
  width: 100%;
  margin: 0 auto;
  padding: 60px 24px 80px;
  text-align: center;
  transition: all 0.3s ease;
  transform: translateY(30px);
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 26px;
  letter-spacing: -0.02em;
  line-height: 1.3;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ??????? */
.hero-input-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 24px;
  overflow: hidden;
  width: 72%;
  margin-left: auto;
  margin-right: auto;
}

.hero-input-card:focus-within {
  border-color: #94a3b8;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.hero-input-inner {
  padding: 22px 22px 22px;
  border-radius: 24px;
}

.hero-input-inner input {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #1e293b;
  outline: none;
  padding: 22px 0 25px;
}

.hero-input-inner input::placeholder {
  color: #94a3b8;
}

.hero-input-chips {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.hero-chips-group {
  display: inline-flex;
  align-items: center;
  padding: 4px 5px 4px 4px;
  background: #e2e8f0;
  border-radius: 9999px;
  gap: 2px;
  position: relative;
  overflow: hidden;
}

.hero-chip-slider {
  position: absolute;
  top: 4px;
  left: 4px;
  height: calc(100% - 8px);
  background: #fff;
  border-radius: 9999px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.hero-chip {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 9999px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  position: relative;
  z-index: 1;
}

.hero-chip:hover {
  color: #475569;
}

.hero-chip.active {
  color: #3b82f6;
}

.hero-send-btn {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #334155;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.hero-send-btn:hover:not(:disabled) {
  background: #475569;
}

.hero-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.hero-send-btn.active {
  background: #3b82f6;
  color: #fff;
}

.hero-send-btn.active:hover {
  background: #2563eb;
}

.hero-attach-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.hero-attach-btn:hover {
  background: #334155;
  color: #fff;
}

/* 模式按钮：未选中仅图标，选中时白底高亮+文字 */
.hero-mode-group {
  display: inline-flex;
  align-items: center;
  padding: 4px 5px 4px 4px;
  background: #e2e8f0;
  border-radius: 9999px;
  gap: 2px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.hero-mode-slider {
  position: absolute;
  top: 4px;
  left: 0;
  height: calc(100% - 8px);
  background: #fff;
  border-radius: 9999px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.hero-mode-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
  min-width: 32px;
}

.hero-mode-btn .hero-mode-label {
  visibility: hidden;
  position: absolute;
  white-space: nowrap;
}

.hero-mode-btn.active .hero-mode-label {
  visibility: visible;
  position: static;
}

.hero-mode-btn svg {
  flex-shrink: 0;
  color: inherit;
}

.hero-mode-btn.active {
  color: #3b82f6;
}

.hero-mode-btn .hero-mode-width-calc {
  visibility: hidden;
  position: absolute;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 500;
}

/* ?????? */
.hero-suggestions {
  text-align: center;
  transform: translateY(24px);
}

.hero-suggest-label {
  font-size: 10px;
  color: #94a3b8;
  margin: 0 0 10px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.hero-pill {
  padding: 8px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 11px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.hero-pill:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #334155;
}

/* ?????? */
.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 24px 12px;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  background: white;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  position: relative;
  z-index: 1;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
}

.user-message .message-avatar {
  background: #3b82f6;
  color: white;
}

.user-message .message-content {
  text-align: right;
}

.ai-message .message-avatar {
  background: #f1f5f9;
}

.message-content {
  flex: 1;
  max-width: max-content;
  width: fit-content;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.7;
  font-size: 15px;
  max-width: 600px;
  word-wrap: break-word;
  word-break: break-word;
}

.user-message .message-bubble {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-bubble {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.message-bubble :deep(code) {
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.message-bubble :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.source-count {
  color: #3b82f6;
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* ???? */
.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: white;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 16px 16px 16px 16px;
  transition: all 0.2s;
  flex-wrap: wrap;
  width: 100%;
  box-sizing: border-box;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

.input-wrapper textarea {
  flex: 1;
  min-width: 200px;
  border: none;
  background: transparent;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  max-height: 200px;
  font-family: inherit;
  padding: 10px 0 8px;
  margin-top: 10px;
}

.input-wrapper textarea:focus {
  outline: none;
}

.input-mode-group {
  display: inline-flex;
  align-items: center;
  padding: 3px 4px 3px 3px;
  background: #e2e8f0;
  border-radius: 9999px;
  gap: 2px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  margin-right: 8px;
}

.input-mode-slider {
  position: absolute;
  top: 3px;
  left: 0;
  height: calc(100% - 6px);
  background: #fff;
  border-radius: 9999px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.input-mode-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 4px 8px;
  border: none;
  background: transparent;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
  white-space: nowrap;
}

.input-mode-btn.active {
  color: #3b82f6;
}

.attach-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.attach-btn:hover {
  background: #e2e8f0;
  color: #3b82f6;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  border-radius: 10px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ??? */
.chat-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

.sidebar-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.sidebar-card p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

/* ?? */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 420px;
  animation: fadeIn 0.2s ease;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 { font-size: 18px; }
.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 24px;
  cursor: pointer;
}

.modal-body { padding: 20px; }
.modal-body p { margin-bottom: 16px; }

.feedback-options {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.feedback-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #e5e7eb;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.feedback-btn.active, .feedback-btn:hover {
  border-color: #3b82f6;
  background: rgba(102,126,234,0.1);
}

.modal-body textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1024px) {
  .chat-content {
    grid-template-columns: 1fr;
  }
  .chat-sidebar {
    display: none;
  }
}

@media (max-width: 768px) {
  .chat-hero h1 {
    font-size: 28px;
  }
  .hero-input {
    flex-direction: column;
    padding: 12px;
  }
  .hero-input input {
    width: 100%;
  }
  .hero-send {
    width: 100%;
  }
}
</style>
