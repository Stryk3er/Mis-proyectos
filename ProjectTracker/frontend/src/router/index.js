import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login',    name: 'Login',     component: () => import('@/views/Login.vue'),     meta: { public: true } },
  { path: '/',         name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  const isPublic    = !!to.meta.public
  const isLoggedIn  = auth.isAuthenticated

  if (!isPublic && !isLoggedIn) return { name: 'Login' }
  if (isPublic && isLoggedIn && to.name === 'Login') return { name: 'Dashboard' }
})

export default router
