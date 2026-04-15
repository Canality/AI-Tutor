<template>
  <div class="profile-page">
    <Navigation />
    <div class="content main-content">
      <div class="header-row">
        <h1>📊 学习画像与掌握度</h1>
        <button class="refresh-btn" :disabled="loading" @click="loadAll">
          {{ loading ? '加载中...' : '刷新数据' }}
        </button>
      </div>

      <p class="sub">用户ID：{{ userId || '-' }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <section class="card">
        <h2>能力曲线（最近记录）</h2>
        <div v-if="dashboard.ability_curve.length === 0" class="empty">暂无能力曲线数据</div>
        <div v-else class="curve-list">
          <div v-for="(item, idx) in dashboard.ability_curve.slice(-10)" :key="idx" class="curve-item">
            <div class="curve-head">
              <span>{{ formatTime(item.time) }}</span>
              <strong>θ={{ safeNum(item.theta) }}</strong>
            </div>
            <div class="curve-ci">CI: [{{ safeNum(item.theta_ci_lower) }}, {{ safeNum(item.theta_ci_upper) }}]</div>
          </div>
        </div>
      </section>

      <section class="grid-two">
        <div class="card">
          <h2>掌握度雷达维度（Top）</h2>
          <div v-if="dashboard.radar_dimensions.length === 0" class="empty">暂无掌握度数据</div>
          <div v-else>
            <div v-for="item in dashboard.radar_dimensions" :key="item.knowledge_point" class="progress-row">
              <div class="label">{{ item.knowledge_point }}</div>
              <div class="bar-wrap">
                <div class="bar" :class="item.color" :style="{ width: `${Math.round((item.mastery || 0) * 100)}%` }"></div>
              </div>
              <div class="value">{{ Math.round((item.mastery || 0) * 100) }}%</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h2>错题分布（按知识点）</h2>
          <div v-if="distributionList.length === 0" class="empty">暂无错题分布数据</div>
          <div v-else>
            <div v-for="item in distributionList" :key="item.kp" class="distribution-row">
              <span>{{ item.kp }}</span>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-two">
        <div class="card">
          <h2>A/B 统计（Control）</h2>
          <div v-if="abStats.control" class="stats">
            <div>记录数：{{ abStats.control.total_records }}</div>
            <div>正确率：{{ pct(abStats.control.accuracy) }}</div>
            <div>平均难度：{{ safeNum(abStats.control.avg_difficulty) }}</div>
            <div>平均耗时：{{ safeNum(abStats.control.avg_time_spent) }}s</div>
          </div>
          <div v-else class="empty">暂无数据</div>
        </div>

        <div class="card">
          <h2>A/B 统计（Treatment）</h2>
          <div v-if="abStats.treatment" class="stats">
            <div>记录数：{{ abStats.treatment.total_records }}</div>
            <div>正确率：{{ pct(abStats.treatment.accuracy) }}</div>
            <div>平均难度：{{ safeNum(abStats.treatment.avg_difficulty) }}</div>
            <div>平均耗时：{{ safeNum(abStats.treatment.avg_time_spent) }}s</div>
          </div>
          <div v-else class="empty">暂无数据</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Navigation from '../components/Navigation.vue'
import { ensureCurrentUserId, exercisesAPI } from '../services/apiService'

const loading = ref(false)
const error = ref('')
const userId = ref(null)

const dashboard = ref({
  radar_dimensions: [],
  ability_curve: [],
  mistake_distribution: {},
})

const abStats = ref({
  control: null,
  treatment: null,
})

const distributionList = computed(() => {
  const raw = dashboard.value?.mistake_distribution || {}
  return Object.entries(raw)
    .map(([kp, count]) => ({ kp, count: Number(count) || 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 12)
})

const safeNum = (v) => (typeof v === 'number' ? v.toFixed(2) : '-')
const pct = (v) => (typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : '-')
const formatTime = (t) => (t ? new Date(t).toLocaleString() : '-')

const loadAll = async () => {
  loading.value = true
  error.value = ''
  try {
    userId.value = await ensureCurrentUserId()

    const [dashboardRes, controlRes, treatmentRes] = await Promise.all([
      exercisesAPI.getMasteryDashboard({ userId: userId.value, trendLimit: 30 }),
      exercisesAPI.getAbTestStats({ algorithmVersion: 'control', limit: 1000 }),
      exercisesAPI.getAbTestStats({ algorithmVersion: 'treatment', limit: 1000 }),
    ])

    dashboard.value = dashboardRes?.data || dashboard.value
    abStats.value = {
      control: controlRes?.data || null,
      treatment: treatmentRes?.data || null,
    }
  } catch (e) {
    error.value = e?.message || '加载学习画像失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.profile-page { min-height: 100vh; background: #f5f7fb; margin-left: 250px; }
.content { padding: 28px; max-width: 1100px; margin: 0 auto; }
.header-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.sub { color: #666; margin-bottom: 12px; }
.error { color: #d93025; margin-bottom: 12px; }
.refresh-btn { border: none; background: #1d4ed8; color: #fff; padding: 8px 14px; border-radius: 8px; cursor: pointer; }
.refresh-btn:disabled { opacity: .65; cursor: not-allowed; }
.card { background: #fff; border: 1px solid #e9edf2; border-radius: 14px; padding: 16px; margin-bottom: 16px; }
.card h2 { font-size: 16px; margin-bottom: 12px; }
.empty { color: #888; font-size: 14px; }
.grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.curve-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.curve-item { border: 1px solid #eef1f5; border-radius: 10px; padding: 10px; }
.curve-head { display: flex; justify-content: space-between; font-size: 13px; color: #444; }
.curve-ci { font-size: 12px; color: #6b7280; margin-top: 4px; }
.progress-row { display: grid; grid-template-columns: 160px 1fr 64px; gap: 10px; align-items: center; margin-bottom: 10px; }
.label { font-size: 13px; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-wrap { height: 10px; border-radius: 999px; background: #edf1f5; overflow: hidden; }
.bar { height: 100%; border-radius: 999px; }
.bar.green { background: #16a34a; }
.bar.yellow { background: #f59e0b; }
.bar.red { background: #ef4444; }
.value { text-align: right; font-size: 12px; color: #6b7280; }
.distribution-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #eef1f5; font-size: 13px; }
.stats { display: grid; gap: 8px; color: #374151; font-size: 14px; }

@media (max-width: 900px) {
  .profile-page { margin-left: 0; }
  .grid-two { grid-template-columns: 1fr; }
  .curve-list { grid-template-columns: 1fr; }
  .progress-row { grid-template-columns: 1fr; }
}
</style>
