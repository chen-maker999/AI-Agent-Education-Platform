<template>
  <div class="macos-settings">
    <!-- 顶部标题栏 -->
    <header class="macos-header">
      <div class="header-title">
        <span class="header-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </span>
        <h1>系统偏好设置</h1>
      </div>
      <div class="header-search">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        <input type="text" placeholder="搜索" v-model="searchQuery" />
      </div>
    </header>

    <div class="macos-content">
      <!-- 左侧边栏 -->
      <nav class="macos-sidebar">
        <div class="sidebar-section">
          <div
            v-for="item in sidebarItems"
            :key="item.id"
            class="sidebar-item"
            :class="{ active: activeSection === item.id }"
            @click="activeSection = item.id"
          >
            <div class="sidebar-icon" v-html="item.icon"></div>
            <span class="sidebar-label">{{ item.label }}</span>
          </div>
        </div>
      </nav>

      <!-- 主内容区 -->
      <main class="macos-main">
        <!-- 3D背景 -->
        <div class="spline-container">
          <iframe
            src="https://my.spline.design/distortedglasscircleslightmode-HoOpDYouE5JLYNeY7hoPKOiq/"
            frameborder="0"
            width="100%"
            height="100%"
            id="aura-spline"
          ></iframe>
        </div>

        <!-- 账号设置 -->
        <section v-if="activeSection === 'account'" class="settings-section">
          <div class="section-header">
            <h2>{{ currentSectionData.title }}</h2>
            <p>{{ currentSectionData.subtitle }}</p>
          </div>

          <div class="macos-panel">
            <div class="panel-group">
              <h3>个人资料</h3>
              <div class="form-row">
                <div class="form-field">
                  <label>用户名</label>
                  <div class="macos-input">
                    <input type="text" v-model="profile.username" placeholder="输入用户名" />
                  </div>
                </div>
                <div class="form-field">
                  <label>角色</label>
                  <div class="macos-input disabled">
                    <input type="text" :value="profile.role" disabled />
                    <span class="input-lock">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                      </svg>
                    </span>
                  </div>
                </div>
              </div>
              <div class="form-row">
                <div class="form-field">
                  <label>邮箱</label>
                  <div class="macos-input">
                    <input type="email" v-model="profile.email" placeholder="输入邮箱地址" />
                  </div>
                </div>
                <div class="form-field">
                  <label>手机号</label>
                  <div class="macos-input">
                    <input type="tel" v-model="profile.phone" placeholder="输入手机号码" />
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>账号安全</h3>
              <div class="setting-row clickable" @click="showPasswordModal = true">
                <div class="setting-info">
                  <span class="setting-label">修改密码</span>
                  <span class="setting-desc">上次修改于 30 天前</span>
                </div>
                <div class="setting-arrow">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </div>
              </div>
              <div class="setting-row clickable">
                <div class="setting-info">
                  <span class="setting-label">双重认证</span>
                  <span class="setting-desc">为您的账号添加额外的安全保护</span>
                </div>
                <div class="setting-arrow">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </div>
              </div>
            </div>

            <div class="panel-actions">
              <button class="macos-btn primary" @click="saveAccount" :disabled="profileLoading">
                {{ profileLoading ? '保存中...' : '存储更改' }}
              </button>
              <button class="macos-btn secondary" @click="resetAccount">恢复默认</button>
            </div>
            <div v-if="profileSuccess" class="success-msg" style="margin: 0 20px 14px; font-size: 12px; color: #34c759; padding: 6px 12px; background: rgba(52,199,89,0.1); border-radius: 6px;">✓ 资料更新成功</div>
            <div v-if="profileError" class="error-msg" style="margin: 0 20px 14px; font-size: 12px; color: #ff3b30; padding: 6px 12px; background: rgba(255,59,48,0.1); border-radius: 6px;">{{ profileError }}</div>
          </div>
        </section>

        <!-- 通知设置 -->
        <section v-if="activeSection === 'notification'" class="settings-section">
          <div class="section-header">
            <h2>{{ currentSectionData.title }}</h2>
            <p>{{ currentSectionData.subtitle }}</p>
          </div>

          <div class="macos-panel">
            <div class="panel-group">
              <h3>通知类型</h3>
              <div v-for="item in notifications" :key="item.id" class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">{{ item.title }}</span>
                  <span class="setting-desc">{{ item.description }}</span>
                </div>
                <div class="macos-toggle" :class="{ active: item.enabled }" @click="item.enabled = !item.enabled">
                  <div class="toggle-knob"></div>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>静默模式</h3>
              <div class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">勿扰模式</span>
                  <span class="setting-desc">在指定时间段内静音所有通知</span>
                </div>
                <div class="macos-toggle" :class="{ active: dndEnabled }" @click="dndEnabled = !dndEnabled">
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <div v-if="dndEnabled" class="time-range">
                <div class="time-input">
                  <label>开始时间</label>
                  <input type="time" v-model="dndStart" />
                </div>
                <div class="time-input">
                  <label>结束时间</label>
                  <input type="time" v-model="dndEnd" />
                </div>
              </div>
            </div>

            <div class="panel-actions">
              <button class="macos-btn primary" @click="saveNotifications">存储更改</button>
            </div>
          </div>
        </section>

        <!-- 主题设置 -->
        <section v-if="activeSection === 'appearance'" class="settings-section">
          <div class="section-header">
            <h2>{{ currentSectionData.title }}</h2>
            <p>{{ currentSectionData.subtitle }}</p>
          </div>

          <div class="macos-panel">
            <div class="panel-group">
              <h3>外观</h3>
              <div class="theme-options">
                <div
                  v-for="theme in themes"
                  :key="theme.id"
                  class="theme-option"
                  :class="{ active: selectedTheme === theme.id }"
                  @click="selectedTheme = theme.id"
                >
                  <div class="theme-preview" :style="{ background: theme.gradient }">
                    <div class="theme-indicator" v-if="selectedTheme === theme.id">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    </div>
                  </div>
                  <span class="theme-label">{{ theme.name }}</span>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>强调色</h3>
              <div class="color-options">
                <div
                  v-for="color in accentColors"
                  :key="color.id"
                  class="color-option"
                  :class="{ active: selectedAccent === color.id }"
                  :style="{ background: color.value }"
                  @click="selectedAccent = color.id"
                >
                  <svg v-if="selectedAccent === color.id" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>高级选项</h3>
              <div class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">透明效果</span>
                  <span class="setting-desc">允许窗口和控件使用透明效果</span>
                </div>
                <div class="macos-toggle" :class="{ active: transparencyEnabled }" @click="transparencyEnabled = !transparencyEnabled">
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <div class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">放大显示</span>
                  <span class="setting-desc">以更大的分辨率显示界面元素</span>
                </div>
                <div class="macos-toggle" :class="{ active: reduceMotion }" @click="reduceMotion = !reduceMotion">
                  <div class="toggle-knob"></div>
                </div>
              </div>
            </div>

            <div class="panel-actions">
              <button class="macos-btn primary" @click="saveAppearance">存储更改</button>
            </div>
          </div>
        </section>

        <!-- 偏好设置 -->
        <section v-if="activeSection === 'preference'" class="settings-section">
          <div class="section-header">
            <h2>{{ currentSectionData.title }}</h2>
            <p>{{ currentSectionData.subtitle }}</p>
          </div>

          <div class="macos-panel">
            <div class="panel-group">
              <h3>启动与工作台</h3>
              <div class="setting-row clickable">
                <div class="setting-info">
                  <span class="setting-label">默认工作台</span>
                  <span class="setting-desc">登录后自动进入与角色匹配的工作台首页</span>
                </div>
                <div class="setting-value">智能工作台</div>
              </div>
              <div class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">搜索优先入口</span>
                  <span class="setting-desc">保留顶部全局搜索</span>
                </div>
                <div class="macos-toggle" :class="{ active: searchFirst }" @click="searchFirst = !searchFirst">
                  <div class="toggle-knob"></div>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>移动端</h3>
              <div class="setting-row">
                <div class="setting-info">
                  <span class="setting-label">移动端导航</span>
                  <span class="setting-desc">在手机端折叠上下文面板</span>
                </div>
                <div class="macos-toggle" :class="{ active: mobileNav }" @click="mobileNav = !mobileNav">
                  <div class="toggle-knob"></div>
                </div>
              </div>
            </div>

            <div class="panel-divider"></div>

            <div class="panel-group">
              <h3>语言与地区</h3>
              <div class="setting-row clickable">
                <div class="setting-info">
                  <span class="setting-label">语言</span>
                </div>
                <div class="setting-value with-arrow">简体中文</div>
              </div>
              <div class="setting-row clickable">
                <div class="setting-info">
                  <span class="setting-label">地区</span>
                </div>
                <div class="setting-value with-arrow">中国</div>
              </div>
            </div>

            <div class="panel-actions">
              <button class="macos-btn primary" @click="savePreferences">存储更改</button>
              <button class="macos-btn secondary" @click="resetPreferences">恢复默认</button>
            </div>
          </div>
        </section>
      </main>
    </div>

    <!-- 修改密码弹窗 -->
    <div class="modal-overlay" v-if="showPasswordModal" @click.self="showPasswordModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>修改密码</h3>
          <button class="modal-close" @click="showPasswordModal = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="modal-field">
            <label>当前密码</label>
            <input type="password" v-model="passwordForm.oldPassword" placeholder="请输入当前密码" />
          </div>
          <div class="modal-field">
            <label>新密码</label>
            <input type="password" v-model="passwordForm.newPassword" placeholder="至少 8 位" />
          </div>
          <div class="modal-field">
            <label>确认新密码</label>
            <input type="password" v-model="passwordForm.confirmPassword" placeholder="再次输入新密码" />
          </div>
          <p class="modal-error" v-if="passwordError">{{ passwordError }}</p>
        </div>
        <div class="modal-footer">
          <button class="macos-btn secondary" @click="showPasswordModal = false">取消</button>
          <button class="macos-btn primary" :disabled="passwordLoading" @click="handleChangePassword">
            {{ passwordLoading ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/index'

const authStore = useAuthStore()

// 搜索
const searchQuery = ref('')

// 侧边栏
const activeSection = ref('account')

const sidebarItems = [
  {
    id: 'account',
    label: '账号',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>`
  },
  {
    id: 'notification',
    label: '通知',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>`
  },
  {
    id: 'appearance',
    label: '主题',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/>
      <line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>`
  },
  {
    id: 'preference',
    label: '偏好',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <line x1="4" y1="21" x2="4" y2="14"/>
      <line x1="4" y1="10" x2="4" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12" y2="3"/>
      <line x1="20" y1="21" x2="20" y2="16"/>
      <line x1="20" y1="12" x2="20" y2="3"/>
      <line x1="1" y1="14" x2="7" y2="14"/>
      <line x1="9" y1="8" x2="15" y2="8"/>
      <line x1="17" y1="16" x2="23" y2="16"/>
    </svg>`
  }
]

// 内容区数据
const sectionData = {
  account: {
    title: '账号与基础资料',
    subtitle: '当前设置围绕账号、角色和联系方式，避免混入业务内容。'
  },
  notification: {
    title: '通知管理',
    subtitle: '根据角色控制作业、预警和索引通知。'
  },
  appearance: {
    title: '主题与外观',
    subtitle: '统一维持 Search-native Workspace 的视觉系统。'
  },
  preference: {
    title: '平台偏好',
    subtitle: '定义默认入口和设备端交互行为。'
  }
}

const currentSectionData = computed(() => sectionData[activeSection.value])

// 账号表单
const profile = ref({
  username: authStore.user?.username || 'student_01',
  role: authStore.user?.role || '学生',
  email: authStore.user?.email || 'student@example.com',
  phone: authStore.user?.phone || ''
})
const profileLoading = ref(false)
const profileSuccess = ref(false)
const profileError = ref('')

onMounted(async () => {
  try {
    const res = await authApi.me()
    if (res.code === 200 && res.data) {
      authStore.setUser(res.data)
      profile.value = {
        username: res.data.username || profile.value.username,
        role: res.data.role || profile.value.role,
        email: res.data.email || profile.value.email,
        phone: res.data.phone || ''
      }
    }
  } catch (e) {
    // ignore
  }
})

// 通知设置
const notifications = ref([
  { id: 1, title: '作业状态提醒', description: '作业提交、批改完成、批注回看等消息通知。', enabled: true },
  { id: 2, title: '预警干预提醒', description: '教师端接收高风险预警与待干预学生通知。', enabled: authStore.user?.role !== 'student' },
  { id: 3, title: '知识库索引通知', description: '文档分块、向量化和索引完成状态通知。', enabled: true },
  { id: 4, title: '系统更新提醒', description: '平台版本、嵌入能力和 Agent Studio 状态更新。', enabled: false }
])

const dndEnabled = ref(false)
const dndStart = ref('22:00')
const dndEnd = ref('07:00')

// 主题设置
const themes = [
  { id: 'blue', name: '沉浸蓝', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'system', name: '跟随系统', gradient: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' },
  { id: 'dark', name: '深色模式', gradient: 'linear-gradient(135deg, #2c3e50 0%, #1a1a2e 100%)' },
  { id: 'sunset', name: '日落橙', gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }
]

const selectedTheme = ref('blue')

const accentColors = [
  { id: 'blue', value: '#007AFF' },
  { id: 'purple', value: '#AF52DE' },
  { id: 'pink', value: '#FF2D55' },
  { id: 'red', value: '#FF3B30' },
  { id: 'orange', value: '#FF9500' },
  { id: 'yellow', value: '#FFCC00' },
  { id: 'green', value: '#34C759' },
  { id: 'teal', value: '#5AC8FA' }
]

const selectedAccent = ref('blue')
const transparencyEnabled = ref(true)
const reduceMotion = ref(false)

// 偏好设置
const searchFirst = ref(true)
const mobileNav = ref(true)

// 修改密码弹窗
const showPasswordModal = ref(false)
const passwordForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const passwordLoading = ref(false)
const passwordError = ref('')

async function saveAccount() {
  profileError.value = ''
  profileSuccess.value = false
  if (!profile.value.username || profile.value.username.length < 3) {
    profileError.value = '用户名至少 3 个字符'
    return
  }
  if (!profile.value.email) {
    profileError.value = '邮箱不能为空'
    return
  }
  profileLoading.value = true
  try {
    const res = await authApi.updateProfile({
      username: profile.value.username,
      email: profile.value.email,
      phone: profile.value.phone
    })
    if (res.code === 200) {
      profileSuccess.value = true
      authStore.setUser(res.data)
      setTimeout(() => { profileSuccess.value = false }, 3000)
    } else {
      profileError.value = res.message || '保存失败'
    }
  } catch (e) {
    profileError.value = e?.response?.data?.detail || '保存失败，请重试'
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  passwordError.value = ''
  if (!passwordForm.value.oldPassword) {
    passwordError.value = '请输入当前密码'
    return
  }
  if (passwordForm.value.newPassword.length < 8) {
    passwordError.value = '新密码至少 8 位'
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  passwordLoading.value = true
  try {
    const res = await authApi.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    if (res.code === 200) {
      showPasswordModal.value = false
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
      // 提示重新登录
      window.dispatchEvent(new CustomEvent('force-logout', { detail: { message: res.message } }))
    } else {
      passwordError.value = res.message || '修改失败'
    }
  } catch (e) {
    passwordError.value = e?.response?.data?.detail || '原密码错误'
  } finally {
    passwordLoading.value = false
  }
}

function resetAccount() {
  profile.value = {
    username: authStore.user?.username || 'student_01',
    role: authStore.user?.role || '学生',
    email: authStore.user?.email || 'student@example.com',
    phone: authStore.user?.phone || ''
  }
  profileError.value = ''
  profileSuccess.value = false
}

function saveNotifications() {
  console.log('保存通知设置:', notifications.value)
}

function saveAppearance() {
  console.log('保存外观设置:', { theme: selectedTheme.value, accent: selectedAccent.value })
}

function savePreferences() {
  console.log('保存偏好设置')
}

function resetPreferences() {
  searchFirst.value = true
  mobileNav.value = true
}
</script>

<style scoped>
/* 基础变量 */
.macos-settings {
  --macos-bg: #f5f5f7;
  --macos-sidebar-bg: rgba(246, 246, 246, 0.95);
  --macos-panel-bg: rgba(255, 255, 255, 0.95);
  --macos-border: rgba(0, 0, 0, 0.1);
  --macos-text: #1d1d1f;
  --macos-text-secondary: #86868b;
  --macos-accent: #007aff;
  --macos-success: #34c759;
  --macos-radius: 10px;
  --macos-radius-lg: 14px;
  --macos-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  --macos-blur: 20px;

  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--macos-bg);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', sans-serif;
  color: var(--macos-text);
  overflow: hidden;
}

/* 3D背景场景 - 放在主内容区 */
.spline-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  border-radius: inherit;
}

.spline-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: auto;
}

/* 顶部标题栏 */
.macos-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 52px;
  background: var(--macos-sidebar-bg);
  border-bottom: 1px solid var(--macos-border);
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--macos-accent), #5856d6);
  border-radius: 8px;
  color: white;
}

.header-title h1 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.header-search {
  position: relative;
  width: 200px;
}

.header-search .search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--macos-text-secondary);
}

.header-search input {
  width: 100%;
  height: 28px;
  padding: 0 12px 0 32px;
  background: rgba(0, 0, 0, 0.04);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: all 0.2s ease;
}

.header-search input:focus {
  background: rgba(0, 0, 0, 0.06);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

/* 内容区 */
.macos-content {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 侧边栏 */
.macos-sidebar {
  position: relative;
  z-index: 10;
  width: 200px;
  flex-shrink: 0;
  padding: 12px 8px;
  background: var(--macos-sidebar-bg);
  border-right: 1px solid var(--macos-border);
  overflow-y: auto;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--macos-text-secondary);
}

.sidebar-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--macos-text);
}

.sidebar-item.active {
  background: var(--macos-accent);
  color: white;
}

.sidebar-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.sidebar-label {
  font-size: 13px;
  font-weight: 500;
}

/* 主内容区 */
.macos-main {
  position: relative;
  z-index: 10;
  flex: 1;
  min-width: 0;
  padding: 24px 32px;
  overflow-y: auto;
}

.settings-section {
  position: relative;
  z-index: 5;
  max-width: 680px;
  margin: 0 auto;
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-header {
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 6px;
}

.section-header p {
  font-size: 13px;
  color: var(--macos-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* MacOS 面板 */
.macos-panel {
  position: relative;
  z-index: 5;
  background: var(--macos-panel-bg);
  border: 1px solid var(--macos-border);
  border-radius: var(--macos-radius-lg);
  box-shadow: var(--macos-shadow);
  overflow: hidden;
}

.panel-group {
  padding: 16px 20px;
}

.panel-group h3 {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--macos-text-secondary);
  margin: 0 0 12px;
}

.panel-divider {
  height: 1px;
  background: var(--macos-border);
  margin: 0;
}

/* 表单样式 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 12px;
  font-weight: 500;
  color: var(--macos-text-secondary);
}

.macos-input {
  position: relative;
  display: flex;
  align-items: center;
}

.macos-input input {
  width: 100%;
  height: 34px;
  padding: 0 12px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid var(--macos-border);
  border-radius: 6px;
  font-size: 14px;
  color: var(--macos-text);
  outline: none;
  transition: all 0.15s ease;
}

.macos-input input:hover {
  border-color: rgba(0, 0, 0, 0.2);
}

.macos-input input:focus {
  background: white;
  border-color: var(--macos-accent);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.macos-input.disabled input {
  color: var(--macos-text-secondary);
  cursor: not-allowed;
}

.macos-input.disabled input:disabled {
  background: rgba(0, 0, 0, 0.02);
}

.input-lock {
  position: absolute;
  right: 10px;
  color: var(--macos-text-secondary);
}

/* 设置行 */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.setting-row:last-child {
  border-bottom: none;
}

.setting-row.clickable {
  padding: 12px 0;
  cursor: pointer;
  transition: background 0.15s ease;
}

.setting-row.clickable:hover {
  background: rgba(0, 0, 0, 0.02);
  margin: 0 -20px;
  padding: 12px 20px;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--macos-text);
}

.setting-desc {
  font-size: 12px;
  color: var(--macos-text-secondary);
}

.setting-value {
  font-size: 14px;
  color: var(--macos-text-secondary);
}

.setting-value.with-arrow {
  display: flex;
  align-items: center;
  gap: 4px;
}

.setting-value.with-arrow::after {
  content: '';
  width: 6px;
  height: 6px;
  border-right: 2px solid var(--macos-text-secondary);
  border-bottom: 2px solid var(--macos-text-secondary);
  transform: rotate(-45deg);
  opacity: 0.5;
}

.setting-arrow {
  color: var(--macos-text-secondary);
  opacity: 0.5;
}

/* MacOS Toggle 开关 */
.macos-toggle {
  position: relative;
  width: 44px;
  height: 26px;
  background: #e9e9eb;
  border-radius: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.macos-toggle.active {
  background: var(--macos-success);
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.25s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.macos-toggle.active .toggle-knob {
  transform: translateX(18px);
}

/* 时间范围 */
.time-range {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.time-input {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.time-input label {
  font-size: 12px;
  color: var(--macos-text-secondary);
}

.time-input input {
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--macos-border);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: white;
}

.time-input input:focus {
  border-color: var(--macos-accent);
}

/* 主题选项 */
.theme-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.theme-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 10px;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-option:hover .theme-preview {
  transform: scale(1.05);
}

.theme-option.active .theme-preview {
  border-color: var(--macos-accent);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
}

.theme-indicator {
  width: 28px;
  height: 28px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.theme-label {
  font-size: 12px;
  color: var(--macos-text-secondary);
}

/* 强调色选项 */
.color-options {
  display: flex;
  gap: 12px;
}

.color-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
}

.color-option:hover {
  transform: scale(1.15);
}

.color-option.active {
  border-color: white;
  box-shadow: 0 0 0 2px currentColor, 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 按钮 */
.panel-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--macos-border);
  background: rgba(0, 0, 0, 0.01);
}

.macos-btn {
  height: 34px;
  padding: 0 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
  outline: none;
}

.macos-btn.primary {
  background: var(--macos-accent);
  color: white;
}

.macos-btn.primary:hover {
  background: #0071e3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.macos-btn.primary:active {
  transform: translateY(0);
}

.macos-btn.secondary {
  background: rgba(0, 0, 0, 0.05);
  color: var(--macos-text);
  border: 1px solid var(--macos-border);
}

.macos-btn.secondary:hover {
  background: rgba(0, 0, 0, 0.08);
}

/* 响应式 */
@media (max-width: 900px) {
  .macos-sidebar {
    width: 160px;
  }

  .macos-main {
    padding: 20px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .theme-options {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .macos-content {
    flex-direction: column;
  }

  .macos-sidebar {
    width: 100%;
    flex-direction: row;
    padding: 8px;
    border-right: none;
    border-bottom: 1px solid var(--macos-border);
    overflow-x: auto;
  }

  .sidebar-section {
    flex-direction: row;
    gap: 4px;
  }

  .sidebar-item {
    flex-direction: column;
    padding: 8px 16px;
    gap: 4px;
  }

  .sidebar-label {
    font-size: 11px;
  }

  .header-search {
    width: 140px;
  }
}

/* 滚动条样式 */
.macos-sidebar::-webkit-scrollbar,
.macos-main::-webkit-scrollbar {
  width: 6px;
}

.macos-sidebar::-webkit-scrollbar-track,
.macos-main::-webkit-scrollbar-track {
  background: transparent;
}

.macos-sidebar::-webkit-scrollbar-thumb,
.macos-main::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

.macos-sidebar::-webkit-scrollbar-thumb:hover,
.macos-main::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

/* 成功/错误提示 */
.macos-panel {
  position: relative;
}

.macos-panel .success-msg,
.macos-panel .error-msg {
  font-size: 12px;
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 6px;
}

.macos-panel .success-msg {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.macos-panel .error-msg {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: #fff;
  border-radius: 14px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #86868b;
  transition: background 0.15s;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #1d1d1f;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.modal-field label {
  font-size: 12px;
  font-weight: 500;
  color: #86868b;
}

.modal-field input {
  height: 36px;
  padding: 0 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  font-size: 14px;
  color: #1d1d1f;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.modal-field input:focus {
  border-color: #007aff;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.modal-error {
  font-size: 12px;
  color: #ff3b30;
  margin: 0;
  padding: 6px 10px;
  background: rgba(255, 59, 48, 0.08);
  border-radius: 6px;
}

.modal-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 14px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.01);
}

.modal-footer .macos-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
