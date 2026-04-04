import { defineStore } from 'pinia'
import {
  clearSession,
  fetchCurrentUser,
  getPersistedUser,
  loginWithCredentials,
  persistUser,
} from '../services/authService'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: getPersistedUser(),
    isLoading: false,
    isInitialized: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isAdmin: (state) => Boolean(state.user?.is_admin),
    role: (state) => (state.user?.is_admin ? 'admin' : state.user ? 'user' : null),
  },

  actions: {
    async init() {
      if (this.isInitialized) return
      if (!this.user) {
        this.isInitialized = true
        return
      }
      try {
        const current = await fetchCurrentUser()
        this.user = current
        persistUser(current)
      } catch {
        this.user = null
        clearSession()
      } finally {
        this.isInitialized = true
      }
    },

    async login({ email, password }) {
      this.isLoading = true
      try {
        await loginWithCredentials(email, password)
        const current = await fetchCurrentUser()
        this.user = current
        persistUser(current)
        return current
      } finally {
        this.isLoading = false
      }
    },

    logout() {
      this.user = null
      clearSession()
    },
  },
})
