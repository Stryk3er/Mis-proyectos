<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore }     from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import KpiCards     from '@/components/KpiCards.vue'
import FilterBar    from '@/components/FilterBar.vue'
import ProjectTable from '@/components/ProjectTable.vue'
import ProjectModal from '@/components/ProjectModal.vue'

const auth     = useAuthStore()
const store    = useProjectsStore()
const modal    = ref(false)
const editing  = ref(null)
const exporting = ref(false)

function openNew()   { editing.value = null; modal.value = true }
function openEdit(p) { editing.value = p;    modal.value = true }
function onClose()   { modal.value = false;  editing.value = null }

async function exportPDF() {
  exporting.value = true
  try {
    const token = localStorage.getItem('access_token')
    const res   = await fetch('/api/reports/pdf', {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error('Failed to generate report')
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `project-report-${new Date().toISOString().split('T')[0]}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('PDF export error:', e)
  } finally {
    exporting.value = false
  }
}

function onFilter(f) {
  store.fetchAll({
    search:   f.search   || undefined,
    status:   f.status   || undefined,
    priority: f.priority || undefined,
    area:     f.area     || undefined,
  })
}

onMounted(async () => {
  try {
    await auth.fetchMe()
    await Promise.all([store.fetchAll(), store.fetchStats()])
  } catch (e) {
    console.error('Dashboard init error:', e)
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col">

    <!-- Topbar -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div class="max-w-7xl mx-auto px-5 h-14 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-brand flex items-center justify-center shadow-sm">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2"/>
            </svg>
          </div>
          <span class="font-bold text-slate-800 text-sm">ProjectTracker</span>
        </div>

        <div class="flex items-center gap-3">
          <div v-if="auth.user" class="flex items-center gap-2 text-sm text-slate-500">
            <div class="w-7 h-7 rounded-full bg-brand flex items-center justify-center text-white text-xs font-bold">
              {{ auth.user.name.charAt(0) }}
            </div>
            <span class="hidden sm:inline font-medium text-slate-700">{{ auth.user.name }}</span>
          </div>
          <button @click="auth.logout(); $router.push('/login')"
            class="text-xs text-slate-400 hover:text-slate-600 transition-colors">
            Sign out
          </button>
        </div>
      </div>
    </header>

    <!-- Main -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-5 py-6 space-y-6">

      <!-- Page title + actions -->
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-slate-800">Project Dashboard</h1>
          <p class="text-sm text-slate-400 mt-0.5">Track all ongoing initiatives at a glance.</p>
        </div>
        <div class="flex gap-2">
          <button @click="exportPDF" :disabled="exporting" class="btn-secondary flex items-center gap-1.5 whitespace-nowrap">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            {{ exporting ? 'Generating…' : 'Export PDF' }}
          </button>
          <button @click="openNew" class="btn-primary flex items-center gap-1.5 whitespace-nowrap">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            New project
          </button>
        </div>
      </div>

      <!-- KPI cards -->
      <KpiCards :stats="store.stats" />

      <!-- Filters -->
      <FilterBar @change="onFilter" />

      <!-- Table -->
      <ProjectTable :projects="store.projects" :loading="store.loading" @edit="openEdit" />

    </main>

    <!-- Modal -->
    <ProjectModal :open="modal" :project="editing" @close="onClose" />
  </div>
</template>
