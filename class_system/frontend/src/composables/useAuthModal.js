import { useAuthStore } from '@/stores/auth'

export function useAuthModal() {
  const authStore = useAuthStore()

  function openLogin() {
    authStore.openAuthModal('login')
  }

  function openRegister() {
    authStore.openAuthModal('register')
  }

  function closeAuth() {
    authStore.closeAuthModal()
  }

  function requireAuth(callback) {
    if (authStore.isAuthenticated) {
      callback?.()
    } else {
      authStore.openAuthModal('login')
    }
  }

  return {
    openLogin,
    openRegister,
    closeAuth,
    requireAuth,
    showAuthModal: authStore.showAuthModal,
    authModalMode: authStore.authModalMode
  }
}
