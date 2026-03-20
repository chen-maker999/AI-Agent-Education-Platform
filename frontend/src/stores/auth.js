import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')

  const isAuthenticated = computed(() => !!token.value)

  const login = async (credentials) => {
    try {
      const res = await authApi.login(credentials)
      if (res.code === 200) {
        token.value = res.data.access_token
        refreshToken.value = res.data.refresh_token
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('refreshToken', res.data.refresh_token)
        await fetchUserInfo()
        return { success: true }
      }
      return { success: false, message: res.message }
    } catch (error) {
      const msg = error.response?.data?.detail ?? error.response?.data?.message ?? error.message
      return { success: false, message: typeof msg === 'string' ? msg : '登录失败，请检查用户名和密码' }
    }
  }

  const register = async (data) => {
    try {
      const res = await authApi.register(data)
      return res
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (e) {}
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  const fetchUserInfo = async () => {
    try {
      const res = await authApi.me()
      console.log('fetchUserInfo response:', res)
      if (res.code === 200) {
        user.value = res.data
        console.log('User info set:', user.value)
      }
    } catch (e) {
      console.error('获取用户信息失败', e)
    }
  }

  const refreshAccessToken = async () => {
    try {
      const res = await authApi.refresh({ refresh_token: refreshToken.value })
      if (res.code === 200) {
        token.value = res.data.access_token
        refreshToken.value = res.data.refresh_token
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('refreshToken', res.data.refresh_token)
        return true
      }
    } catch (e) {
      logout()
    }
    return false
  }

  if (token.value) {
    fetchUserInfo()
  }

  return {
    token,
    user,
    refreshToken,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUserInfo,
    refreshAccessToken
  }
})
