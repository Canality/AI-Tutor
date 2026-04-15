<!-- src/pages/RecommendView.vue -->
<template>
  <div class="recommend-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="user-section" @click="showEditProfile = true">
        <div class="user-avatar-large">
          <img v-if="isImageAvatar(userInfo.avatar)" :src="userInfo.avatar" class="avatar-img" />
          <span v-else>{{ userInfo.avatar }}</span>
        </div>
        <div class="user-info" v-show="!isSidebarCollapsed">
          <span class="user-name">{{ userInfo.name }}</span>
          <span class="user-level">θ={{ profileSnap.theta ?? '-' }} · 掌握度{{ pct(profileSnap.avg_mastery) }}</span>
        </div>
      </div>

      <button class="toggle-btn" @click.stop="toggleSidebar">
        {{ isSidebarCollapsed ? '→' : '←' }}
      </button>

      <div class="quick-nav" v-show="!isSidebarCollapsed">
        <router-link to="/ai-tutor" class="nav-item">
          <span class="nav-icon">💬</span><span>AI 提问</span>
        </router-link>
        <router-link to="/recommend" class="nav-item active">
          <span class="nav-icon">✨</span><span>智能推荐</span>
        </router-link>
        <router-link to="/exercises" class="nav-item">
          <span class="nav-icon">📝</span><span>练习中心</span>
        </router-link>
        <router-link to="/profile" class="nav-item">
          <span class="nav-icon">📊</span><span>学习画像</span>
        </router-link>
      </div>

      <div class="sidebar-footer" v-show="!isSidebarCollapsed">
        <button class="logout-btn" @click="logout">
          <span>🚪</span><span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="main-content">
      <div class="mobile-header">
        <button class="mobile-menu-btn" @click="toggleSidebar">☰</button>
        <span class="mobile-title">智能推荐</span>
      </div>

      <div class="recommend-container">
        <!-- 页头 -->
        <div class="page-header">
          <div class="header-left">
            <h1>✨ 个性化推荐</h1>
            <p>基于你的学习画像，AI 为你精心挑选最合适的题目</p>
          </div>
          <div class="header-right">
            <div v-if="redisOk !== null" class="redis-badge" :class="redisOk ? 'online' : 'offline'">
              {{ redisOk ? '⚡ 实时推荐' : '📦 离线模式' }}
            </div>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="error-banner">{{ error }}</div>

        <!-- Advisor 模式 + 画像快照 -->
        <div v-if="profileSnap.theta" class="advisor-mode-card" :class="advisorModeClass">
          <div class="mode-icon">{{ modeIcon }}</div>
          <div class="mode-body">
            <div class="mode-label">{{ modeName }}</div>
            <div class="mode-reason">{{ advisorInstruction?.reasoning }}</div>
          </div>
          <div class="mode-stats">
            <span>做题 {{ profileSnap.total_questions }}</span>
            <span>薄弱 {{ (profileSnap.weak_kps || []).join('、') || '暂无' }}</span>
          </div>
        </div>

        <!-- 操作栏 -->
        <div class="action-bar">
          <select v-model="limit" class="limit-select">
            <option :value="3">3 题</option>
            <option :value="5">5 题</option>
            <option :value="8">8 题</option>
          </select>
          <button class="refresh-btn" :disabled="loading" @click="loadRecommendations">
            <span v-if="loading">推荐中…</span>
            <span v-else>🔄 换一批</span>
          </button>
        </div>

        <!-- 加载骨架屏 -->
        <div v-if="loading" class="skeleton-list">
          <div v-for="i in limit" :key="i" class="skeleton-card"></div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="recommendations.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>暂无推荐题目</p>
          <p class="empty-sub">先去 AI 提问区做几道题，系统会根据你的水平推荐合适的练习！</p>
          <button class="primary-btn" @click="initAndLoad">初始化画像并推荐</button>
        </div>

        <!-- 推荐题目列表 -->
        <div v-else class="problem-list">
          <div
            v-for="(item, index) in recommendations"
            :key="item.id"
            class="problem-card"
            :class="{ 'is-review': item.is_review, 'submitted': submittedSet.has(item.id) }"
          >
            <!-- 卡片头 -->
            <div class="card-header">
              <div class="card-num">#{{ index + 1 }}</div>
              <div class="card-badges">
                <span v-if="item.is_review" class="badge review">复习</span>
                <span class="badge difficulty" :class="diffClass(item.difficulty)">
                  难度 {{ item.difficulty }}
                </span>
                <span class="badge tone" :class="toneClass(item.tone)">{{ item.tone }}</span>
              </div>
              <div class="card-score">综合 {{ item.scores?.final_score ?? '-' }}</div>
            </div>

            <!-- 题目内容 -->
            <div class="card-content">{{ item.content }}</div>

            <!-- 知识点 -->
            <div class="card-kps">
              <span v-for="kp in (item.knowledge_points || [])" :key="kp" class="kp-tag">{{ kp }}</span>
            </div>

            <!-- 推荐理由 -->
            <div class="card-reason">💡 {{ item.recommendation_reason }}</div>

            <!-- 答案输入 + 操作按钮 -->
            <div class="card-actions" v-if="!submittedSet.has(item.id)">
              <input
                v-model="answerMap[item.id]"
                class="answer-input"
                placeholder="输入思路或答案（可选）"
                @keyup.enter="submitAnswer(item, true)"
              />
              <div class="btn-group">
                <button class="act-btn correct" @click="submitAnswer(item, true)">✔ 答对了</button>
                <button class="act-btn wrong" @click="submitAnswer(item, false)">✘ 答错了</button>
                <button class="act-btn skip-easy" @click="skipQuestion(item, 'too_easy')">⏩ 太简单</button>
                <button class="act-btn skip-hard" @click="skipQuestion(item, 'too_hard')">⏭ 太难了</button>
              </div>
            </div>

            <!-- 已提交状态 -->
            <div class="submitted-badge" v-else>
              <span>{{ submittedResults[item.id] }}</span>
            </div>
          </div>
        </div>

        <!-- 全部完成提示 -->
        <div v-if="!loading && recommendations.length > 0 && submittedSet.size === recommendations.length" class="all-done">
          <p>🎉 这批题目全部完成！</p>
          <button class="primary-btn" @click="loadRecommendations">继续推荐下一批</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { advisorAPI } from '../services/apiService'

const router = useRouter()

// 侧边栏
const isSidebarCollapsed = ref(false)
const toggleSidebar = () => { isSidebarCollapsed.value = !isSidebarCollapsed.value }

// 用户信息
const userInfo = reactive({ name: '学习者', avatar: '👤' })
const loadUserInfo = () => {
  try {
    const saved = localStorage.getItem('user_info')
    if (saved) {
      const d = JSON.parse(saved)
      userInfo.name = d.username || d.name || '学习者'
      if (d.avatar) userInfo.avatar = d.avatar
    }
  } catch {}
}
const isImageAvatar = (a) => a && (a.startsWith('data:') || a.startsWith('blob:') || a.startsWith('http'))
const logout = () => { if (confirm('确定要退出登录吗？')) router.push('/') }

// 状态
const loading = ref(false)
const error = ref('')
const redisOk = ref(null)
const limit = ref(5)

const recommendations = ref([])
const answerMap = reactive({})
const submittedSet = ref(new Set())
const submittedResults = reactive({})

const profileSnap = reactive({
  theta: null,
  avg_mastery: null,
  weak_kps: [],
  total_questions: 0,
})
const advisorMode = ref('')
const advisorInstruction = ref(null)

// 计算属性
const advisorModeClass = computed(() => ({
  'mode-scaffold': advisorMode.value === 'MODE_SCAFFOLD',
  'mode-challenge': advisorMode.value === 'MODE_CHALLENGE',
  'mode-encourage': advisorMode.value === 'MODE_ENCOURAGE',
}))
const modeIcon = computed(() => ({
  MODE_SCAFFOLD: '🔧',
  MODE_CHALLENGE: '🚀',
  MODE_ENCOURAGE: '💪',
}[advisorMode.value] || '🤖'))
const modeName = computed(() => ({
  MODE_SCAFFOLD: '脚手架模式 — 分步引导',
  MODE_CHALLENGE: '挑战模式 — 自主探索',
  MODE_ENCOURAGE: '鼓励模式 — 适度引导',
}[advisorMode.value] || '智能模式'))

const pct = (v) => v != null ? (v * 100).toFixed(0) + '%' : '-'
const diffClass = (d) => d <= 1 ? 'easy' : d <= 2 ? 'medium' : d <= 3 ? 'hard' : 'expert'
const toneClass = (t) => ({ '鼓励型': 'encourage', '激励型': 'motivate', '中性': 'neutral' }[t] || 'neutral')

// 检查 Redis
const checkRedis = async () => {
  try {
    const res = await advisorAPI.redisHealth()
    redisOk.value = res?.redis_available ?? false
  } catch {
    redisOk.value = false
  }
}

// 加载推荐
const loadRecommendations = async () => {
  loading.value = true
  error.value = ''
  submittedSet.value = new Set()
  try {
    const res = await advisorAPI.getRecommendations({ limit: limit.value })
    const data = res?.data || {}
    recommendations.value = data.recommendations || []
    advisorMode.value = data.advisor_mode || ''
    advisorInstruction.value = data.advisor_instruction || null
    const snap = data.profile_snapshot || {}
    Object.assign(profileSnap, snap)
  } catch (e) {
    error.value = e?.message || '获取推荐失败，请重试'
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

// 初始化画像再推荐
const initAndLoad = async () => {
  loading.value = true
  error.value = ''
  try {
    await advisorAPI.initProfile()
    await loadRecommendations()
  } catch (e) {
    error.value = e?.message || '初始化失败'
    loading.value = false
  }
}

// 提交答案
const submitAnswer = async (item, isCorrect) => {
  try {
    const startTs = Date.now()
    const res = await advisorAPI.submitFeedback({
      questionId: item.id,
      isCorrect,
      hintCount: 0,
      timeSpent: Math.round((Date.now() - startTs) / 1000),
      algorithmVersion: 'advisor-v1',
      recommendationSessionId: `web-${Date.now()}`,
    })
    submittedSet.value = new Set([...submittedSet.value, item.id])
    const action = res?.data?.advisor_action || ''
    const label = isCorrect ? '✅ 答对' : '❌ 答错'
    const actionMsg = action === 'escalate' ? ' · 准备升级难度' : action === 'deescalate' ? ' · 准备降低难度' : ''
    submittedResults[item.id] = label + actionMsg

    // 若全部完成，顺手刷新画像快照
    if (submittedSet.value.size === recommendations.value.length) {
      try {
        const prof = await advisorAPI.getProfile()
        const snap = prof?.data || {}
        Object.assign(profileSnap, {
          theta: snap.theta,
          avg_mastery: snap.avg_mastery,
          weak_kps: Object.entries(snap.knowledge_mastery || {})
            .sort((a, b) => a[1] - b[1]).slice(0, 3).map(e => e[0]),
          total_questions: snap.total_questions,
        })
      } catch {}
    }
  } catch (e) {
    alert(e?.message || '提交失败，请重试')
  }
}

// 跳过
const skipQuestion = async (item, skipReason) => {
  try {
    const res = await advisorAPI.submitFeedback({
      questionId: item.id,
      isCorrect: skipReason === 'too_easy',
      skipReason,
      algorithmVersion: 'advisor-v1',
    })
    submittedSet.value = new Set([...submittedSet.value, item.id])
    const label = skipReason === 'too_easy' ? '⏩ 太简单，已跳过' : '⏭ 太难了，已记录'
    submittedResults[item.id] = label
  } catch (e) {
    alert(e?.message || '跳过提交失败')
  }
}

onMounted(async () => {
  loadUserInfo()
  await checkRedis()
  await loadRecommendations()
})
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.recommend-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: #f5f5f7;
  position: fixed;
  top: 0; left: 0;
}

/* ====== 侧边栏 ====== */
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background: #fff;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  position: relative;
  transition: all 0.3s ease;
  overflow: hidden;
}
.recommend-page.sidebar-collapsed .sidebar { width: 60px; min-width: 60px; padding: 20px 8px; }
.user-section { display: flex; align-items: center; gap: 12px; padding: 12px; margin-bottom: 16px; border-radius: 12px; cursor: pointer; transition: 0.2s; }
.user-section:hover { background: #f0f0f0; }
.user-avatar-large { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg,#667eea,#764ba2); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; overflow: hidden; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.user-info { display: flex; flex-direction: column; overflow: hidden; flex: 1; }
.user-name { font-size: 14px; font-weight: 600; color: #1d1d1f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-level { font-size: 11px; color: #007aff; margin-top: 2px; }
.toggle-btn { position: absolute; right: -12px; top: 80px; width: 24px; height: 24px; border-radius: 50%; background: white; border: 1px solid #e0e0e0; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #666; box-shadow: 0 2px 8px rgba(0,0,0,.1); z-index: 10; }
.quick-nav { margin-bottom: 16px; border-bottom: 1px solid #e5e5e5; padding-bottom: 16px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 8px; text-decoration: none; color: #666; font-size: 14px; transition: 0.2s; margin-bottom: 4px; }
.nav-item:hover { background: #f0f0f0; color: #1d1d1f; }
.nav-item.active { background: #e8e8e8; color: #1d1d1f; font-weight: 600; }
.nav-icon { font-size: 18px; }
.sidebar-footer { margin-top: auto; padding-top: 16px; border-top: 1px solid #e5e5e5; }
.logout-btn { width: 100%; display: flex; align-items: center; gap: 8px; padding: 10px; border: none; background: transparent; color: #666; font-size: 14px; cursor: pointer; border-radius: 8px; transition: 0.2s; }
.logout-btn:hover { background: #ffebee; color: #c62828; }

/* ====== 主内容 ====== */
.main-content { flex: 1; height: 100%; overflow-y: auto; background: #f5f5f7; }
.mobile-header { display: none; padding: 12px 16px; border-bottom: 1px solid #e5e5e5; background: white; align-items: center; gap: 12px; }
.mobile-menu-btn { background: none; border: none; font-size: 20px; cursor: pointer; padding: 4px; }
.mobile-title { font-size: 16px; font-weight: 600; flex: 1; text-align: center; }

.recommend-container { max-width: 860px; margin: 0 auto; padding: 32px 20px 60px; }

/* ====== 页头 ====== */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h1 { font-size: 26px; font-weight: 700; color: #1d1d1f; margin-bottom: 6px; }
.page-header p { font-size: 14px; color: #86868b; }
.redis-badge { padding: 6px 14px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.redis-badge.online { background: #e6f4ea; color: #137333; }
.redis-badge.offline { background: #fce8e6; color: #c5221f; }

/* ====== 错误 ====== */
.error-banner { background: #fff0f0; border: 1px solid #ffcdd2; color: #b71c1c; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; font-size: 14px; }

/* ====== Advisor 模式 ====== */
.advisor-mode-card { display: flex; align-items: center; gap: 16px; padding: 16px 20px; border-radius: 14px; margin-bottom: 20px; border: 1.5px solid transparent; }
.advisor-mode-card.mode-scaffold { background: #fff8e1; border-color: #ffc107; }
.advisor-mode-card.mode-challenge { background: #e8f5e9; border-color: #4caf50; }
.advisor-mode-card.mode-encourage { background: #e3f2fd; border-color: #2196f3; }
.mode-icon { font-size: 28px; flex-shrink: 0; }
.mode-body { flex: 1; }
.mode-label { font-size: 15px; font-weight: 700; color: #1d1d1f; margin-bottom: 4px; }
.mode-reason { font-size: 13px; color: #555; line-height: 1.5; }
.mode-stats { display: flex; flex-direction: column; gap: 4px; text-align: right; font-size: 12px; color: #666; flex-shrink: 0; }

/* ====== 操作栏 ====== */
.action-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; }
.limit-select { border: 1px solid #d0d7e2; border-radius: 8px; padding: 8px 12px; font-size: 13px; cursor: pointer; background: white; }
.refresh-btn { padding: 8px 20px; border: none; border-radius: 10px; background: #0071e3; color: white; font-size: 14px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.refresh-btn:disabled { background: #aac7f0; cursor: not-allowed; }
.refresh-btn:hover:not(:disabled) { background: #005bb5; }

/* ====== 骨架屏 ====== */
.skeleton-list { display: flex; flex-direction: column; gap: 16px; }
.skeleton-card { height: 180px; background: linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%); background-size: 200% 100%; border-radius: 16px; animation: shimmer 1.4s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { font-size: 16px; color: #555; margin-bottom: 8px; }
.empty-sub { font-size: 14px; color: #999; margin-bottom: 24px; }
.primary-btn { padding: 12px 28px; background: #0071e3; color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.primary-btn:hover { background: #005bb5; }

/* ====== 题目卡片 ====== */
.problem-list { display: flex; flex-direction: column; gap: 16px; }
.problem-card { background: white; border-radius: 18px; padding: 22px; border: 1.5px solid #e5e5e5; transition: 0.25s; }
.problem-card:hover { border-color: #0071e3; box-shadow: 0 4px 20px rgba(0,113,227,.1); }
.problem-card.is-review { border-color: #ff9800; background: #fffdf5; }
.problem-card.submitted { opacity: 0.72; }

.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.card-num { width: 32px; height: 32px; background: #f0f7ff; color: #0071e3; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.card-badges { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.badge { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.badge.review { background: #fff3e0; color: #e65100; }
.badge.difficulty.easy { background: #e8f5e9; color: #2e7d32; }
.badge.difficulty.medium { background: #e3f2fd; color: #1565c0; }
.badge.difficulty.hard { background: #fff8e1; color: #f57f17; }
.badge.difficulty.expert { background: #fce4ec; color: #ad1457; }
.badge.tone.encourage { background: #e8f5e9; color: #2e7d32; }
.badge.tone.motivate { background: #e3f2fd; color: #1565c0; }
.badge.tone.neutral { background: #f3f4f6; color: #555; }
.card-score { font-size: 12px; color: #aaa; flex-shrink: 0; }

.card-content { font-size: 15px; color: #1d1d1f; line-height: 1.7; margin-bottom: 12px; word-break: break-word; }
.card-kps { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.kp-tag { padding: 3px 9px; background: #f5f5f7; border-radius: 6px; font-size: 12px; color: #555; }
.card-reason { font-size: 13px; color: #0071e3; background: #f0f7ff; padding: 8px 12px; border-radius: 8px; margin-bottom: 14px; line-height: 1.6; }

.card-actions { display: flex; flex-direction: column; gap: 10px; }
.answer-input { width: 100%; padding: 10px 14px; border: 1px solid #d0d7e2; border-radius: 10px; font-size: 14px; outline: none; transition: 0.2s; }
.answer-input:focus { border-color: #0071e3; box-shadow: 0 0 0 3px rgba(0,113,227,.15); }
.btn-group { display: flex; flex-wrap: wrap; gap: 8px; }
.act-btn { padding: 8px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.act-btn.correct { background: #e8f5e9; color: #2e7d32; }
.act-btn.correct:hover { background: #c8e6c9; }
.act-btn.wrong { background: #fce4ec; color: #ad1457; }
.act-btn.wrong:hover { background: #f8bbd0; }
.act-btn.skip-easy { background: #e8eaf6; color: #3949ab; }
.act-btn.skip-easy:hover { background: #c5cae9; }
.act-btn.skip-hard { background: #f3e5f5; color: #6a1b9a; }
.act-btn.skip-hard:hover { background: #e1bee7; }

.submitted-badge { padding: 10px 14px; background: #f0f0f0; border-radius: 10px; font-size: 14px; font-weight: 600; color: #555; text-align: center; }

/* ====== 全部完成 ====== */
.all-done { text-align: center; padding: 32px; background: white; border-radius: 16px; border: 1.5px dashed #0071e3; margin-top: 20px; }
.all-done p { font-size: 18px; font-weight: 700; color: #0071e3; margin-bottom: 16px; }

/* ====== 响应式 ====== */
@media (max-width: 1024px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 100; box-shadow: 2px 0 8px rgba(0,0,0,.1); }
  .recommend-page.sidebar-collapsed .sidebar { transform: translateX(-100%); }
  .mobile-header { display: flex; }
}
@media (max-width: 640px) {
  .btn-group { flex-direction: column; }
  .act-btn { text-align: center; }
  .advisor-mode-card { flex-direction: column; align-items: flex-start; }
  .mode-stats { text-align: left; }
}
</style>
