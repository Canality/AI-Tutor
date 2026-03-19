<template>
  <div class="exercises-container">
    <Navigation />
    <h1>练习推荐</h1>
    
    <div class="tabs">
      <button 
        :class="['tab', activeTab === 'recommend' ? 'active' : '']" 
        @click="activeTab = 'recommend'"
      >
        推荐练习
      </button>
      <button 
        :class="['tab', activeTab === 'plan' ? 'active' : '']" 
        @click="activeTab = 'plan'"
      >
        学习计划
      </button>
    </div>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- 推荐练习 -->
      <div v-if="activeTab === 'recommend'" class="recommend-content">
        <h2>个性化推荐练习题</h2>
        <div v-if="recommendations.length > 0" class="exercises-list">
          <div 
            v-for="(exercise, index) in recommendations" 
            :key="index"
            class="exercise-item"
          >
            <div class="exercise-header">
              <h3>题目 {{ index + 1 }}</h3>
              <span class="difficulty" :class="getDifficultyClass(exercise.difficulty)">
                {{ getDifficultyText(exercise.difficulty) }}
              </span>
            </div>
            <div class="exercise-content">
              {{ exercise.content }}
            </div>
            <div class="exercise-footer">
              <div class="knowledge-points">
                <span 
                  v-for="(point, idx) in exercise.knowledge_points" 
                  :key="idx"
                  class="knowledge-tag"
                >
                  {{ point }}
                </span>
              </div>
              <button class="solve-btn">开始解题</button>
            </div>
          </div>
        </div>
        <div v-else class="empty">暂无推荐练习题</div>
      </div>
      
      <!-- 学习计划 -->
      <div v-else-if="activeTab === 'plan'" class="plan-content">
        <h2>短期学习计划</h2>
        <div v-if="plan" class="plan-details">
          <div class="plan-item">
            <h3>计划目标</h3>
            <p>{{ plan.goal }}</p>
          </div>
          <div class="plan-item">
            <h3>时间安排</h3>
            <div class="schedule">
              <div 
                v-for="(day, index) in plan.schedule" 
                :key="index"
                class="day-item"
              >
                <div class="day-header">第 {{ index + 1 }} 天</div>
                <div class="day-content">
                  <ul>
                    <li v-for="(task, taskIndex) in day.tasks" :key="taskIndex">
                      {{ task }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div class="plan-item">
            <h3>预期效果</h3>
            <p>{{ plan.expected_outcome }}</p>
          </div>
        </div>
        <div v-else class="empty">暂无学习计划</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Navigation from '../components/Navigation.vue'
import { exercisesAPI } from '../services/apiService'

const activeTab = ref('recommend')
const recommendations = ref([])
const plan = ref(null)
const loading = ref(false)
const error = ref('')

// 加载推荐练习题
const loadRecommendations = async () => {
  try {
    loading.value = true
    const data = await exercisesAPI.getRecommendations()
    recommendations.value = data.exercises || []
  } catch (err) {
    error.value = '加载推荐练习题失败：' + (err.message || '请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载学习计划
const loadPlan = async () => {
  try {
    loading.value = true
    const data = await exercisesAPI.getPlan()
    plan.value = data
  } catch (err) {
    error.value = '加载学习计划失败：' + (err.message || '请稍后重试')
  } finally {
    loading.value = false
  }
}

// 监听标签页变化
watch(activeTab, (newTab) => {
  if (newTab === 'recommend') {
    loadRecommendations()
  } else if (newTab === 'plan') {
    loadPlan()
  }
})

// 初始化
onMounted(() => {
  loadRecommendations()
})

// 获取难度等级的样式类
const getDifficultyClass = (difficulty) => {
  if (difficulty <= 2) return 'easy'
  if (difficulty <= 3) return 'medium'
  return 'hard'
}

// 获取难度等级的文本
const getDifficultyText = (difficulty) => {
  if (difficulty <= 2) return '简单'
  if (difficulty <= 3) return '中等'
  return '困难'
}
</script>

<style scoped>
.exercises-container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.exercises-container::before {
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

.tabs {
  display: flex;
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f0f0f0;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}

.tab {
  flex: 1;
  padding: 12px 20px;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.05);
  transition: left 0.3s ease;
}

.tab:hover::before {
  left: 0;
}

.tab:hover {
  color: #333;
}

.tab.active {
  color: white;
  background: linear-gradient(135deg, #4a90e2, #357abd);
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
}

.tab.active::before {
  display: none;
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

.recommend-content, .plan-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

h2 {
  color: #333;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  position: relative;
  padding-left: 16px;
}

h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #4a90e2, #357abd);
  border-radius: 2px;
}

.exercises-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.exercise-item {
  padding: 24px;
  border-radius: 12px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.exercise-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #4a90e2, #357abd);
}

.exercise-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.exercise-header h3 {
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.difficulty {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.difficulty.easy {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.difficulty.medium {
  background-color: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.difficulty.hard {
  background-color: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.exercise-content {
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.exercise-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.knowledge-tag {
  padding: 6px 12px;
  background-color: #f0f5ff;
  color: #1890ff;
  border: 1px solid #d6e4ff;
  border-radius: 16px;
  font-size: 12px;
  transition: all 0.3s ease;
}

.knowledge-tag:hover {
  background-color: #e6f7ff;
  border-color: #91d5ff;
  transform: translateY(-1px);
}

.solve-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #4a90e2, #357abd);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
}

.solve-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.2);
  transition: left 0.3s ease;
}

.solve-btn:hover::before {
  left: 0;
}

.solve-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.plan-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.plan-item {
  padding: 24px;
  border-radius: 12px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.plan-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #4a90e2, #357abd);
}

.plan-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.plan-item h3 {
  color: #333;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  padding-left: 12px;
}

.plan-item p {
  color: #666;
  line-height: 1.6;
  font-size: 14px;
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.schedule {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.day-item {
  padding: 16px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.day-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.day-header {
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
  font-size: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.day-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.day-content li {
  padding: 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  position: relative;
  padding-left: 20px;
}

.day-content li::before {
  content: '•';
  color: #4a90e2;
  font-weight: bold;
  display: inline-block;
  width: 1em;
  position: absolute;
  left: 0;
  top: 8px;
}

.empty {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
  background-color: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

@media (max-width: 768px) {
  .exercises-container {
    margin: 15px;
    padding: 16px;
  }
  
  .exercise-footer {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .solve-btn {
    align-self: flex-end;
  }
}
</style>