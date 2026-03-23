<template>
  <div class="auth-root">
    <!-- Spline 动态背景 + 磨砂遮罩 -->
    <div class="auth-bg" aria-hidden="true">
      <iframe
        class="auth-bg__spline"
        src="https://my.spline.design/ailoginpagesplinehackathon-QLjqoZ6ku0r7DoIsHbyeAq7R/"
        frameborder="0"
        width="100%"
        height="100%"
        allow="autoplay; fullscreen"
      ></iframe>
      <div class="auth-bg__overlay"></div>
    </div>

    <div class="auth-layout">

      <!-- ═══ LEFT HERO ═══ -->
      <div class="auth-hero">
        <div class="auth-hero__logo">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
            <rect width="44" height="44" rx="13" fill="rgba(31,94,255,0.15)" stroke="rgba(61,125,255,0.35)" stroke-width="1"/>
            <path d="M11 22L22 11L33 22L22 33Z" fill="none" stroke="#6ba3ff" stroke-width="1.5"/>
            <circle cx="22" cy="22" r="4.5" fill="#2563eb"/>
            <circle cx="22" cy="11" r="2.2" fill="#0891b2"/>
            <circle cx="33" cy="22" r="2.2" fill="#a080ff"/>
            <circle cx="22" cy="33" r="2.2" fill="#20f0a8"/>
            <circle cx="11" cy="22" r="2.2" fill="#ffb850"/>
          </svg>
          <span class="auth-hero__brand">EduNavigator</span>
        </div>

        <div class="auth-hero__content">
          <transition name="hero-fade" mode="out-in">
            <!-- Login mode -->
            <div v-if="mode === 'login'" key="login">
              <div class="auth-hero__eyebrow">AI 驱动的教学平台</div>
              <h1 class="auth-hero__title">
                智学领航
                <span class="auth-hero__title-accent">· 无界探索</span>
              </h1>
              <p class="auth-hero__desc">
                可嵌入式跨课程 AI Agent 平台，融合知识图谱、认知诊断、自适应推荐与智能问答，为每位学习者构建专属的成长轨迹。
              </p>
              <div class="auth-hero__features">
                <div class="auth-feat" v-for="f in loginFeatures" :key="f.label">
                  <div class="auth-feat__dot" :style="{background: f.color, boxShadow: `0 0 8px ${f.color}`}"></div>
                  <span>{{ f.label }}</span>
                </div>
              </div>
            </div>

            <!-- Register mode -->
            <div v-else key="register">
              <div class="auth-hero__eyebrow">开始你的旅程</div>
              <h1 class="auth-hero__title auth-hero__title--reg">
                创建你的<br>
                <span class="auth-hero__title-accent">EduNavigator 账号</span>
              </h1>
              <p class="auth-hero__desc">
                注册后即可进入学生、教师或管理员工作区，使用统一的搜索、知识、作业、画像与平台接入能力。
              </p>
              <div class="auth-hero__chips">
                <span class="chip" v-for="c in regChips" :key="c">{{ c }}</span>
              </div>
            </div>
          </transition>
        </div>
      </div>

      <!-- ═══ RIGHT FORM ═══ -->
      <div class="auth-form-wrap">

        <!-- Login form -->
        <template v-if="mode === 'login'">
          <div class="macos-window">
            <div class="macos-titlebar">
              <div class="macos-dots">
                <span class="dot dot--close"></span>
                <span class="dot dot--minimize"></span>
                <span class="dot dot--maximize"></span>
              </div>
              <span class="macos-title">{{ mode === 'login' ? '登录 EduNavigator' : '创建账号' }}</span>
              <div class="macos-titlebar-spacer"></div>
            </div>
            <div class="macos-content auth-form-panel">
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
                  <button type="button" class="auth-switch__link" @click="mode = 'register'">立即注册</button>
                </div>
              </form>
            </div>
          </div>
        </template>

        <!-- Register form -->
        <template v-else>
          <div class="macos-window">
            <div class="macos-titlebar">
              <div class="macos-dots">
                <span class="dot dot--close"></span>
                <span class="dot dot--minimize"></span>
                <span class="dot dot--maximize"></span>
              </div>
              <span class="macos-title">{{ mode === 'login' ? '登录 EduNavigator' : '创建账号' }}</span>
              <div class="macos-titlebar-spacer"></div>
            </div>
            <div class="macos-content auth-form-panel">
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
                  <button type="button" class="auth-switch__link" @click="mode = 'login'">去登录</button>
                </div>
              </form>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const mode = ref(route.query.tab === 'register' ? 'register' : 'login')

const loginForm = reactive({ username: '', password: '', remember: false })
const loginLoading = ref(false)
const loginError = ref('')
const showPwd = ref(false)

async function handleLogin() {
  loginError.value = ''
  loginLoading.value = true
  const result = await authStore.login({ username: loginForm.username, password: loginForm.password })
  loginLoading.value = false
  if (result?.success) {
    router.push('/dashboard')
  } else {
    loginError.value = result?.message || '用户名或密码不正确'
  }
}

const regForm = reactive({ username: '', email: '', password: '', role: 'student' })
const regLoading = ref(false)
const regError = ref('')
const regSuccess = ref('')
const showRegPwd = ref(false)

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
    setTimeout(() => { mode.value = 'login' }, 1200)
  } else {
    regError.value = result?.message || '注册失败，请稍后重试。'
  }
}

const loginFeatures = [
  { label: 'RAG 知识库问答', color: '#2563eb' },
  { label: '跨课程知识图谱', color: '#0891b2' },
  { label: '认知诊断追踪', color: '#a080ff' },
  { label: '自适应学习推荐', color: '#20f0a8' },
  { label: '多模态作业批改', color: '#ffb850' },
]
const regChips = ['学生工作台', '教师工作台', '平台工作台']
</script>

<style scoped>
.auth-root { min-height: 100vh; background: var(--bg-canvas); display: flex; align-items: stretch; position: relative; overflow: hidden; }
.auth-bg {
  position: fixed; inset: 0;
  z-index: 0;
  background: var(--bg-canvas);
  overflow: hidden;
}
.auth-bg__spline {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  pointer-events: auto;
  border: none;
  z-index: 1;
}
.auth-bg__overlay {
  position: absolute; inset: 0;
  z-index: 2;
  background: rgba(10, 10, 20, 0.15);
  pointer-events: none;
}

.auth-layout { position: relative; z-index: 3; display: grid; grid-template-columns: 1fr 440px; width: 100%; min-height: 100vh; overflow: hidden; }

/* ── Left hero ── */
.auth-hero {
  position: relative; z-index: 1;
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 36px 48px; gap: 28px;
  background: transparent;
}
.auth-hero::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.55) 0%, rgba(0, 0, 0, 0.18) 55%, transparent 100%);
  z-index: 0;
  pointer-events: none;
}

.auth-hero__logo { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; }
.auth-hero__brand { font-family: var(--font-display2); font-size: 18px; font-weight: 700; color: #ffffff; }
.auth-hero__content { position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; justify-content: center; padding-bottom: 15%; }
.auth-hero__eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
  color: #fbbf24; display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}
.auth-hero__eyebrow::before { content: ''; display: block; width: 24px; height: 1px; background: #fbbf24; }
.auth-hero__title {
  font-family: var(--font-display); font-size: clamp(40px, 5vw, 64px);
  font-weight: 800; line-height: 1.1; color: #ffffff; margin-bottom: 16px;
}
.auth-hero__title--reg { font-size: clamp(32px, 4vw, 52px); }
.auth-hero__title-accent { color: #fbbf24; text-shadow: 0 0 24px rgba(251,191,36,0.55); }
.auth-hero__desc { font-size: 15px; line-height: 1.8; color: rgba(255,255,255,0.88); max-width: 520px; margin-bottom: 20px; }
.auth-hero__features { display: flex; flex-wrap: wrap; gap: 10px 20px; }
.auth-feat { display: flex; align-items: center; gap: 8px; font-size: 13px; color: rgba(255,255,255,0.88); }
.auth-feat__dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.auth-hero__chips { display: flex; flex-wrap: wrap; gap: 8px; }

/* ── Right form — white panel ── */
.auth-form-wrap {
  position: relative; z-index: 1;
  display: flex; align-items: center; justify-content: center;
  padding: 48px 40px;
  background: transparent;
  overflow-y: auto;
}

/* ── MacOS Window Style ── */
.macos-window {
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset,
    0 1px 0 rgba(255, 255, 255, 0.8) inset;
  overflow: hidden;
}

.macos-titlebar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(248, 248, 248, 0.8);
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
}

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
  padding: 28px 32px;
}

.auth-form-panel {
  width: 100%;
}

.auth-panel__header { margin-bottom: 28px; }
.auth-panel__eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--brand-500); margin-bottom: 6px;
}
.auth-panel__title { font-size: 24px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px; }
.auth-panel__sub { font-size: 13px; color: var(--text-muted); }

.auth-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.input-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.input-wrap { position: relative; display: flex; align-items: center; }
.input-icon { position: absolute; left: 14px; width: 18px; height: 18px; color: var(--text-muted); pointer-events: none; }
.input-field {
  width: 100%; padding: 13px 16px;
  border: 1px solid rgba(0,0,0,0.10); border-radius: var(--r-md);
  background: #f8fafc; font-size: 15px; color: var(--text-primary);
  transition: border-color 150ms ease, box-shadow 150ms ease; outline: none;
}
.input-field::placeholder { color: var(--text-muted); }
.input-field:focus { border-color: var(--brand-400); box-shadow: 0 0 0 3px rgba(37,99,235,0.10); background: #fff; }
.input-field--icon { padding-left: 46px; }
select.input-field { appearance: none; }
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

.auth-submit { width: 100%; justify-content: center; padding: 12px 20px; font-size: 14px; }
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.spin { animation: spin-slow 0.8s linear infinite; }

.auth-error {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.18);
  border-radius: var(--r-md); font-size: 13px; color: #dc2626;
}
.auth-success {
  padding: 10px 14px; border-radius: var(--r-md); font-size: 13px;
  background: rgba(37,99,235,0.06); border: 1px solid rgba(37,99,235,0.18);
  color: var(--brand-600); text-align: center;
}

/* ── Switch link ── */
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

/* ── Hero content transition ── */
.hero-fade-enter-active { transition: opacity 0.45s ease, transform 0.45s var(--ease-expo); }
.hero-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.hero-fade-enter-from { opacity: 0; transform: translateY(20px); }
.hero-fade-leave-to  { opacity: 0; transform: translateY(-12px); }

@media (max-width: 1100px) {
  .auth-layout { grid-template-columns: 1fr; }
  .auth-hero { display: none; }
  .auth-form-wrap { min-height: 100vh; }
}

/* ── MacOS Window Dark Mode ── */
:global([data-theme="dark"]) .macos-window {
  background: rgba(40, 40, 40, 0.85);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

:global([data-theme="dark"]) .macos-titlebar {
  background: rgba(30, 30, 30, 0.8);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

:global([data-theme="dark"]) .macos-title {
  color: #999;
}

/* ── Dark mode ── */
:global([data-theme="dark"]) .auth-form-wrap {
  background: transparent;
}
:global([data-theme="dark"]) .auth-panel__eyebrow { color: var(--brand-400); }
:global([data-theme="dark"]) .auth-panel__title { color: #f1f5f9; }
:global([data-theme="dark"]) .auth-panel__sub { color: #94a3b8; }
:global([data-theme="dark"]) .input-label { color: #94a3b8; }
:global([data-theme="dark"]) .input-field {
  background: #1f2937; border-color: rgba(255,255,255,0.10); color: #f1f5f9;
}
:global([data-theme="dark"]) .input-field::placeholder { color: #6b7280; }
:global([data-theme="dark"]) .input-field:focus { border-color: var(--brand-400); box-shadow: 0 0 0 3px rgba(37,99,235,0.20); background: #1f2937; }
:global([data-theme="dark"]) .input-icon { color: #6b7280; }
:global([data-theme="dark"]) .input-action { color: #6b7280; }
:global([data-theme="dark"]) .input-action:hover { color: #94a3b8; }
:global([data-theme="dark"]) .auth-check { color: #94a3b8; }
:global([data-theme="dark"]) .auth-check__box { background: rgba(0,0,0,0.40); border-color: rgba(255,255,255,0.12); }
:global([data-theme="dark"]) .auth-error { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.20); color: #fca5a5; }
:global([data-theme="dark"]) .auth-success { background: rgba(37,99,235,0.08); border-color: rgba(37,99,235,0.20); color: #93c5fd; }
:global([data-theme="dark"]) .auth-switch { color: #6b7280; }
:global([data-theme="dark"]) .auth-switch__link { color: var(--brand-400); }
:global([data-theme="dark"]) .auth-switch__link:hover { color: var(--brand-300); }
</style>
