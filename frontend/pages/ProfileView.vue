<template>
  <div class="profile-container">
    <Navigation />
    <h1>学习画像</h1>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="profile-content">
      <div class="profile-card">
        <h2>个人信息</h2>
        <div class="info-item">
          <span class="label">用户名：</span>
          <span class="value">{{ profile.username || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="label">总答题数：</span>
          <span class="value">{{ profile.total_questions || 0 }}</span>
        </div>
        <div class="info-item">
          <span class="label">正确数：</span>
          <span class="value">{{ profile.correct_count || 0 }}</span>
        </div>
        <div class="info-item">
          <span class="label">正确率：</span>
          <span class="value">{{ calculateAccuracy() }}%</span>
        </div>
      </div>
      
      <div class="profile-card">
        <h2>知识点掌握度</h2>
        <div v-if="profile.knowledge_mastery" class="knowledge-mastery">
          <div 
            v-for="(mastery, knowledge) in profile.knowledge_mastery" 
            :key="knowledge"
            class="mastery-item"
          >
            <span class="knowledge">{{ knowledge }}</span>
            <div class="mastery-bar">
              <div 
                class="mastery-fill" 
                :style="{ width: `${mastery}%` }"
                :class="getMasteryLevel(mastery)"
              ></div>
            </div>
            <span class="mastery-value">{{ mastery }}%</span>
          </div>
        </div>
        <div v-else class="empty">暂无知识点掌握度数据</div>
      </div>
      
      <div class="profile-card">
        <h2>薄弱知识点</h2>
        <div v-if="profile.weak_points" class="weak-points">
          <div 
            v-for="(point, index) in profile.weak_points" 
            :key="index"
            class="weak-item"
          >
            {{ point }}
          </div>
        </div>
        <div v-else class="empty">暂无薄弱知识点数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Navigation from '../components/Navigation.vue'
import { profileAPI } from '../services/apiService'

const profile = ref({})
const loading = ref(true)
const error = ref('')

// 加载学生画像
onMounted(async () => {
  try {
    loading.value = true
    const data = await profileAPI.getProfile()
    profile.value = data
  } catch (err) {
    error.value = '加载学习画像失败：' + (err.message || '请稍后重试')
  } finally {
    loading.value = false
  }
})

// 计算正确率
const calculateAccuracy = () => {
  const total = profile.value.total_questions || 0
  const correct = profile.value.correct_count || 0
  if (total === 0) return 0
  return Math.round((correct / total) * 100)
}

// 获取掌握度等级
const getMasteryLevel = (mastery) => {
  if (mastery >= 80) return 'high'
  if (mastery >= 60) return 'medium'
  return 'low'
}
</script>

<style scoped>
.profile-container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.profile-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #4a90e2, #357abd);
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 700;
  position: relative;
  padding-bottom: 12px;
}

h1::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, #4a90e2, #357abd);
  border-radius: 3px;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  border-radius: 12px;
  margin: 20px 0;
}

.error {
  color: #ff4d4f;
  background-color: #fff1f0;
  border: 1px solid #ffccc7;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.profile-card {
  padding: 24px;
  border-radius: 12px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.profile-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #4a90e2, #357abd);
}

.profile-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

h2 {
  color: #333;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  padding-left: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 12px 16px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.info-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.label {
  color: #666;
  font-weight: 500;
  transition: color 0.3s ease;
}

.value {
  color: #333;
  font-weight: 600;
  transition: color 0.3s ease;
}

.knowledge-mastery {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mastery-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.mastery-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.knowledge {
  width: 120px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.mastery-bar {
  flex: 1;
  height: 12px;
  background-color: #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}

.mastery-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s ease;
  position: relative;
  overflow: hidden;
}

.mastery-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shine 2s infinite;
}

@keyframes shine {
  to {
    left: 100%;
  }
}

.mastery-fill.high {
  background: linear-gradient(90deg, #52c41a, #389e0d);
}

.mastery-fill.medium {
  background: linear-gradient(90deg, #faad14, #d48806);
}

.mastery-fill.low {
  background: linear-gradient(90deg, #ff4d4f, #cf1322);
}

.mastery-value {
  width: 60px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.weak-points {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.weak-item {
  padding: 10px 16px;
  background-color: #fff2e8;
  border: 1px solid #ffd591;
  border-radius: 20px;
  font-size: 14px;
  color: #d46b08;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.weak-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(212, 107, 8, 0.1);
  transition: left 0.3s ease;
}

.weak-item:hover::before {
  left: 0;
}

.weak-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(212, 107, 8, 0.2);
}

.empty {
  padding: 32px;
  text-align: center;
  color: #999;
  font-size: 14px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

@media (max-width: 768px) {
  .profile-container {
    margin: 15px;
    padding: 16px;
  }
  
  .profile-card {
    padding: 16px;
  }
  
  .mastery-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .knowledge {
    width: 100%;
  }
  
  .mastery-bar {
    width: 100%;
  }
  
  .mastery-value {
    align-self: flex-end;
  }
}
</style>