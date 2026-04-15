import './assets/base.css'
import { createApp } from 'vue'
import App from './App.vue'
import router, { setupAuthSessionMonitor } from './router'  // 导入路由配置

const app = createApp(App)     // 创建应用
app.use(router)                // 使用路由（关键！）
setupAuthSessionMonitor(router) // 启动登录会话过期自动退出监控
app.mount('#app')              // 挂载到页面上
