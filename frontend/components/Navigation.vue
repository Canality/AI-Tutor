<template>
  <nav class="navigation">
    <div class="nav-container">
      <div class="nav-brand">
        <router-link to="/ai-tutor" class="brand">AI Tutor</router-link>
      </div>
      <div class="nav-menu">
        <router-link to="/ai-tutor" class="nav-item">智能辅导</router-link>
        <router-link to="/profile" class="nav-item">学习画像</router-link>
        <router-link to="/exercises" class="nav-item">练习推荐</router-link>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

// 处理退出登录
const handleLogout = () => {
  // 清除本地存储的 token
  localStorage.removeItem('token')
  // 跳转到登录页面
  router.push('/')
}
</script>

<style scoped>
.navigation {
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  padding: 15px 0;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand .brand {
  font-size: 20px;
  font-weight: bold;
  color: white;
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-brand .brand:hover {
  transform: scale(1.05);
}

.nav-menu {
  display: flex;
  gap: 24px;
  align-items: center;
}

.nav-item {
  color: white;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.1);
  transition: left 0.3s ease;
}

.nav-item:hover::before {
  left: 0;
}

.nav-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.logout-btn {
  padding: 8px 16px;
  background-color: rgba(255,255,255,0.2);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.logout-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.2);
  transition: left 0.3s ease;
}

.logout-btn:hover::before {
  left: 0;
}

.logout-btn:hover {
  background-color: rgba(255,255,255,0.3);
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 10px;
  }
  
  .nav-menu {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>