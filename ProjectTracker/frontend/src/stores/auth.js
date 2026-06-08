import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email, password) {
    const form = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', form)
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    await fetchMe()
  }

  async function fetchMe() {
    if (!token.value) return
    const { data } = await api.get('/auth/me')
    user.value = data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, isAuthenticated, login, fetchMe, logout }
})
