<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="brand">
          <img :src="elementIcon" alt="AI教育平台" class="brand-title-icon">
          <p>可嵌入式跨课程AI Agent通用架构平台</p>
        </div>
        <div class="features-visual">
          <div class="floating-element el-1"></div>
          <div class="floating-element el-2"></div>
          <div class="floating-element el-3"></div>
        </div>
      </div>
      <div class="login-right">
        <div class="login-card">
          <div class="login-header">
            <h2>欢迎回来</h2>
            <p>登录您的账号继续学习</p>
          </div>
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label>用户名 / 邮箱</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <input v-model="form.username" type="text" placeholder="请输入用户名或邮箱" required>
              </div>
            </div>
            <div class="form-group">
              <label>密码</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="请输入密码" required>
                <button type="button" class="toggle-password" @click="showPassword = !showPassword">
                  <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="form-options">
              <label class="checkbox">
                <input type="checkbox" v-model="form.remember">
                <span>记住我</span>
              </label>
              <a href="#" class="forgot-link">忘记密码？</a>
            </div>
            <button type="submit" class="btn-login" :disabled="loading">
              <span v-if="!loading">登录</span>
              <div v-else class="spinner"></div>
            </button>
            <div v-if="error" class="error-message">{{ error }}</div>
          </form>
          <div class="login-footer">
            <p>还没有账号？ <router-link to="/register">立即注册</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import elementIcon from '../../icons/icon_u7adlm4fwln/element.png'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '', remember: false })
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  const result = await authStore.login({
    username: form.username,
    password: form.password
  })
  
  loading.value = false
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.message || '登录失败，请检查用户名和密码'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
}

.login-container {
  display: flex;
  width: 100%;
  max-width: 1200px;
  margin: auto;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  padding: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.brand { position: relative; z-index: 1; }
.brand-title-icon {
  width: 187.5px;
  height: 187.5px;
  margin-bottom: 24px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}
.brand p { color: rgba(255,255,255,0.8); font-size: 16px; }

.features-visual {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.floating-element {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  animation: float 6s ease-in-out infinite;
}

.el-1 { width: 300px; height: 300px; top: -100px; right: -50px; animation-delay: 0s; }
.el-2 { width: 200px; height: 200px; bottom: -50px; left: 20%; animation-delay: 2s; }
.el-3 { width: 150px; height: 150px; top: 40%; right: 10%; animation-delay: 4s; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(10deg); }
}

.login-right {
  flex: 1;
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card { width: 100%; max-width: 400px; }

.login-header { margin-bottom: 40px; }
.login-header h2 { font-size: 32px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.login-header p { color: #64748b; }

.form-group { margin-bottom: 24px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px; }

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.3s;
}
.input-wrapper:focus-within { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.input-wrapper svg { color: #9ca3af; flex-shrink: 0; }
.input-wrapper input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: #1a1a2e;
  outline: none;
}

.toggle-password {
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  padding: 0;
}
.toggle-password:hover { color: #3b82f6; }

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #64748b;
}
.checkbox input { width: 16px; height: 16px; accent-color: #3b82f6; }

.forgot-link { font-size: 14px; color: #3b82f6; text-decoration: none; }
.forgot-link:hover { text-decoration: underline; }

.btn-login {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-login:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.3); }
.btn-login:disabled { opacity: 0.7; cursor: not-allowed; }

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

.login-footer {
  margin-top: 32px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
.login-footer a { color: #3b82f6; text-decoration: none; font-weight: 500; }
.login-footer a:hover { text-decoration: underline; }

@media (max-width: 900px) {
  .login-left { display: none; }
}
</style>
