import axios from 'axios'

// 使用相对路径，通过 Vite 代理转发到后端
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let cachedToken = null

const getOrCreateToken = async () => {
  if (cachedToken) return cachedToken
  
  try {
    // 1. 尝试注册（用 JSON，不是 FormData）
    try {
      await apiClient.post('/auth/register', {
        username: 'testuser999',
        password: 'test123456'
      })
      console.log('注册成功')
    } catch (e) {
      // 用户已存在或其他错误，忽略
      console.log('注册跳过:', e.response?.status)
    }
    
    // 2. 登录拿 token
    const res = await apiClient.post('/auth/login', {
      username: 'testuser999',
      password: 'test123456'
    })
    
    cachedToken = res.data.access_token
    console.log('拿到token:', cachedToken)
    return cachedToken
  } catch (e) {
    console.error('获取token失败:', e)
    return null
  }
}

export const sendQuestion = async (question, imageBase64 = null, onChunk = null) => {
  const token = await getOrCreateToken()
  
  if (!token) {
    console.error('没有token，无法请求')
    return { answer: '登录失败，请刷新重试' }
  }
  
  // 创建 FormData（用于文件上传）
  const formData = new FormData()
  formData.append('question', question || '')
  
  if (imageBase64) {
    const arr = imageBase64.split(',')
    const mime = arr[0].match(/:(.*?);/)[1]
    const bstr = atob(arr[1])
    const u8arr = new Uint8Array(bstr.length)
    for (let i = 0; i < bstr.length; i++) u8arr[i] = bstr.charCodeAt(i)
    formData.append('image', new File([u8arr], 'upload.png', { type: mime }))
  }

  // ✅ 关键：不要设置 Content-Type，让浏览器自动处理 multipart/form-data
  const response = await fetch('/api/chat/ask-stream', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`
      // 注意：不要加 'Content-Type': 'multipart/form-data'
      // 浏览器会自动设置，并加上 boundary
    },
    body: formData
  })

  if (!response.ok) {
    console.error('请求失败:', response.status)
    return { answer: `请求失败: ${response.status}` }
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let fullText = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value)
    const lines = chunk.split('\n\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const text = line.slice(6)
        if (text !== '[DONE]') {
          fullText += text
          if (onChunk) onChunk(text, fullText)
        }
      }
    }
  }
  return { answer: fullText }
}
