<template>
  <div class="nav-wrapper">
    <!-- 折叠按钮 -->
    <button 
      class="nav-toggle" 
      @click="isNavOpen = !isNavOpen"
      :class="{ 'nav-open': isNavOpen }"
    >
      <span class="toggle-icon">{{ isNavOpen ? '✕' : '☰' }}</span>
    </button>
    
    <!-- 导航栏 -->
    <nav class="navigation" :class="{ 'nav-hidden': !isNavOpen }">
      <div class="nav-container">
        <div class="nav-brand">
          <router-link to="/ai-tutor" class="brand">AI Tutor</router-link>
        </div>
        <div class="nav-menu">
          <router-link to="/ai-tutor" class="nav-item" @click="closeNavOnMobile">
            <span class="nav-icon">🤖</span>
            <span class="nav-text">智能辅导</span>
          </router-link>
          <router-link to="/profile" class="nav-item" @click="closeNavOnMobile">
            <span class="nav-icon">👤</span>
            <span class="nav-text">学习画像</span>
          </router-link>
          <router-link to="/exercises" class="nav-item" @click="closeNavOnMobile">
            <span class="nav-icon">📝</span>
            <span class="nav-text">练习推荐</span>
          </router-link>
          <button class="logout-btn" @click="handleLogout">
            <span class="nav-icon">🚪</span>
            <span class="nav-text">退出登录</span>
          </button>
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isNavOpen = ref(true) // 默认展开

// 在移动端自动折叠
const checkMobile = () => {
  if (window.innerWidth <= 768) {
    isNavOpen.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// 移动端点击菜单项后自动关闭
const closeNavOnMobile = () => {
  if (window.innerWidth <= 768) {
    isNavOpen.value = false
  }
}

// 处理退出登录
const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/')
}
</script>

<style scoped>
.nav-wrapper {
  position: relative;
}

/* 折叠按钮 */
.nav-toggle {
  position: fixed;
  top: 15px;
  left: 15px;
  z-index: 1001;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  transition: all 0.3s ease;
}

.nav-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.nav-toggle.nav-open {
  left: 270px;
}

.toggle-icon {
  font-weight: bold;
}

/* 导航栏 */
.navigation {
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  padding: 15px 0;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  height: 100vh;
  z-index: 1000;
  transition: transform 0.3s ease;
}

.navigation.nav-hidden {
  transform: translateX(-100%);
}

.nav-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 60px 20px 20px;
}

.nav-brand {
  margin-bottom: 30px;
  text-align: center;
}

.nav-brand .brand {
  font-size: 24px;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.1);
}

.nav-item:hover {
  background: rgba(255,255,255,0.2);
  transform: translateX(5px);
}

.nav-icon {
  font-size: 20px;
  width: 30px;
  text-align: center;
}

.nav-text {
  flex: 1;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.15);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: auto;
}

.logout-btn:hover {
  background: rgba(255,255,255,0.25);
  transform: translateX(5px);
}

/* 响应式 */
@media (max-width: 768px) {
  .navigation {
    width: 100%;
  }
  
  .nav-toggle.nav-open {
    left: auto;
    right: 15px;
  }
}

/* 主内容区域需要调整边距 */
:global(.main-content) {
  margin-left: 250px;
  transition: margin-left 0.3s ease;
}

:global(.main-content.nav-collapsed) {
  margin-left: 0;
}

@media (max-width: 768px) {
  :global(.main-content) {
    margin-left: 0;
  }
}
</style>
