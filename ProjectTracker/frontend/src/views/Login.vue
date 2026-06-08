<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth   = useAuthStore()

const email    = ref('admin@company.com')
const password = ref('admin123')
const error    = ref('')
const loading  = ref(false)

async function submit() {
  error.value   = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-brand-light via-white to-slate-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md p-8">

      <!-- Logo -->
      <div class="flex items-center gap-3 mb-8">
        <div class="w-10 h-10 rounded-xl bg-brand flex items-center justify-center shadow">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-800">ProjectTracker</h1>
          <p class="text-xs text-slate-400">Team project management</p>
        </div>
      </div>

      <h2 class="text-lg font-semibold mb-1">Sign in</h2>
      <p class="text-sm text-slate-400 mb-6">Enter your credentials to continue.</p>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1">Email</label>
          <input v-model="email" type="email" class="input" placeholder="you@company.com" required />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1">Password</label>
          <input v-model="password" type="password" class="input" placeholder="••••••••" required />
        </div>

        <p v-if="error" class="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{{ error }}</p>

        <button type="submit" class="btn-primary w-full flex justify-center" :disabled="loading">
          <span v-if="!loading">Sign in</span>
          <svg v-else class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
        </button>
      </form>

      <p class="mt-6 text-xs text-center text-slate-400">
        Demo: <span class="font-mono">admin@company.com</span> / <span class="font-mono">admin123</span>
      </p>
    </div>
  </div>
</template>
