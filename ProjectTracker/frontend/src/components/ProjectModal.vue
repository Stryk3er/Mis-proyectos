<script setup>
import { ref, watch, computed } from 'vue'
import { useProjectsStore } from '@/stores/projects'

const props = defineProps({ project: Object, open: Boolean })
const emit  = defineEmits(['close'])

const store   = useProjectsStore()
const loading = ref(false)
const error   = ref('')

const blank = () => ({
  name: '', description: '', status: 'on_track', priority: 'medium',
  progress: 0, area: '', start_date: '', end_date: '', owner_id: null,
})

const form = ref(blank())

watch(() => props.open, (val) => {
  error.value = ''
  form.value  = props.project
    ? {
        name: props.project.name, description: props.project.description || '',
        status: props.project.status, priority: props.project.priority,
        progress: props.project.progress, area: props.project.area || '',
        start_date: props.project.start_date || '',
        end_date:   props.project.end_date   || '',
        owner_id:   props.project.owner?.id  || null,
      }
    : blank()
  if (val && !store.users.length) store.fetchUsers()
})

async function save() {
  if (!form.value.name.trim()) { error.value = 'Project name is required.'; return }
  loading.value = true
  error.value   = ''
  try {
    const payload = {
      ...form.value,
      progress: Number(form.value.progress),
      owner_id: form.value.owner_id || null,
      start_date: form.value.start_date || null,
      end_date:   form.value.end_date   || null,
    }
    if (props.project) await store.updateProject(props.project.id, payload)
    else               await store.createProject(payload)
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

async function remove() {
  if (!confirm('Delete this project?')) return
  loading.value = true
  try {
    await store.deleteProject(props.project.id)
    emit('close')
  } finally {
    loading.value = false
  }
}

const statusOptions   = ['on_track','at_risk','delayed','completed','on_hold']
const priorityOptions = ['high','medium','low']
const areaOptions     = ['Infrastructure','Security','Development','Operations','HR','Finance']
const statusLabel = { on_track:'On Track', at_risk:'At Risk', delayed:'Delayed', completed:'Completed', on_hold:'On Hold' }
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" @click.self="emit('close')">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 class="text-base font-semibold">{{ project ? 'Edit Project' : 'New Project' }}</h2>
            <button @click="emit('close')" class="text-slate-400 hover:text-slate-600 transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <div class="px-6 py-5 space-y-4">
            <!-- Name -->
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">Project name <span class="text-red-400">*</span></label>
              <input v-model="form.name" class="input" placeholder="e.g. Cloud Migration" />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">Description</label>
              <textarea v-model="form.description" class="input resize-none" rows="2" placeholder="Brief description…" />
            </div>

            <!-- Status + Priority -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">Status</label>
                <select v-model="form.status" class="input">
                  <option v-for="s in statusOptions" :key="s" :value="s">{{ statusLabel[s] }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">Priority</label>
                <select v-model="form.priority" class="input capitalize">
                  <option v-for="p in priorityOptions" :key="p" :value="p" class="capitalize">{{ p.charAt(0).toUpperCase()+p.slice(1) }}</option>
                </select>
              </div>
            </div>

            <!-- Progress -->
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">Progress — {{ form.progress }}%</label>
              <input v-model="form.progress" type="range" min="0" max="100" class="w-full accent-brand" />
            </div>

            <!-- Area + Owner -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">Area</label>
                <select v-model="form.area" class="input">
                  <option value="">— None —</option>
                  <option v-for="a in areaOptions" :key="a">{{ a }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">Owner</label>
                <select v-model="form.owner_id" class="input">
                  <option :value="null">— None —</option>
                  <option v-for="u in store.users" :key="u.id" :value="u.id">{{ u.name }}</option>
                </select>
              </div>
            </div>

            <!-- Dates -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">Start date</label>
                <input v-model="form.start_date" type="date" class="input" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">End date</label>
                <input v-model="form.end_date" type="date" class="input" />
              </div>
            </div>

            <p v-if="error" class="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{{ error }}</p>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-slate-50 rounded-b-2xl">
            <button v-if="project" @click="remove" class="btn-danger" :disabled="loading">Delete</button>
            <div v-else />
            <div class="flex gap-2">
              <button @click="emit('close')" class="btn-secondary">Cancel</button>
              <button @click="save" class="btn-primary" :disabled="loading">
                {{ loading ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
