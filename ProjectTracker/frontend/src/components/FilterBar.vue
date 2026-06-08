<script setup>
import { reactive, watch } from 'vue'

const emit = defineEmits(['change'])

const filters = reactive({ search: '', status: '', priority: '', area: '' })

watch(filters, () => emit('change', { ...filters }), { deep: true })

const statuses   = [
  { value: 'on_track',  label: '🟢 On Track'  },
  { value: 'at_risk',   label: '🟡 At Risk'   },
  { value: 'delayed',   label: '🔴 Delayed'   },
  { value: 'completed', label: '✅ Completed'  },
  { value: 'on_hold',   label: '⏸ On Hold'    },
]
const priorities = ['high', 'medium', 'low']
const areas      = ['Infrastructure', 'Security', 'Development', 'Operations', 'HR', 'Finance']
</script>

<template>
  <div class="flex flex-wrap gap-3 items-center">
    <div class="relative flex-1 min-w-[180px]">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
      </svg>
      <input v-model="filters.search" type="text" placeholder="Search projects…" class="input pl-9" />
    </div>

    <select v-model="filters.status" class="input w-auto min-w-[140px]">
      <option value="">All statuses</option>
      <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option>
    </select>

    <select v-model="filters.priority" class="input w-auto min-w-[130px]">
      <option value="">All priorities</option>
      <option v-for="p in priorities" :key="p" :value="p" class="capitalize">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
    </select>

    <select v-model="filters.area" class="input w-auto min-w-[140px]">
      <option value="">All areas</option>
      <option v-for="a in areas" :key="a" :value="a">{{ a }}</option>
    </select>

    <button
      v-if="filters.search || filters.status || filters.priority || filters.area"
      @click="Object.assign(filters, { search:'', status:'', priority:'', area:'' })"
      class="text-xs text-slate-400 hover:text-slate-600 transition-colors whitespace-nowrap"
    >✕ Clear</button>
  </div>
</template>
