<script setup>
const props = defineProps({ stats: Object })

const cards = [
  { key: 'total',     label: 'Total Projects', color: 'text-brand',        bg: 'bg-brand-light'  },
  { key: 'on_track',  label: 'On Track',        color: 'text-emerald-600',  bg: 'bg-emerald-50'   },
  { key: 'at_risk',   label: 'At Risk',         color: 'text-amber-600',    bg: 'bg-amber-50'     },
  { key: 'delayed',   label: 'Delayed',         color: 'text-red-600',      bg: 'bg-red-50'       },
  { key: 'completed', label: 'Completed',       color: 'text-blue-600',     bg: 'bg-blue-50'      },
  { key: 'avg_progress', label: 'Avg Progress', color: 'text-violet-600',   bg: 'bg-violet-50', suffix: '%' },
]
</script>

<template>
  <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
    <div v-for="c in cards" :key="c.key" class="card p-4">
      <div :class="[c.bg, 'w-8 h-8 rounded-lg flex items-center justify-center mb-3']">
        <span :class="[c.color, 'text-xs font-bold']">{{ c.key.charAt(0).toUpperCase() }}</span>
      </div>
      <p :class="[c.color, 'text-2xl font-bold leading-none']">
        {{ stats[c.key] }}{{ c.suffix || '' }}
      </p>
      <p class="text-xs text-slate-400 mt-1">{{ c.label }}</p>
    </div>
  </div>
  <!-- Skeleton -->
  <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
    <div v-for="i in 6" :key="i" class="card p-4 animate-pulse">
      <div class="w-8 h-8 rounded-lg bg-slate-100 mb-3"/>
      <div class="h-7 bg-slate-100 rounded w-12 mb-2"/>
      <div class="h-3 bg-slate-100 rounded w-20"/>
    </div>
  </div>
</template>
