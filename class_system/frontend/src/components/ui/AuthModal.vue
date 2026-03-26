<template>
  <Teleport to="body">
    <Transition name="auth-modal">
      <div v-if="authStore.showAuthModal" class="auth-modal-overlay" @click.self="closeModal">
        <div class="auth-modal-window">
          <!-- MacOS 风格标题栏 -->
          <div class="macos-titlebar">
            <div class="macos-dots">
              <span class="dot dot--close" @click="closeModal"></span>
              <span class="dot dot--minimize"></span>
              <span class="dot dot--maximize"></span>
            </div>
            <span class="macos-title">{{ authStore.authModalMode === 'login' ? '登录 EduNavigator' : '创建账号' }}</span>
            <div class="macos-titlebar-spacer"></div>
          </div>

          <div class="macos-content">
            <!-- 登录表单 -->
            <template v-if="authStore.authModalMode === 'login'">
              <div class="auth-panel__header">
                <div class="auth-panel__eyebrow">Sign In</div>
                <h2 class="auth-panel__title">欢迎回来</h2>
                <p class="auth-panel__sub">使用平台账号登录工作区</p>
              </div>
              <form class="auth-form" @submit.prevent="handleLogin">
                <div class="form-group">
                  <label class="input-label">用户名 / 邮箱</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <path d="M10 10a4 4 0 100-8 4 4 0 000 8zM2 18a8 8 0 0116 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input class="input-field input-field--icon" v-model="loginForm.username" type="text"
                      placeholder="请输入用户名或邮箱" required autocomplete="username"/>
                  </div>
                </div>
                <div class="form-group">
                  <label class="input-label">密码</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <rect x="3" y="9" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M7 9V6a3 3 0 016 0v3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input class="input-field input-field--icon" v-model="loginForm.password"
                      :type="showPwd ? 'text' : 'password'" placeholder="请输入密码" required autocomplete="current-password"/>
                    <button type="button" class="input-action" @click="showPwd = !showPwd" tabindex="-1">
                      <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
                        <path v-if="!showPwd" d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z" stroke="currentColor" stroke-width="1.5"/>
                        <circle v-if="!showPwd" cx="10" cy="10" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                        <path v-if="showPwd" d="M3 3l14 14M8.5 8.6A2.5 2.5 0 0011.4 11.5M6 5.3C3.8 6.8 2 10 2 10s3 6 8 6c1.5 0 2.9-.4 4.1-1.1M10 4c5 0 8 6 8 6a12.4 12.4 0 01-1.9 2.7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="auth-form__opts">
                  <label class="auth-check">
                    <input type="checkbox" v-model="loginForm.remember"/>
                    <span class="auth-check__box"></span>
                    <span>记住我</span>
                  </label>
                </div>
                <button type="submit" class="btn btn-primary auth-submit" :disabled="loginLoading">
                  <svg v-if="loginLoading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="10"/>
                  </svg>
                  {{ loginLoading ? '登录中...' : '登录工作区' }}
                </button>
                <div v-if="loginError" class="auth-error">
                  <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
                    <circle cx="10" cy="10" r="9" stroke="#ff6098" stroke-width="1.5"/>
                    <path d="M10 6v4M10 13v1" stroke="#ff6098" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  {{ loginError }}
                </div>
                <div class="auth-switch">
                  <span>还没有账号？</span>
                  <button type="button" class="auth-switch__link" @click="authStore.authModalMode = 'register'">立即注册</button>
                </div>
              </form>
            </template>

            <!-- 注册表单 -->
            <template v-else>
              <div class="auth-panel__header">
                <div class="auth-panel__eyebrow">Sign Up</div>
                <h2 class="auth-panel__title">创建账号</h2>
                <p class="auth-panel__sub">填写信息，立即开始使用</p>
              </div>
              <form class="auth-form" @submit.prevent="handleRegister">
                <div class="form-group">
                  <label class="input-label">用户名</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <path d="M10 10a4 4 0 100-8 4 4 0 000 8zM2 18a8 8 0 0116 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input class="input-field input-field--icon" v-model="regForm.username" type="text"
                      placeholder="请输入用户名" required autocomplete="username"/>
                  </div>
                </div>
                <div class="form-group">
                  <label class="input-label">邮箱</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <rect x="2" y="4" width="16" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M2 7l8 5 8-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input class="input-field input-field--icon" v-model="regForm.email" type="email"
                      placeholder="请输入邮箱" required autocomplete="email"/>
                  </div>
                </div>
                <div class="form-group">
                  <label class="input-label">密码</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <rect x="3" y="9" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M7 9V6a3 3 0 016 0v3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input class="input-field input-field--icon" v-model="regForm.password"
                      :type="showRegPwd ? 'text' : 'password'" placeholder="请输入密码" required autocomplete="new-password"/>
                    <button type="button" class="input-action" @click="showRegPwd = !showRegPwd" tabindex="-1">
                      <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
                        <path v-if="!showRegPwd" d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z" stroke="currentColor" stroke-width="1.5"/>
                        <circle v-if="!showRegPwd" cx="10" cy="10" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                        <path v-if="showRegPwd" d="M3 3l14 14M8.5 8.6A2.5 2.5 0 0011.4 11.5M6 5.3C3.8 6.8 2 10 2 10s3 6 8 6c1.5 0 2.9-.4 4.1-1.1M10 4c5 0 8 6 8 6a12.4 12.4 0 01-1.9 2.7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="form-group">
                  <label class="input-label">角色</label>
                  <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="7" r="3" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M4 17c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <select class="input-field input-field--icon" v-model="regForm.role">
                      <option value="student">学生</option>
                      <option value="teacher">教师</option>
                      <option value="admin">管理员</option>
                    </select>
                  </div>
                </div>
                <button type="submit" class="btn btn-primary auth-submit" :disabled="regLoading">
                  <svg v-if="regLoading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="10"/>
                  </svg>
                  {{ regLoading ? '注册中...' : '创建账号' }}
                </button>
                <div v-if="regError" class="auth-error">
                  <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
                    <circle cx="10" cy="10" r="9" stroke="#ff6098" stroke-width="1.5"/>
                    <path d="M10 6v4M10 13v1" stroke="#ff6098" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  {{ regError }}
                </div>
                <div v-if="regSuccess" class="auth-success">{{ regSuccess }}</div>
                <div class="auth-switch">
                  <span>已有账号？</span>
                  <button type="button" class="auth-switch__link" @click="authStore.authModalMode = 'login'">去登录</button>
                </div>
              </form>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = reactive({ username: '', password: '', remember: false })
const loginLoading = ref(false)
const loginError = ref('')
const showPwd = ref(false)

const regForm = reactive({ username: '', email: '', password: '', role: 'student' })
const regLoading = ref(false)
const regError = ref('')
const regSuccess = ref('')
const showRegPwd = ref(false)

function closeModal() {
  authStore.closeAuthModal()
  loginError.value = ''
  regError.value = ''
  regSuccess.value = ''
}

async function handleLogin() {
  loginError.value = ''
  loginLoading.value = true
  const result = await authStore.login({ username: loginForm.username, password: loginForm.password })
  loginLoading.value = false
  if (result?.success) {
    closeModal()
    router.push('/dashboard')
  } else {
    loginError.value = result?.message || '用户名或密码不正确'
  }
}

async function handleRegister() {
  regLoading.value = true
  regError.value = ''
  regSuccess.value = ''
  const result = await authStore.register({
    username: regForm.username,
    email: regForm.email,
    password: regForm.password,
    role: regForm.role
  })
  regLoading.value = false
  if (result?.code === 200 || result?.success) {
    regSuccess.value = '账号创建成功，正在跳转登录...'
    setTimeout(() => {
      authStore.authModalMode = 'login'
      regSuccess.value = ''
    }, 1200)
  } else {
    regError.value = result?.message || '注册失败，请稍后重试。'
  }
}
</script>

<style scoped>
.auth-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.auth-modal-window {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 12px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  overflow: hidden;
  animation: modalPopIn 0.3s ease-out;
}

@keyframes modalPopIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.macos-titlebar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(248, 248, 248, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.macos-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: opacity 0.15s;
}

.dot:hover { opacity: 0.8; }
.dot--close { background: #ff5f57; }
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
  padding: 24px 28px;
}

.auth-panel__header { margin-bottom: 20px; }
.auth-panel__eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--brand-500); margin-bottom: 6px;
}
.auth-panel__title { font-size: 22px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px; }
.auth-panel__sub { font-size: 13px; color: var(--text-muted); }

.auth-form { display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.input-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.input-wrap { position: relative; display: flex; align-items: center; }
.input-icon { position: absolute; left: 14px; width: 18px; height: 18px; color: var(--text-muted); pointer-events: none; }
.input-field {
  width: 100%; padding: 11px 16px;
  border: 1px solid rgba(0,0,0,0.10); border-radius: 8px;
  background: #f8fafc; font-size: 14px; color: var(--text-primary);
  transition: border-color 150ms ease, box-shadow 150ms ease; outline: none;
}
.input-field::placeholder { color: var(--text-muted); }
.input-field:focus { border-color: var(--brand-400); box-shadow: 0 0 0 3px rgba(37,99,235,0.10); background: #fff; }
.input-field--icon { padding-left: 42px; }
select.input-field { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; }
.input-action { position: absolute; right: 12px; background: none; border: none; cursor: pointer; color: var(--text-muted); padding: 4px; transition: color 150ms ease; }
.input-action:hover { color: var(--text-secondary); }

.auth-form__opts { display: flex; align-items: center; justify-content: space-between; }
.auth-check { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); cursor: pointer; }
.auth-check input[type=checkbox] { display: none; }
.auth-check__box {
  width: 16px; height: 16px; border-radius: 4px;
  border: 1px solid rgba(0,0,0,0.15); background: #f8fafc;
  transition: all 150ms ease; flex-shrink: 0;
}
.auth-check input:checked + .auth-check__box { background: var(--brand-500); border-color: var(--brand-500); }

.auth-submit { width: 100%; justify-content: center; padding: 11px 20px; font-size: 14px; }
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.spin { animation: spin-slow 0.8s linear infinite; }
@keyframes spin-slow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.auth-error {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.18);
  border-radius: 8px; font-size: 13px; color: #dc2626;
}
.auth-success {
  padding: 10px 14px; border-radius: 8px; font-size: 13px;
  background: rgba(37,99,235,0.06); border: 1px solid rgba(37,99,235,0.18);
  color: var(--brand-600); text-align: center;
}

.auth-switch {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  font-size: 13px; color: var(--text-tertiary);
}
.auth-switch__link {
  background: none; border: none; cursor: pointer;
  color: var(--brand-400); font-weight: 600; font-size: 13px;
  transition: color 150ms ease;
}
.auth-switch__link:hover { color: var(--brand-300); }

/* Transition */
.auth-modal-enter-active { transition: opacity 0.25s ease; }
.auth-modal-leave-active { transition: opacity 0.2s ease; }
.auth-modal-enter-from,
.auth-modal-leave-to { opacity: 0; }

/* Dark mode */
:global([data-theme="dark"]) .auth-modal-window {
  background: rgba(35, 35, 35, 0.95);
}
:global([data-theme="dark"]) .macos-titlebar {
  background: rgba(30, 30, 30, 0.9);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}
:global([data-theme="dark"]) .macos-title { color: #999; }
:global([data-theme="dark"]) .auth-panel__eyebrow { color: var(--brand-400); }
:global([data-theme="dark"]) .auth-panel__title { color: #f1f5f9; }
:global([data-theme="dark"]) .auth-panel__sub { color: #94a3b8; }
:global([data-theme="dark"]) .input-label { color: #94a3b8; }
:global([data-theme="dark"]) .input-field {
  background: #1f2937; border-color: rgba(255,255,255,0.10); color: #f1f5f9;
}
:global([data-theme="dark"]) .input-field::placeholder { color: #6b7280; }
:global([data-theme="dark"]) .input-field:focus { border-color: var(--brand-400); box-shadow: 0 0 0 3px rgba(37,99,235,0.20); }
:global([data-theme="dark"]) .input-icon { color: #6b7280; }
:global([data-theme="dark"]) .auth-check { color: #94a3b8; }
:global([data-theme="dark"]) .auth-check__box { background: rgba(0,0,0,0.40); border-color: rgba(255,255,255,0.12); }
:global([data-theme="dark"]) .auth-error { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.20); color: #fca5a5; }
:global([data-theme="dark"]) .auth-success { background: rgba(37,99,235,0.08); border-color: rgba(37,99,235,0.20); color: #93c5fd; }
:global([data-theme="dark"]) .auth-switch { color: #6b7280; }
</style>
