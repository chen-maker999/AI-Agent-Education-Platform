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

          <!-- Welcome header -->
          <transition name="header-out">
            <div v-if="!hasStarted" class="welcome-header">
              <div class="glow-title-wrap"></div>
            </div>
          </transition>

          <!-- Top spacer -->
          <div class="top-spacer" :class="{ 'top-spacer--gone': hasStarted }"></div>

          <!-- Top toolbar -->
          <div v-if="hasStarted" class="chat-toolbar">
            <!-- 会话轨迹按钮 + 展开面板 -->
            <div class="toolbar-dropdown">
              <button class="pill-btn" :class="{ active: showHistory }" @click="showHistory = !showHistory; if(showHistory) showSources = false">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6.5 3.5v3l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                会话轨迹
                <svg class="pill-chevron" :class="{ open: showHistory }" width="11" height="11" viewBox="0 0 11 11" fill="none">
                  <path d="M2.5 4l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <transition name="dropdown-pop">
                <div v-if="showHistory" class="dropdown-card">
                  <div v-if="conversationHistory.length" class="resource-list">
                    <button v-for="(item, index) in conversationHistory" :key="item.id" type="button"
                      class="chat-history-item" :class="{ active: currentConversationIndex === index }"
                      @click="loadConversation(index)">
                      <strong>{{ item.title }}</strong>
                      <span>{{ item.time }}</span>
                    </button>
                  </div>
                  <InfoState v-else title="还没有历史会话" description="发送一个问题后，这里会保留最近的工作上下文。"/>
                </div>
              </transition>
            </div>

            <!-- 引用与动作按钮 + 展开面板 -->
            <div class="toolbar-dropdown">
              <button class="pill-btn" :class="{ active: showSources }" @click="showSources = !showSources; if(showSources) showHistory = false">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <path d="M2 2.5h9M2 6.5h6M2 10.5h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                引用与动作
                <svg class="pill-chevron" :class="{ open: showSources }" width="11" height="11" viewBox="0 0 11 11" fill="none">
                  <path d="M2.5 4l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
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
            <button class="new-chat-btn" @click="createNewChat" title="新建会话">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Chat stream -->
          <transition name="stream-in">
            <div v-if="hasStarted" class="chat-stream-box" ref="streamRef">
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
                  <p class="chat-content">
                    <span class="chat-text" :class="{ 'text-reveal': streamingIndex === index }">{{ msg.content }}</span>
                    <span v-if="streamingIndex === index" class="typing-cursor"></span>
                  </p>
                </div>
              </div>

              <div v-if="isLoading && streamingIndex === -1" class="chat-loading">
                <div class="chat-loading__dots"><span></span><span></span><span></span></div>
                <p>AI 正在检索知识库并生成回答</p>
              </div>
            </div>
          </transition>

          <!-- Composer -->
          <div class="composer-wrap">
            <div class="composer-glow" aria-hidden="true"></div>
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
                  <button class="tool-btn" title="附件">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 7.5L7.5 13.5a4 4 0 01-5.657-5.657l5.657-5.657a2.5 2.5 0 013.536 3.536L5.379 11.47a1 1 0 01-1.414-1.414L9 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
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
import { computed, nextTick, ref, onMounted } from 'vue'
import { ragApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import InfoState from '@/components/ui/InfoState.vue'

const authStore = useAuthStore()

// 页面加载时初始化 thumb 位置
onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      const activeIndex = modeOptions.findIndex(m => m.value === selectedMode.value)
      if (activeIndex >= 0) updateThumb(activeIndex)
    }, 100)
  })
})
const userInitial = computed(() => (authStore.user?.username || 'U').charAt(0).toUpperCase())

const modeOptions = [
  { label: '通用问答', value: 'general' },
  { label: '知识库对话', value: 'knowledge' },
  { label: '智能体', value: 'agent' }
]

const selectedMode = ref('general')
const inputMessage = ref('')
const isLoading = ref(false)
const hasStarted = ref(false)
const showHistory = ref(false)
const showSources = ref(false)
const currentConversationIndex = ref(-1)
const messages = ref([])
const conversationHistory = ref([])
const inputRef = ref(null)
const streamRef = ref(null)
const modeRefs = ref([])
const modeThumbX = ref(0)
const modeThumbW = ref(0)
const lastQuestion = ref('')
const showPreviewCard = ref(false)
const streamingIndex = ref(-1) // 正在流式输出的消息索引

function selectMode(value, index) {
  selectedMode.value = value
  nextTick(() => updateThumb(index))
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
}

function createNewChat() {
  // 保存当前会话到历史（如果当前有内容）
  if (currentConversationIndex.value > -1 && messages.value.length > 0) {
    conversationHistory.value[currentConversationIndex.value].messages = [...messages.value]
  }
  // 重置状态
  messages.value = []
  conversationHistory.value = []
  currentConversationIndex.value = -1
  hasStarted.value = false
  showHistory.value = false
  showSources.value = false
  streamingIndex.value = -1
  activeSources.value = [
    { title: '引用来源将在这里显示', summary: '命中文档、知识块和建议动作会伴随回答一起出现。' }
  ]
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
    const response = await ragApi.chatStream({
      query: text,
      student_id: authStore.user?.id || 'guest',
      session_id: `chat_${selectedMode.value}`,
      mode: selectedMode.value === 'general' ? 'general' : 'learning'
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
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  margin-bottom: 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(18px) saturate(1.4);
  -webkit-backdrop-filter: blur(18px) saturate(1.4);
  overflow-y: auto;
  padding: 20px;
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
  display: grid;
  gap: 3px;
  text-align: left;
  padding: 9px 11px;
  border-radius: 9px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.02);
  color: var(--text-secondary);
  transition: all var(--t-fast) ease;
  cursor: pointer;
}
.chat-history-item strong { color: var(--text-primary); font-size: 12px; }
.chat-history-item span   { color: var(--text-muted); font-size: 11px; }
.chat-history-item:hover  { background: rgba(255,255,255,0.04); border-color: var(--glass-border-hi); }
.chat-history-item.active {
  border-color: rgba(48,112,255,0.22);
  background: rgba(48,112,255,0.06);
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
</style>
