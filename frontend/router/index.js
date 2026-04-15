import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../pages/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'  // 根路径重定向到登录页
    },
    {
      path: '/login',
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
      component: () => import('../pages/AiTutorView.vue'),
      meta: { requiresAuth: true }  // 需要登录
    },
    {
      path: '/recommend',
      name: 'recommend',
      component: () => import('../pages/RecommendView.vue'),
      meta: { requiresAuth: true }  // 需要登录
    },
    {
      path: '/exercises',
      name: 'exercises',
      component: () => import('../pages/ExercisesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../pages/ProfileView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})


// 路由守卫：检查登录状态
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const isAuthenticated = !!token
  
  // 如果访问需要登录的页面但没有 token，跳转到登录页
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } 
  // 如果已登录但访问登录/注册页，跳转到 ai-tutor
  else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/ai-tutor')
  } 
  // 其他情况正常放行
  else {
    next()
  }
})

export default router
