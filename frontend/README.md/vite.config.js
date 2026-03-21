import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 删除 server.proxy，因为后端已经允许 CORS，直接访问 8000 就行
})
