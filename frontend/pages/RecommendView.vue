<!-- src/pages/RecommendView.vue -->
<template>
  <div class="recommend-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 左侧边栏（与主界面一致） -->
    <aside class="sidebar">
      <div class="user-section" @click="showEditProfile = true">
        <div class="user-avatar-large">
          <img v-if="isImageAvatar(userInfo.avatar)" :src="userInfo.avatar" class="avatar-img" />
          <span v-else>{{ userInfo.avatar }}</span>
        </div>
        <div class="user-info" v-show="!isSidebarCollapsed">
          <span class="user-name">{{ userInfo.name }}</span>
          <span class="edit-hint">✏️ 点击编辑</span>
        </div>
      </div>
      
      <button class="toggle-btn" @click.stop="toggleSidebar">
        {{ isSidebarCollapsed ? '→' : '←' }}
      </button>

      <div class="quick-nav" v-show="!isSidebarCollapsed">
        <router-link to="/ai-tutor" class="nav-item">
          <span class="nav-icon">💬</span>
          <span>AI 提问</span>
        </router-link>
        <router-link to="/recommend" class="nav-item active">
          <span class="nav-icon">✨</span>
          <span>数列推荐</span>
        </router-link>
      </div>

      <div class="sidebar-footer" v-show="!isSidebarCollapsed">
        <button class="logout-btn" @click="logout">
          <span>🚪</span>
          <span>退出登录</span>
        </button>
      </div>
    </aside>
    
    <!-- 主内容：数列推荐列表 -->
    <main class="main-content">
      <div class="mobile-header">
        <button class="mobile-menu-btn" @click="toggleSidebar">☰</button>
        <span class="mobile-title">数列专项练习</span>
      </div>

      <div class="recommend-container">
        <div class="page-header">
          <h1>📐 数列专项练习</h1>
          <p>针对数列章节的智能推荐题目</p>
        </div>

        <!-- 题目列表 -->
        <div class="problem-list">
          <div 
            v-for="(item, index) in problemList" 
            :key="item.id"
            class="problem-card"
          >
            <div class="card-number">#{{ index + 1 }}</div>
            <div class="card-content">
              <h3 class="card-title">{{ item.title }}</h3>
              <p class="card-desc">{{ item.description }}</p>
              <div class="card-tags">
                <span class="tag">{{ item.type }}</span>
                <span class="tag difficulty">{{ item.difficulty }}</span>
              </div>
            </div>
            <button class="practice-btn" @click="startPractice(item)">
              练习
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 侧边栏状态
const isSidebarCollapsed = ref(false)
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 用户信息
const userInfo = reactive({
  name: '学习者',
  avatar: '👤'
})

const loadUserInfo = () => {
  try {
    const saved = localStorage.getItem('user_info')
    if (saved) {
      const data = JSON.parse(saved)
      userInfo.name = data.username || data.name || '学习者'
      if (data.avatar) userInfo.avatar = data.avatar
    }
  } catch (e) {
    console.error('加载用户信息失败:', e)
  }
}

const isImageAvatar = (avatar) => {
  return avatar && (avatar.startsWith('data:') || avatar.startsWith('blob:') || avatar.startsWith('http'))
}

const logout = () => {
  if (confirm('确定要退出登录吗？')) {
    router.push('/')
  }
}

// 数列题目列表（mock数据）
const problemList = ref([
  {
    id: 1,
    title: '等差数列基础求和',
    description: '已知等差数列{aₙ}中，a₃=5，a₇=13，求前10项和S₁₀。',
    type: '基础题',
    difficulty: '简单'
  },
  {
    id: 2,
    title: '等比数列通项公式',
    description: '等比数列{aₙ}中，a₂=6，a₅=48，求通项公式aₙ。',
    type: '公式应用',
    difficulty: '中等'
  },
  {
    id: 3,
    title: '裂项相消法求和',
    description: '求数列1/(n(n+1))的前n项和，并用裂项相消法证明。',
    type: '求和技巧',
    difficulty: '中等'
  },
  {
    id: 4,
    title: '错位相减法',
    description: '求数列{n·2ⁿ}的前n项和Sₙ。',
    type: '求和技巧',
    difficulty: '较难'
  },
  {
    id: 5,
    title: '数列与不等式综合',
    description: '已知数列{aₙ}满足递推关系，证明对于任意正整数n，有aₙ < 2。',
    type: '综合题',
    difficulty: '困难'
  },
  {
    id: 6,
    title: '递推数列求通项',
    description: '已知a₁=1，aₙ₊₁=2aₙ+1，求通项公式。',
    type: '构造法',
    difficulty: '中等'
  }
])

const startPractice = (item) => {
  // 后续对接：跳转到AI Tutor并自动填入题目
  if (confirm(`进入 AI Tutor 解答：${item.title}`)) {
    router.push('/ai-tutor')
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.recommend-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background-color: #ffffff;
  position: fixed;
  top: 0;
  left: 0;
}

/* 侧边栏（与AiTutorView一致） */
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background-color: #f9f9f9;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  position: relative;
  transition: all 0.3s ease;
  overflow: hidden;
}

.recommend-page.sidebar-collapsed .sidebar {
  width: 60px;
  min-width: 60px;
  padding: 20px 8px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-section:hover { background-color: #f0f0f0; }

.user-avatar-large {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.user-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.edit-hint { font-size: 11px; color: #999; margin-top: 2px; }

.toggle-btn {
  position: absolute;
  right: -12px;
  top: 80px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: white;
  border: 1px solid #e0e0e0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #666;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 10;
}

/* 导航 */
.quick-nav {
  margin-bottom: 16px;
  border-bottom: 1px solid #e5e5e5;
  padding-bottom: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  text-decoration: none;
  color: #666;
  font-size: 14px;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.nav-item:hover {
  background-color: #f0f0f0;
  color: #1d1d1f;
}

.nav-item.active {
  background-color: #e8e8e8;
  color: #1d1d1f;
  font-weight: 600;
}

.nav-icon { font-size: 18px; }

.sidebar-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #e5e5e5;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.logout-btn:hover { background: #ffebee; color: #c62828; }

/* 主内容 */
.main-content {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  background: #fafafa;
}

.mobile-header {
  display: none;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e5e5;
  background: white;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}

.mobile-title { font-size: 16px; font-weight: 600; flex: 1; text-align: center; }

.recommend-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* 页面标题 */
.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1d1d1f;
  margin-bottom: 8px;
}

.page-header p {
  font-size: 15px;
  color: #86868b;
}

/* 题目卡片列表 */
.problem-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.problem-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e5e5e5;
  display: flex;
  align-items: flex-start;
  gap: 20px;
  transition: all 0.2s;
}

.problem-card:hover {
  border-color: #0071e3;
  box-shadow: 0 4px 20px rgba(0,113,227,0.1);
  transform: translateY(-2px);
}

.card-number {
  width: 40px;
  height: 40px;
  background: #f0f7ff;
  color: #0071e3;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 8px;
}

.card-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 12px;
}

.card-tags {
  display: flex;
  gap: 8px;
}

.tag {
  padding: 4px 10px;
  background: #f5f5f7;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
}

.tag.difficulty {
  background: #fff7e6;
  color: #fa8c16;
}

.practice-btn {
  padding: 10px 24px;
  background: #1d1d1f;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.practice-btn:hover {
  background: #000;
  transform: scale(1.05);
}

/* 响应式 */
@media (max-width: 1024px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: 2px 0 8px rgba(0,0,0,0.1);
  }
  
  .recommend-page.sidebar-collapsed .sidebar {
    transform: translateX(-100%);
  }
  
  .mobile-header { display: flex; }
}

@media (max-width: 640px) {
  .problem-card {
    flex-direction: column;
    gap: 16px;
  }
  
  .practice-btn {
    width: 100%;
  }
}
</style>
