<template>
  <div class="exercises-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="user-section">
        <div class="user-avatar-large">
          <span>{{ userInfo.avatar }}</span>
        </div>
        <div class="user-info" v-show="!isSidebarCollapsed">
          <span class="user-name">{{ userInfo.name }}</span>
          <span class="user-level">练习中心</span>
        </div>
      </div>

      <button class="toggle-btn" @click.stop="toggleSidebar">
        {{ isSidebarCollapsed ? '→' : '←' }}
      </button>

      <div class="quick-nav" v-show="!isSidebarCollapsed">
        <router-link to="/ai-tutor" class="nav-item">
          <span class="nav-icon">💬</span><span>AI 提问</span>
        </router-link>
        <router-link to="/recommend" class="nav-item">
          <span class="nav-icon">✨</span><span>智能推荐</span>
        </router-link>
        <router-link to="/exercises" class="nav-item active">
          <span class="nav-icon">📝</span><span>练习中心</span>
        </router-link>
        <router-link to="/mistake-book" class="nav-item">
          <span class="nav-icon">📕</span><span>错题本</span>
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

    <div class="content main-content">
      <div class="header-row">
        <h1>📝 练习推荐 / 错题本 / 收藏夹</h1>
        <button class="refresh-btn" :disabled="loadingAny" @click="bootstrap">
          {{ loadingAny ? '加载中...' : '一键刷新' }}
        </button>
      </div>
      <p class="sub">用户ID：{{ userId || '-' }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <section class="card">
        <div class="row">
          <label>算法版本</label>
          <select v-model="algorithmVersion">
            <option value="">自动分组</option>
            <option value="control">control</option>
            <option value="treatment">treatment</option>
            <option value="v1.0">v1.0</option>
            <option value="v2.0">v2.0</option>
          </select>

          <label>推荐数量</label>
          <input v-model.number="limit" type="number" min="1" max="20" />

          <button class="btn" :disabled="loadingRecs" @click="loadRecommendations">
            {{ loadingRecs ? '推荐中...' : '获取推荐题' }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty">暂无推荐题，请先做几道题后再尝试。</div>
        <div v-else class="recommend-list">
          <div v-for="q in recommendations" :key="q.id" class="recommend-item">
            <div class="meta">#{{ q.id }} · 难度 {{ q.difficulty }} · {{ q.algorithm_version }}</div>
            <div class="content-text">{{ q.content }}</div>
            <div class="kp">知识点：{{ formatKp(q.knowledge_points) }}</div>

            <div class="score-row">
              <span>综合分：{{ q?.scores?.final_score ?? '-' }}</span>
              <span>匹配度：{{ q?.scores?.difficulty_match ?? '-' }}</span>
              <span>相关性：{{ q?.scores?.kp_relevance ?? '-' }}</span>
            </div>

            <div class="submit-row">
              <input v-model="answerMap[q.id]" placeholder="输入你的答案（可选）" />
              <button class="btn success" @click="submitResult(q, true)">标记答对并提交</button>
              <button class="btn danger" @click="submitResult(q, false)">标记答错并提交</button>
              <button class="btn ghost" @click="addFavorite(q.id)">收藏</button>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-two">
        <div class="card">
          <h2>错题本</h2>
          <div class="row compact">
            <label>仅到期</label>
            <input type="checkbox" v-model="onlyDue" />
            <button class="btn" @click="loadMistakes">刷新错题</button>
          </div>
          <div v-if="mistakes.length === 0" class="empty">暂无错题记录</div>
          <div v-else class="list">
            <div v-for="m in mistakes" :key="m.id" class="list-item">
              <div class="line1">题目#{{ m.question_id }} · 错误{{ m.error_count }}次</div>
              <div class="line2">{{ shorten(m.question_content) }}</div>
              <div class="line3">下次复习：{{ formatTime(m.next_review_at) }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h2>复习提醒</h2>
          <div class="row compact">
            <label>窗口天数</label>
            <input type="number" min="1" max="30" v-model.number="windowDays" />
            <button class="btn" @click="loadReminders">刷新提醒</button>
          </div>
          <div class="reminder-group">
            <h3>到期（{{ reminders.due.length }}）</h3>
            <div v-if="reminders.due.length === 0" class="empty">暂无</div>
            <div v-else class="list">
              <div v-for="d in reminders.due" :key="`d-${d.id}`" class="list-item">
                <div class="line1">题目#{{ d.question_id }}</div>
                <div class="line3">复习时间：{{ formatTime(d.next_review_at) }}</div>
              </div>
            </div>

            <h3>即将到期（{{ reminders.upcoming.length }}）</h3>
            <div v-if="reminders.upcoming.length === 0" class="empty">暂无</div>
            <div v-else class="list">
              <div v-for="u in reminders.upcoming" :key="`u-${u.id}`" class="list-item">
                <div class="line1">题目#{{ u.question_id }}</div>
                <div class="line3">复习时间：{{ formatTime(u.next_review_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>收藏夹</h2>
        <div class="row compact">
          <label>收藏夹名称</label>
          <input v-model="folderName" placeholder="默认收藏夹" />
          <button class="btn" @click="loadFavorites">刷新收藏</button>
        </div>
        <div v-if="favorites.length === 0" class="empty">暂无收藏</div>
        <div v-else class="list">
          <div v-for="f in favorites" :key="f.id" class="list-item">
            <div class="line1">#{{ f.question_id }} · {{ f.folder_name }}</div>
            <div class="line2">{{ shorten(f.question_content) }}</div>
            <div class="line3">标签：{{ (f.tags || []).join(', ') || '-' }}</div>
            <button class="btn mini danger" @click="removeFavorite(f.id)">删除</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ensureCurrentUserId, exercisesAPI, learningToolsAPI } from '../services/apiService'

const router = useRouter()
const isSidebarCollapsed = ref(false)
const toggleSidebar = () => { isSidebarCollapsed.value = !isSidebarCollapsed.value }
const userInfo = ref({ name: '', avatar: '👤' })

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
  router.push('/login')
}

const userId = ref(null)
const error = ref('')

const loadingRecs = ref(false)
const loadingMistakes = ref(false)
const loadingFavorites = ref(false)
const loadingReminders = ref(false)
const loadingAny = computed(() => loadingRecs.value || loadingMistakes.value || loadingFavorites.value || loadingReminders.value)

const algorithmVersion = ref('')
const limit = ref(5)
const recommendations = ref([])
const answerMap = reactive({})

const onlyDue = ref(false)
const mistakes = ref([])

const windowDays = ref(3)
const reminders = ref({ due: [], upcoming: [] })

const folderName = ref('默认收藏夹')
const favorites = ref([])

const formatKp = (kps) => (Array.isArray(kps) ? kps.join('、') : '-')
const shorten = (text) => (text ? String(text).slice(0, 90) : '-')
const formatTime = (t) => (t ? new Date(t).toLocaleString() : '-')

const loadRecommendations = async () => {
  loadingRecs.value = true
  error.value = ''
  try {
    const res = await exercisesAPI.getRecommendations({
      userId: userId.value,
      limit: limit.value,
      algorithmVersion: algorithmVersion.value || undefined,
    })
    recommendations.value = res?.data?.exercises || []
  } catch (e) {
    error.value = e?.message || '获取推荐题失败'
  } finally {
    loadingRecs.value = false
  }
}

const submitResult = async (q, isCorrect) => {
  try {
    await exercisesAPI.submitRecommendedAnswer({
      userId: userId.value,
      questionId: q.id,
      answer: answerMap[q.id] || '',
      isCorrect,
      algorithmVersion: algorithmVersion.value || undefined,
      recommendationSessionId: `web-${Date.now()}`,
    })
    await Promise.all([loadMistakes(), loadReminders()])
    alert('提交成功，已写入学习记录')
  } catch (e) {
    alert(e?.message || '提交失败')
  }
}

const loadMistakes = async () => {
  loadingMistakes.value = true
  error.value = ''
  try {
    const res = await learningToolsAPI.getMistakes({ userId: userId.value, onlyDue: onlyDue.value, limit: 100 })
    mistakes.value = res?.data?.items || []
  } catch (e) {
    error.value = e?.message || '获取错题本失败'
  } finally {
    loadingMistakes.value = false
  }
}

const loadReminders = async () => {
  loadingReminders.value = true
  error.value = ''
  try {
    const res = await learningToolsAPI.getReviewReminders({ userId: userId.value, windowDays: windowDays.value })
    reminders.value = res?.data || { due: [], upcoming: [] }
  } catch (e) {
    error.value = e?.message || '获取复习提醒失败'
  } finally {
    loadingReminders.value = false
  }
}

const loadFavorites = async () => {
  loadingFavorites.value = true
  error.value = ''
  try {
    const res = await learningToolsAPI.getFavorites({ userId: userId.value, folderName: folderName.value || undefined, limit: 100 })
    favorites.value = res?.data?.items || []
  } catch (e) {
    error.value = e?.message || '获取收藏夹失败'
  } finally {
    loadingFavorites.value = false
  }
}

const addFavorite = async (questionId) => {
  try {
    await learningToolsAPI.addFavorite({
      userId: userId.value,
      questionId,
      folderName: folderName.value || '默认收藏夹',
    })
    await loadFavorites()
    alert('已收藏')
  } catch (e) {
    alert(e?.message || '收藏失败')
  }
}

const removeFavorite = async (favoriteId) => {
  try {
    await learningToolsAPI.removeFavorite({ userId: userId.value, favoriteId })
    await loadFavorites()
  } catch (e) {
    alert(e?.message || '删除收藏失败')
  }
}

const bootstrap = async () => {
  error.value = ''
  try {
    userId.value = await ensureCurrentUserId()
    const stored = localStorage.getItem('user_info')
    if (stored) {
      const info = JSON.parse(stored)
      userInfo.value.name = info.username || info.name || '用户'
      userInfo.value.avatar = info.avatar || '👤'
    }
    await Promise.all([loadRecommendations(), loadMistakes(), loadReminders(), loadFavorites()])
  } catch (e) {
    error.value = e?.message || '初始化失败，请重新登录'
  }
}

onMounted(bootstrap)
</script>

<style scoped>
/* ===== 布局 ===== */
.exercises-page {
  display: flex;
  min-height: 100vh;
  background: #f6f8fc;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
  height: 100vh;
  background: linear-gradient(160deg, #1e3a5f 0%, #2563eb 100%);
  display: flex;
  flex-direction: column;
  padding: 20px 16px;
  z-index: 100;
  transition: width 0.3s ease;
  overflow: hidden;
}

.exercises-page.sidebar-collapsed .sidebar { width: 64px; }
.exercises-page.sidebar-collapsed .main-content { margin-left: 64px; }

.main-content { margin-left: 240px; flex: 1; transition: margin-left 0.3s ease; }

.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}

.user-avatar-large {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.user-info { display: flex; flex-direction: column; overflow: hidden; }
.user-name { color: white; font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-level { color: rgba(255,255,255,0.65); font-size: 12px; margin-top: 2px; }

.toggle-btn {
  align-self: flex-end;
  background: rgba(255,255,255,0.15);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.quick-nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: rgba(255,255,255,0.8);
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s;
  white-space: nowrap;
}

.nav-item:hover { background: rgba(255,255,255,0.15); color: white; }
.nav-item.active { background: rgba(255,255,255,0.25); color: white; font-weight: 600; }
.nav-icon { font-size: 18px; width: 24px; text-align: center; flex-shrink: 0; }

.sidebar-footer { margin-top: auto; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.15); }

.logout-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 10px;
  color: rgba(255,255,255,0.85);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}
.logout-btn:hover { background: rgba(255,255,255,0.2); }

/* ===== 内容区 ===== */
.content { max-width: 1160px; margin: 0 auto; padding: 28px; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 6px; }
.sub { color: #6b7280; margin-bottom: 12px; }
.error { color: #d93025; margin-bottom: 12px; }
.refresh-btn { border: none; background: #1d4ed8; color: white; padding: 8px 14px; border-radius: 8px; cursor: pointer; }
.card { background: #fff; border: 1px solid #e7ebf0; border-radius: 14px; padding: 16px; margin-bottom: 16px; }
.grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
.row.compact { margin-bottom: 10px; }
label { color: #475569; font-size: 13px; }
input, select { border: 1px solid #d0d7e2; border-radius: 8px; padding: 6px 8px; font-size: 13px; }
.btn { border: none; border-radius: 8px; padding: 7px 12px; background: #0f172a; color: #fff; cursor: pointer; font-size: 13px; }
.btn.success { background: #15803d; }
.btn.danger { background: #b91c1c; }
.btn.ghost { background: #334155; }
.btn.mini { padding: 4px 8px; margin-top: 8px; }
.empty { color: #888; font-size: 14px; }
.recommend-list { display: grid; gap: 10px; }
.recommend-item { border: 1px solid #edf1f5; border-radius: 10px; padding: 12px; }
.meta { color: #64748b; font-size: 12px; margin-bottom: 6px; }
.content-text { color: #0f172a; margin-bottom: 8px; line-height: 1.6; }
.kp { color: #475569; font-size: 13px; margin-bottom: 8px; }
.score-row { display: flex; flex-wrap: wrap; gap: 10px; color: #64748b; font-size: 12px; margin-bottom: 8px; }
.submit-row { display: flex; flex-wrap: wrap; gap: 8px; }
.submit-row input { flex: 1; min-width: 260px; }
.reminder-group h3 { font-size: 14px; margin: 10px 0 8px; }
.list { display: grid; gap: 8px; }
.list-item { border: 1px solid #edf1f5; border-radius: 10px; padding: 10px; }
.line1 { color: #0f172a; font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.line2, .line3 { color: #64748b; font-size: 12px; }

@media (max-width: 960px) {
  .sidebar { width: 64px; }
  .main-content { margin-left: 64px; }
  .user-info, .quick-nav span:last-child, .logout-btn span:last-child, .user-level { display: none; }
  .grid-two { grid-template-columns: 1fr; }
}
</style>
