<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-left">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1>AI教育平台</h1>
          <p>开启智能学习之旅</p>
        </div>
      </div>
      <div class="register-right">
        <div class="register-card">
          <div class="register-header">
            <h2>创建账号</h2>
            <p>注册一个新账号开始学习</p>
          </div>
          <form @submit.prevent="handleRegister">
            <div class="form-group">
              <label>用户名</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <input v-model="form.username" type="text" placeholder="字母开头，3-50字符" required>
              </div>
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                <input v-model="form.email" type="email" placeholder="请输入邮箱地址" required>
              </div>
            </div>
            <div class="form-group">
              <label>密码</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="至少8位，包含大小写字母和数字" required>
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
            <div class="form-group">
              <label>确认密码</label>
              <div class="input-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input v-model="form.confirmPassword" :type="showPassword ? 'text' : 'password'" placeholder="请再次输入密码" required>
              </div>
            </div>
            <div class="form-group">
              <label>角色</label>
              <div class="role-selector">
                <button type="button" v-for="role in roles" :key="role.value" :class="['role-btn', { active: form.role === role.value }]" @click="form.role = role.value">
                  <span class="role-icon">{{ role.icon }}</span>
                  <span class="role-label">{{ role.label }}</span>
                </button>
              </div>
            </div>
            <button type="submit" class="btn-register" :disabled="loading || !isValid">
              <span v-if="!loading">注册</span>
              <div v-else class="spinner"></div>
            </button>
            <div v-if="error" class="error-message">{{ error }}</div>
            <div v-if="success" class="success-message">{{ success }}</div>
          </form>
          <div class="register-footer">
            <p>已有账号？ <router-link to="/login">立即登录</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'student'
})

const roles = [
  { value: 'student', label: '学生', icon: '🎓' },
  { value: 'teacher', label: '教师', icon: '👨‍🏫' },
  { value: 'admin', label: '管理员', icon: '⚙️' }
]

const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref('')

const isValid = computed(() => {
  const { username, email, password, confirmPassword } = form
  // 基本字段检查
  if (!username || !email || !password || !confirmPassword) return false
  // 两次密码一致
  if (password !== confirmPassword) return false
  // 密码复杂度：至少8位，包含大小写字母和数字
  const passwordValid = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(password)
  return passwordValid
})

const handleRegister = async () => {
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  const result = await authStore.register({
    username: form.username,
    email: form.email,
    password: form.password,
    role: form.role
  })
  
  loading.value = false
  
  if (result.code === 201) {
    success.value = '注册成功，正在跳转到登录页...'
    setTimeout(() => router.push('/login'), 2000)
  } else {
    error.value = result.message || '注册失败，请稍后重试'
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.register-container {
  display: flex;
  width: 100%;
  max-width: 1000px;
  margin: auto;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.register-left {
  width: 350px;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand { text-align: center; }
.brand-icon {
  width: 80px;
  height: 80px;
  background: rgba(255,255,255,0.2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}
.brand-icon svg { width: 48px; height: 48px; color: white; }
.brand h1 { font-size: 28px; color: white; margin-bottom: 12px; }
.brand p { color: rgba(255,255,255,0.8); font-size: 16px; }

.register-right {
  flex: 1;
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-card { width: 100%; max-width: 400px; }

.register-header { margin-bottom: 32px; }
.register-header h2 { font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.register-header p { color: #64748b; }

.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px; }

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  transition: all 0.3s;
}
.input-wrapper:focus-within { border-color: #11998e; box-shadow: 0 0 0 3px rgba(17,153,142,0.1); }
.input-wrapper svg { color: #9ca3af; flex-shrink: 0; }
.input-wrapper input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
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
.toggle-password:hover { color: #11998e; }

.role-selector {
  display: flex;
  gap: 12px;
}

.role-btn {
  flex: 1;
  padding: 12px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.role-btn:hover { border-color: #11998e; }
.role-btn.active { border-color: #11998e; background: rgba(17,153,142,0.05); }
.role-icon { font-size: 24px; }
.role-label { font-size: 13px; color: #64748b; }
.role-btn.active .role-label { color: #11998e; font-weight: 500; }

.btn-register {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 8px;
}
.btn-register:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(17,153,142,0.3); }
.btn-register:disabled { opacity: 0.7; cursor: not-allowed; }

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

.success-message {
  margin-top: 16px;
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #16a34a;
  font-size: 14px;
  text-align: center;
}

.register-footer {
  margin-top: 24px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
.register-footer a { color: #11998e; text-decoration: none; font-weight: 500; }
.register-footer a:hover { text-decoration: underline; }

@media (max-width: 768px) {
  .register-left { display: none; }
}
</style>
