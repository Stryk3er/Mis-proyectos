<script setup>
import { computed, ref } from 'vue'

const props  = defineProps({ projects: Array, loading: Boolean })
const emit   = defineEmits(['edit'])

const sortCol = ref('updated_at')
const sortAsc = ref(false)

function toggle(col) {
  if (sortCol.value === col) sortAsc.value = !sortAsc.value
  else { sortCol.value = col; sortAsc.value = true }
}

const sorted = computed(() => {
  return [...(props.projects || [])].sort((a, b) => {
    let av = a[sortCol.value], bv = b[sortCol.value]
    if (typeof av === 'string') av = av.toLowerCase()
    if (typeof bv === 'string') bv = bv.toLowerCase()
    if (av == null) return 1
    if (bv == null) return -1
    return sortAsc.value ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1)
  })
})

const statusLabel = { on_track:'On Track', at_risk:'At Risk', delayed:'Delayed', completed:'Completed', on_hold:'On Hold' }
const priorityColor = { high:'text-red-600 bg-red-50', medium:'text-amber-600 bg-amber-50', low:'text-emerald-600 bg-emerald-50' }

function progColor(p) {
  if (p >= 70) return '#22c55e'
  if (p >= 40) return '#f59e0b'
  return '#ef4444'
}

function daysLeft(dateStr) {
  if (!dateStr) return null
  return Math.round((new Date(dateStr) - new Date()) / 86400000)
}

function fmtDate(d) {
  if (!d) return '—'
  const [y,m,dd] = d.split('-')
  return `${dd}/${m}/${y}`
}

function arrowFor(col) {
  if (sortCol.value !== col) return '↕'
  return sortAsc.value ? '↑' : '↓'
}

function avatarColor(name) {
  const colors = ['#6366f1','#f43f5e','#0ea5e9','#10b981','#f59e0b','#8b5cf6']
  let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) % colors.length
  return colors[h]
}
function initials(name) {
  return name.split(' ').slice(0,2).map(p => p[0]?.toUpperCase()||'').join('')
}
</script>

<template>
  <div class="card overflow-hidden">
    <!-- Loading skeleton -->
    <div v-if="loading" class="divide-y divide-slate-100">
      <div v-for="i in 5" :key="i" class="flex items-center gap-4 px-5 py-4 animate-pulse">
        <div class="h-4 bg-slate-100 rounded w-1/3"/>
        <div class="h-4 bg-slate-100 rounded w-1/6"/>
        <div class="h-4 bg-slate-100 rounded w-1/6"/>
        <div class="h-4 bg-slate-100 rounded w-1/4"/>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!sorted.length" class="flex flex-col items-center justify-center py-16 text-center">
      <svg class="w-12 h-12 text-slate-200 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2"/>
      </svg>
      <p class="text-sm text-slate-400">No projects found.</p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-slate-50 text-xs font-semibold text-slate-400 uppercase tracking-wide">
            <th class="px-5 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('name')">Project {{ arrowFor('name') }}</th>
            <th class="px-4 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('area')">Area {{ arrowFor('area') }}</th>
            <th class="px-4 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('status')">Status {{ arrowFor('status') }}</th>
            <th class="px-4 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('progress')">Progress {{ arrowFor('progress') }}</th>
            <th class="px-4 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('priority')">Priority {{ arrowFor('priority') }}</th>
            <th class="px-4 py-3 text-left cursor-pointer hover:text-brand transition-colors" @click="toggle('end_date')">Due date {{ arrowFor('end_date') }}</th>
            <th class="px-4 py-3 text-left">Owner</th>
            <th class="px-4 py-3"/>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-50">
          <tr v-for="p in sorted" :key="p.id" class="hover:bg-slate-50/60 transition-colors">

            <!-- Name -->
            <td class="px-5 py-3.5 max-w-[220px]">
              <p class="font-semibold text-slate-800 truncate">{{ p.name }}</p>
              <p v-if="p.description" class="text-xs text-slate-400 truncate mt-0.5">{{ p.description }}</p>
            </td>

            <!-- Area -->
            <td class="px-4 py-3.5">
              <span v-if="p.area" class="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">{{ p.area }}</span>
              <span v-else class="text-slate-300">—</span>
            </td>

            <!-- Status -->
            <td class="px-4 py-3.5">
              <span :class="['badge-'+p.status, 'text-xs font-semibold px-2.5 py-0.5 rounded-full inline-flex items-center gap-1.5']">
                <span class="w-1.5 h-1.5 rounded-full" :class="{
                  'bg-emerald-500': p.status==='on_track',
                  'bg-amber-400':   p.status==='at_risk',
                  'bg-red-500':     p.status==='delayed',
                  'bg-blue-400':    p.status==='completed',
                  'bg-slate-400':   p.status==='on_hold',
                }"/>
                {{ statusLabel[p.status] }}
              </span>
            </td>

            <!-- Progress -->
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-2 min-w-[110px]">
                <div class="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all" :style="{ width: p.progress+'%', background: progColor(p.progress) }"/>
                </div>
                <span class="text-xs font-semibold w-8 text-right" :style="{ color: progColor(p.progress) }">{{ p.progress }}%</span>
              </div>
            </td>

            <!-- Priority -->
            <td class="px-4 py-3.5">
              <span :class="[priorityColor[p.priority], 'text-xs font-bold px-2 py-0.5 rounded-md capitalize']">{{ p.priority }}</span>
            </td>

            <!-- Due date -->
            <td class="px-4 py-3.5 text-xs">
              <template v-if="p.end_date">
                <span :class="{
                  'text-red-600 font-semibold':   daysLeft(p.end_date) < 0,
                  'text-amber-600 font-semibold': daysLeft(p.end_date) >= 0 && daysLeft(p.end_date) <= 7,
                  'text-slate-500':               daysLeft(p.end_date) > 7,
                }">
                  <template v-if="daysLeft(p.end_date) < 0">{{ -daysLeft(p.end_date) }}d overdue</template>
                  <template v-else-if="daysLeft(p.end_date) === 0">Today</template>
                  <template v-else-if="daysLeft(p.end_date) <= 7">In {{ daysLeft(p.end_date) }}d</template>
                  <template v-else>{{ fmtDate(p.end_date) }}</template>
                </span>
              </template>
              <span v-else class="text-slate-300">—</span>
            </td>

            <!-- Owner -->
            <td class="px-4 py-3.5">
              <div v-if="p.owner" class="flex items-center gap-2">
                <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                  :style="{ background: avatarColor(p.owner.name) }">
                  {{ initials(p.owner.name) }}
                </div>
                <span class="text-xs text-slate-600 truncate max-w-[80px]">{{ p.owner.name }}</span>
              </div>
              <span v-else class="text-slate-300 text-xs">—</span>
            </td>

            <!-- Actions -->
            <td class="px-4 py-3.5">
              <button @click="emit('edit', p)"
                class="p-1.5 rounded-lg text-slate-400 hover:text-brand hover:bg-brand-light transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
