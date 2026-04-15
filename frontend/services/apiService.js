// API 服务层，用于与后端通信

const API_PREFIX = '/api'

const getAuthToken = () => localStorage.getItem('access_token')


const getStoredUserInfo = () => {
  try {
    const raw = localStorage.getItem('user_info')
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

const persistUserInfo = (patch = {}) => {
  const current = getStoredUserInfo()
  const next = { ...current, ...patch }
  localStorage.setItem('user_info', JSON.stringify(next))
  return next
}

const buildQuery = (params = {}) => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) {
      value.forEach((v) => query.append(key, String(v)))
    } else {
      query.append(key, String(value))
    }
  })
  const str = query.toString()
  return str ? `?${str}` : ''
}

async function request(endpoint, options = {}) {
  const token = getAuthToken()
  const headers = { ...(options.headers || {}) }
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData

  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_PREFIX}${endpoint}`, {
    ...options,
    headers,
  })

  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { message: text }
    }
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || `请求失败(${response.status})`)
  }

  return data
}

export const ensureCurrentUserId = async () => {
  const userInfo = getStoredUserInfo()
  if (userInfo?.id) return Number(userInfo.id)

  const me = await request('/auth/me')
  if (!me?.id) {
    throw new Error('无法从登录态获取用户ID，请重新登录')
  }
  persistUserInfo({
    id: me.id,
    username: me.username,
    name: userInfo.name || me.username,
    avatar: userInfo.avatar || '👤',
  })
  return Number(me.id)
}

export const authAPI = {
  register: (userData) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),

  login: (credentials) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  getCurrentUser: () => request('/auth/me'),
}

export const profileAPI = {
  getProfile: async (userId) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/profile/${buildQuery({ user_id: id })}`)
  },
}

export const exercisesAPI = {
  getRecommendations: async ({ userId, limit = 5, algorithmVersion } = {}) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/exercises/recommend${buildQuery({ user_id: id, limit, algorithm_version: algorithmVersion })}`)
  },

  submitRecommendedAnswer: async ({
    userId,
    questionId,
    answer,
    isCorrect,
    algorithmVersion,
    recommendationSessionId,
  }) => {
    const id = userId || (await ensureCurrentUserId())
    return request(
      `/records/recommended/${questionId}/submit${buildQuery({
        user_id: id,
        answer,
        is_correct: isCorrect,
        algorithm_version: algorithmVersion,
        recommendation_session_id: recommendationSessionId,
      })}`,
      { method: 'POST' }
    )
  },

  getMasteryDashboard: async ({ userId, trendLimit = 30 } = {}) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/exercises/mastery/dashboard${buildQuery({ user_id: id, trend_limit: trendLimit })}`)
  },

  getAbTestStats: ({ algorithmVersion, limit = 1000 }) =>
    request(`/exercises/ab-test/stats${buildQuery({ algorithm_version: algorithmVersion, limit })}`),
}

export const learningToolsAPI = {
  getMistakes: async ({ userId, mastered, onlyDue, knowledgePoint, days, limit = 100 } = {}) => {
    const id = userId || (await ensureCurrentUserId())
    return request(
      `/learning-tools/mistakes${buildQuery({
        user_id: id,
        mastered,
        only_due: onlyDue,
        knowledge_point: knowledgePoint,
        days,
        limit,
      })}`
    )
  },

  getReviewReminders: async ({ userId, windowDays = 3 } = {}) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/learning-tools/mistakes/review-reminders${buildQuery({ user_id: id, window_days: windowDays })}`)
  },

  getFavorites: async ({ userId, folderName, limit = 50 } = {}) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/learning-tools/favorites${buildQuery({ user_id: id, folder_name: folderName, limit })}`)
  },

  addFavorite: async ({ userId, questionId, folderName = '默认收藏夹', note, tags = [] }) => {
    const id = userId || (await ensureCurrentUserId())
    return request(
      `/learning-tools/favorites${buildQuery({
        user_id: id,
        question_id: questionId,
        folder_name: folderName,
        note,
        tags,
      })}`,
      { method: 'POST' }
    )
  },

  removeFavorite: async ({ userId, favoriteId }) => {
    const id = userId || (await ensureCurrentUserId())
    return request(`/learning-tools/favorites/${favoriteId}${buildQuery({ user_id: id })}`, { method: 'DELETE' })
  },
}

export const advisorAPI = {
  /** 初始化/重建画像（首次使用或强制重建 Redis 缓存） */
  initProfile: () => request('/advisor/init'),

  /** 获取 Advisor 推荐题目 */
  getRecommendations: ({ limit = 5 } = {}) =>
    request(`/advisor/recommend${buildQuery({ limit })}`),

  /** 提交答题反馈（更新画像 + Redis） */
  submitFeedback: ({ questionId, isCorrect, hintCount = 0, timeSpent, skipReason, algorithmVersion = 'advisor-v1', recommendationSessionId } = {}) =>
    request('/advisor/feedback', {
      method: 'POST',
      body: JSON.stringify({
        question_id: questionId,
        is_correct: isCorrect,
        hint_count: hintCount,
        time_spent: timeSpent ?? null,
        skip_reason: skipReason ?? null,
        algorithm_version: algorithmVersion,
        recommendation_session_id: recommendationSessionId ?? null,
      }),
    }),

  /** 获取带缓存的快速画像 */
  getProfile: () => request('/advisor/profile'),

  /** Redis 健康检查 */
  redisHealth: () => request('/advisor/redis/health'),
}

export const chatAPI = {
  /** 大模型批改大题（非流式） */
  gradeAnswer: ({ questionContent, standardAnswer, userAnswer, knowledgePoints } = {}) =>
    request('/chat/grade-answer', {
      method: 'POST',
      body: JSON.stringify({
        question_content: questionContent,
        standard_answer: standardAnswer ?? null,
        user_answer: userAnswer,
        knowledge_points: knowledgePoints ?? [],
      }),
    }),

  /** 答错后诊断：AI 指出问题所在和正确思路 */
  diagnose: ({ questionContent, standardAnswer, userAnswer, knowledgePoints } = {}) =>
    request('/chat/diagnose', {
      method: 'POST',
      body: JSON.stringify({
        question_content: questionContent,
        standard_answer: standardAnswer ?? null,
        user_answer: userAnswer,
        knowledge_points: knowledgePoints ?? [],
      }),
    }),
}

export default {
  auth: authAPI,
  profile: profileAPI,
  exercises: exercisesAPI,
  learningTools: learningToolsAPI,
  advisor: advisorAPI,
  chat: chatAPI,
  ensureCurrentUserId,
}
