import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'  // 导入路由配置

const app = createApp(App)     // 创建应用
app.use(router)                // 使用路由（关键！）
app.mount('#app')              // 挂载到页面上
