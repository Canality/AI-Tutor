import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../pages/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../pages/RegisterView.vue')
    },
    {
      path: '/ai-tutor',
      name: 'ai-tutor',
      component: () => import('../pages/AiTutorView.vue')
    },
    {
      path: '/recommend',
      name: 'recommend',
      component: () => import('../pages/RecommendView.vue')
    }
  ]
})

export default router
