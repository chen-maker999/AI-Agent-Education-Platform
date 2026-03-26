import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const user = ref(null)
  const showAuthModal = ref(false)
  const authModalMode = ref('login')

  const isAuthenticated = computed(() => Boolean(token.value))

  async function login(credentials) {
    try {
      const res = await authApi.login(credentials)
      if (res?.code === 200 && res?.data) {
        token.value = res.data.access_token
        refreshToken.value = res.data.refresh_token
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('refreshToken', res.data.refresh_token)
        await fetchUserInfo()
        return { success: true }
      }
      return { success: false, message: res?.message || '登录失败，请稍后重试。' }
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        '登录失败，请检查用户名和密码。'

      return {
        success: false,
        message: typeof message === 'string' ? message : '登录失败，请检查用户名和密码。'
      }
    }
  }

  async function register(payload) {
    try {
      return await authApi.register(payload)
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || error.message || '注册失败，请稍后重试。'
      }
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // Ignore logout network errors so local state is still cleared.
    }

    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function fetchUserInfo() {
    if (!token.value) {
      user.value = null
      return null
    }

    try {
      const res = await authApi.me()
      if (res?.code === 200) {
        user.value = res.data
        return user.value
      }
    } catch (error) {
      console.error('获取用户信息失败', error)
    }

    return null
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      return false
    }

    try {
      const res = await authApi.refresh({ refresh_token: refreshToken.value })
      if (res?.code === 200 && res?.data) {
        token.value = res.data.access_token
        refreshToken.value = res.data.refresh_token
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('refreshToken', res.data.refresh_token)
        return true
      }
    } catch {
      await logout()
    }

    return false
  }

  function openAuthModal(mode = 'login') {
    authModalMode.value = mode
    showAuthModal.value = true
  }

  function closeAuthModal() {
    showAuthModal.value = false
  }

  if (token.value) {
    fetchUserInfo()
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    showAuthModal,
    authModalMode,
    login,
    register,
    logout,
    fetchUserInfo,
    refreshAccessToken,
    openAuthModal,
    closeAuthModal
  }
})
