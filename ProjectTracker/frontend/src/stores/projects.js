import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref([])
  const stats    = ref(null)
  const users    = ref([])
  const loading  = ref(false)

  async function fetchAll(filters = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/projects/', { params: filters })
      projects.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    const { data } = await api.get('/projects/stats')
    stats.value = data
  }

  async function fetchUsers() {
    const { data } = await api.get('/auth/users')
    users.value = data
  }

  async function createProject(payload) {
    const { data } = await api.post('/projects/', payload)
    await Promise.all([fetchAll(), fetchStats()])
    return data
  }

  async function updateProject(id, payload) {
    const { data } = await api.patch(`/projects/${id}`, payload)
    await Promise.all([fetchAll(), fetchStats()])
    return data
  }

  async function deleteProject(id) {
    await api.delete(`/projects/${id}`)
    await Promise.all([fetchAll(), fetchStats()])
  }

  async function addUpdate(projectId, content, progressSnapshot) {
    const { data } = await api.post(`/projects/${projectId}/updates`, {
      content, progress_snapshot: progressSnapshot,
    })
    await fetchAll()
    return data
  }

  return {
    projects, stats, users, loading,
    fetchAll, fetchStats, fetchUsers,
    createProject, updateProject, deleteProject, addUpdate,
  }
})
