<template>
  <div class="settings-page">
    <div class="settings-card">
      <!-- 左侧导航 -->
      <aside class="settings-sidebar">
        <h2 class="sidebar-title">设置</h2>
        <nav class="sidebar-nav">
          <button
            :class="['nav-item', { active: activeTab === 'account' }]"
            @click="activeTab = 'account'"
          >
            <span class="nav-icon">👤</span>
            账户与安全
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'profile' }]"
            @click="activeTab = 'profile'"
          >
            <span class="nav-icon">👤</span>
            我的资料
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'general' }]"
            @click="activeTab = 'general'"
          >
            <span class="nav-icon">⚙️</span>
            通用设置
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'storage' }]"
            @click="activeTab = 'storage'"
          >
            <span class="nav-icon">📦</span>
            存储管理
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'notifications' }]"
            @click="activeTab = 'notifications'"
          >
            <span class="nav-icon">🔔</span>
            通知管理
          </button>
          <button
            :class="['nav-item', { active: activeTab === 'academic' }]"
            @click="activeTab = 'academic'"
          >
            <span class="nav-icon">🎓</span>
            学术认证
          </button>
        </nav>
      </aside>

      <!-- 右侧内容区 -->
      <main class="settings-main">
        <!-- 账户与安全 -->
        <div v-if="activeTab === 'account'" class="panel-content">
          <section class="content-section">
            <h3 class="section-title">账号</h3>
            <div class="field-row">
              <div class="field-info">
                <span class="field-icon">📄</span>
                <div>
                  <h4>学术码</h4>
                  <p>学术码是你的平台账号 ID，是科研身份的唯一标识</p>
                </div>
              </div>
              <div class="field-value">
                <span>{{ account.academicCode }}</span>
                <button type="button" class="icon-btn" title="复制">📋</button>
              </div>
            </div>
            <div class="field-row">
              <div class="field-info">
                <span class="field-icon">🪪</span>
                <div>
                  <h4>账户ID</h4>
                  <p>用于合同或财务结算时的业务标识</p>
                </div>
              </div>
              <div class="field-value">
                <span>{{ account.accountId }}</span>
                <button type="button" class="icon-btn" title="复制">📋</button>
              </div>
            </div>
          </section>

          <section class="content-section">
            <h3 class="section-title">登录方式</h3>
            <div class="login-method">
              <span class="method-icon">📱</span>
              <div class="method-text">手机号</div>
              <div class="method-value">{{ account.phone || '未设置' }}</div>
              <button type="button" class="btn-outline">修改</button>
            </div>
            <div class="login-method">
              <span class="method-icon">✉️</span>
              <div class="method-text">邮箱</div>
              <div class="method-value">{{ account.email || '未设置' }}</div>
              <button type="button" class="btn-outline">修改</button>
            </div>
            <div class="login-method">
              <span class="method-icon method-wechat">微</span>
              <div class="method-text">微信</div>
              <div class="method-value">{{ account.wechatBound ? '已绑定' : '未绑定' }}</div>
              <button type="button" class="btn-outline">{{ account.wechatBound ? '解绑' : '绑定' }}</button>
            </div>
            <div class="login-method">
              <span class="method-icon method-apple">🍎</span>
              <div class="method-text">Apple</div>
              <div class="method-value">{{ account.appleBound ? '已绑定' : '未绑定' }}</div>
              <button type="button" class="btn-primary">{{ account.appleBound ? '解绑' : '绑定' }}</button>
            </div>
            <div class="login-method">
              <span class="method-icon">🌐</span>
              <div class="method-text">CARSI 专属权益</div>
              <div class="method-value">未绑定</div>
              <button type="button" class="btn-primary">绑定</button>
            </div>
            <div class="login-method">
              <span class="method-icon">🏫</span>
              <div class="method-desc">
                <div class="method-text">学校/科研机构</div>
                <p>登录时选择“机构登录”即可使用机构专属资源及权益</p>
              </div>
              <div class="method-value">未绑定</div>
              <button type="button" class="btn-primary">绑定</button>
            </div>
          </section>
        </div>

        <!-- 我的资料 -->
        <div v-if="activeTab === 'profile'" class="panel-content">
          <h2 class="panel-title">我的资料</h2>
          <div class="form-group">
            <label>头像</label>
            <div class="avatar-upload">
              <div class="avatar-preview">👤</div>
              <button type="button" class="btn-outline">更换头像</button>
            </div>
          </div>
          <div class="form-group">
            <label>用户名</label>
            <input type="text" v-model="profile.username" class="input">
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input type="email" v-model="profile.email" class="input">
          </div>
          <div class="form-group">
            <label>手机号</label>
            <input type="tel" v-model="profile.phone" class="input">
          </div>
          <div class="form-group">
            <label>个人简介</label>
            <textarea v-model="profile.bio" class="input" rows="4"></textarea>
          </div>
          <button type="button" class="btn-primary">保存更改</button>
        </div>

        <!-- 通用设置 -->
        <div v-if="activeTab === 'general'" class="panel-content">
          <h2 class="panel-title">通用设置</h2>
          <div class="form-group">
            <label>主题模式</label>
            <div class="theme-options">
              <button :class="['theme-btn', { active: appearance.theme === 'light' }]" @click="appearance.theme = 'light'">浅色</button>
              <button :class="['theme-btn', { active: appearance.theme === 'dark' }]" @click="appearance.theme = 'dark'">深色</button>
              <button :class="['theme-btn', { active: appearance.theme === 'auto' }]" @click="appearance.theme = 'auto'">跟随系统</button>
            </div>
          </div>
          <div class="form-group">
            <label>语言</label>
            <select v-model="appearance.language" class="input">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
        </div>

        <!-- 存储管理 -->
        <div v-if="activeTab === 'storage'" class="panel-content">
          <h2 class="panel-title">存储管理</h2>
          <p class="text-muted">管理本地缓存与存储空间。</p>
        </div>

        <!-- 通知管理 -->
        <div v-if="activeTab === 'notifications'" class="panel-content">
          <h2 class="panel-title">通知管理</h2>
          <div class="notification-item">
            <div class="notification-info">
              <span class="notification-title">系统更新</span>
              <span class="notification-desc">接收系统版本更新和功能通知</span>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="notifications.systemUpdates">
              <span class="slider"></span>
            </label>
          </div>
          <div class="notification-item">
            <div class="notification-info">
              <span class="notification-title">学习提醒</span>
              <span class="notification-desc">定时提醒学习计划和任务</span>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="notifications.learningReminders">
              <span class="slider"></span>
            </label>
          </div>
          <div class="notification-item">
            <div class="notification-info">
              <span class="notification-title">成绩通知</span>
              <span class="notification-desc">作业和考试成绩及时通知</span>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="notifications.grades">
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- 学术认证 -->
        <div v-if="activeTab === 'academic'" class="panel-content">
          <h2 class="panel-title">学术认证</h2>
          <p class="text-muted">绑定学校或科研机构以使用专属资源。</p>
        </div>
      </main>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const activeTab = ref('account')

const account = reactive({
  academicCode: 'h861i8dl',
  accountId: '1R4Z1C0',
  phone: '(+86) 153 **** 1572',
  email: '',
  wechatBound: true,
  appleBound: false
})

const profile = reactive({
  username: authStore.user?.username || '用户',
  email: '',
  phone: '',
  bio: ''
})

const notifications = reactive({ systemUpdates: true, learningReminders: true, grades: true })
const appearance = reactive({ theme: 'light', language: 'zh-CN' })
</script>

<style scoped>
.settings-page {
  padding: 24px;
  min-height: calc(100vh - 64px);
  background: var(--bg-secondary);
}

/* 左右合为一块，中间竖线分隔 */
.settings-card {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  align-items: stretch;
  min-height: 560px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
}

/* 左侧边栏 */
.settings-sidebar {
  width: 220px;
  flex-shrink: 0;
  padding: 24px 0;
}

.sidebar-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 24px 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-nav .nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-muted);
  transition: var(--transition);
  text-align: left;
  position: relative;
}

.sidebar-nav .nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

/* 当前项：按钮高亮（浅紫背景 + 深紫文字），与图片一致 */
.sidebar-nav .nav-item.active {
  color: #4c51bf;
  background: rgba(102, 126, 234, 0.15);
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

/* 右侧主内容：仅左侧边框作为中间分割线 */
.settings-main {
  flex: 1;
  min-width: 0;
  border-left: 1px solid var(--border);
  overflow: auto;
}

.panel-content {
  padding: 32px 40px;
}

.panel-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 28px 0;
}

.content-section {
  margin-bottom: 36px;
}

.content-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

.field-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-light);
  gap: 16px;
}

.field-row:last-child {
  border-bottom: none;
}

.field-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.field-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.field-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.field-info p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.field-value {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.field-value span {
  font-size: 14px;
  color: var(--text-primary);
}

.icon-btn {
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.7;
}

.icon-btn:hover {
  opacity: 1;
}

/* 登录方式行 */
.login-method {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
}

.login-method:last-child {
  border-bottom: none;
}

.method-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.method-wechat {
  background: #07c160;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.method-apple {
  background: #000;
  color: white;
}

.method-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 120px;
}

.method-desc .method-text {
  min-width: 0;
}

.method-desc p {
  font-size: 12px;
  color: var(--text-muted);
  margin: 4px 0 0 0;
}

.method-value {
  flex: 1;
  font-size: 14px;
  color: var(--text-secondary);
}

.btn-outline {
  padding: 8px 16px;
  font-size: 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-outline:hover {
  background: var(--bg-tertiary);
}

/* 设置页主按钮：与图片一致使用紫色 */
.btn-primary {
  padding: 8px 16px;
  font-size: 14px;
  background: #667eea;
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  cursor: pointer;
}

.btn-primary:hover {
  background: #5a67d8;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.input {
  width: 100%;
  max-width: 400px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.input:focus {
  outline: none;
  border-color: var(--primary);
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-preview {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.theme-options {
  display: flex;
  gap: 12px;
}

.theme-btn {
  padding: 10px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  font-size: 14px;
  cursor: pointer;
}

.theme-btn.active {
  border-color: #667eea;
  color: #5a67d8;
  background: rgba(102, 126, 234, 0.15);
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-light);
}

.notification-info {
  display: flex;
  flex-direction: column;
}

.notification-title { font-size: 14px; font-weight: 500; }
.notification-desc { font-size: 13px; color: var(--text-muted); }

.toggle { position: relative; width: 48px; height: 26px; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background: var(--border);
  border-radius: 26px;
  transition: 0.3s;
}
.slider::before {
  position: absolute;
  content: '';
  height: 20px; width: 20px;
  left: 3px; bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.toggle input:checked + .slider { background: #667eea; }
.toggle input:checked + .slider::before { transform: translateX(22px); }

.text-muted {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

@media (max-width: 768px) {
  .settings-card { flex-direction: column; min-height: auto; }
  .settings-sidebar { width: 100%; }
  .settings-main { border-left: none; border-top: 1px solid var(--border); }
}
</style>
