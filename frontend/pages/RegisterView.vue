<template>
  <div class="register-page">
    <div class="split-container">
      <!-- 左侧品牌区 -->
      <div class="brand-side">
        <div class="brand-content">
          <div class="brand-icon">🎓</div>
          <h1 class="brand-title">AI Tutor</h1>
          <p class="brand-slogan">开启你的智能学习之旅</p>
          <p class="brand-sub">注册账号，获取个性化辅导</p>
          <div class="brand-features">
            <span>智能解析</span>
            <span>•</span>
            <span>个性推荐</span>
            <span>•</span>
            <span>学习追踪</span>
          </div>
        </div>
      </div>
      
      <!-- 右侧表单区 -->
      <div class="form-side">
        <div class="register-card">
          <div class="card-header">
            <div class="logo-icon">🚀</div>
            <h2>创建账号</h2>
            <p>填写以下信息完成注册</p>
          </div>
          
          <form @submit.prevent="handleRegister">
            <div class="input-group">
              <label>用户名</label>
              <input 
                v-model="form.username" 
                type="text" 
                placeholder="请输入用户名（至少3位）"
                required
                minlength="3"
              />
            </div>
            
            <div class="input-group">
              <label>密码</label>
              <input 
                v-model="form.password" 
                type="password" 
                placeholder="请输入密码（至少6位）"
                required
                minlength="6"
              />
            </div>
            
            <div class="input-group">
              <label>确认密码</label>
              <input 
                v-model="form.confirmPassword" 
                type="password" 
                placeholder="请再次输入密码"
                required
              />
            </div>
            
            <div v-if="errorMsg" class="error-msg">
              ⚠️ {{ errorMsg }}
            </div>
            
            <button type="submit" class="register-btn" :disabled="isLoading">
              {{ isLoading ? '注册中...' : '立即注册' }}
            </button>
          </form>
          
          <div class="divider">
            <span>已有账号？</span>
          </div>
          
          <router-link to="/login" class="login-link">
            直接登录 →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  errorMsg.value = ''
  
  if (!form.username || !form.password) {
    errorMsg.value = '请填写完整信息'
    return
  }
  
  if (form.password !== form.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
  
  if (form.password.length < 6) {
    errorMsg.value = '密码长度至少6位'
    return
  }
  
  isLoading.value = true
  
  try {
    console.log('开始注册请求...')
    
    const registerRes = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: form.username,
        password: form.password
      })
    })
    
    console.log('注册响应状态:', registerRes.status)
    
    // 安全获取响应文本（防止空响应导致 JSON 解析失败）
    const responseText = await registerRes.text()
    console.log('响应内容:', responseText || '(空)')
    
    if (!registerRes.ok) {
      let errorMessage = '注册失败'
      
      // 尝试解析 JSON 错误，失败就用文本
      if (responseText) {
        try {
          const errorData = JSON.parse(responseText)
          errorMessage = errorData.detail || errorData.message || `服务器错误: ${registerRes.status}`
        } catch (e) {
          // 不是 JSON，直接用文本（可能是 HTML 错误页）
          errorMessage = responseText.substring(0, 100) || `服务器错误 (${registerRes.status})`
        }
      } else {
        errorMessage = `服务器错误 (${registerRes.status})：无响应内容，请检查后端是否正常运行`
      }
      
      throw new Error(errorMessage)
    }
    
    // 注册成功，解析用户数据
    let userData
    if (responseText) {
      try {
        userData = JSON.parse(responseText)
        console.log('注册成功:', userData)
      } catch (e) {
        console.warn('注册成功但返回非 JSON:', responseText)
        userData = { username: form.username }
      }
    } else {
      userData = { username: form.username }
    }
    
    // 自动登录（因为注册不返回 token）
    console.log('开始自动登录...')
    
    const loginRes = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: form.username,
        password: form.password
      })
    })
    
    const loginText = await loginRes.text()
    console.log('登录响应:', loginRes.status, loginText)
    
    if (!loginRes.ok) {
      let loginError = '自动登录失败'
      if (loginText) {
        try {
          const errData = JSON.parse(loginText)
          loginError = errData.detail || '自动登录失败，请手动登录'
        } catch {
          loginError = loginText.substring(0, 100)
        }
      }
      throw new Error(loginError)
    }
    
    let loginData
    try {
      loginData = JSON.parse(loginText)
    } catch {
      throw new Error('登录响应格式错误')
    }
    
    // 保存 token 和用户信息
    localStorage.setItem('access_token', loginData.access_token)
    localStorage.setItem('user_info', JSON.stringify({
      id: loginData?.user?.id,
      username: form.username,
      name: form.username,
      avatar: '👤',
      loginTime: new Date().toISOString()
    }))

    
    console.log('登录成功，准备跳转...')
    router.push('/ai-tutor')
    
  } catch (error) {
    console.error('完整错误:', error)
    errorMsg.value = error.message || '网络错误，请检查：1.后端是否启动 2.数据库是否连接'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-page {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.split-container {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  height: 100%;
  width: 100%;
  place-items: center;
}

.brand-side {
  background: linear-gradient(135deg, #1d1d1f 0%, #000000 100%);
  height: 80%;
  width: 80%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-sizing: border-box;
  border-radius: 24px;
  justify-self: start;
  margin-left: 10%;
}

.brand-content {
  text-align: center;
  color: white;
  max-width: 100%;
  width: 100%;
}

.brand-icon { 
  font-size: 80px; 
  margin-bottom: 20px; 
}

.brand-title { 
  font-size: 48px; 
  font-weight: 700; 
  margin: 0 0 15px 0; 
}

.brand-slogan { 
  font-size: 20px; 
  color: #fff; 
  margin: 0 0 8px 0; 
  font-weight: 500; 
}

.brand-sub { 
  font-size: 16px; 
  color: #86868b; 
  margin: 0 0 30px 0; 
}

.brand-features {
  display: flex;
  justify-content: center;
  gap: 15px;
  font-size: 13px;
  color: #666;
  letter-spacing: 1px;
  flex-wrap: wrap;
}

.form-side {
  background-color: #f5f5f7;
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 5%;
  box-sizing: border-box;
}

.register-card {
  width: 450px;
  max-width: 90%;
  height: auto;
  max-height: 90vh;
  background: #ffffff;
  border-radius: 24px;
  padding: 40px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.08);
  overflow-y: auto;
}

.card-header { 
  text-align: center; 
  margin-bottom: 30px; 
}

.logo-icon { 
  font-size: 48px; 
  margin-bottom: 15px; 
}

.card-header h2 { 
  font-size: 28px; 
  font-weight: 700; 
  color: #1d1d1f; 
  margin: 0 0 8px 0; 
}

.card-header p { 
  font-size: 15px; 
  color: #86868b; 
  margin: 0; 
}

.input-group { 
  margin-bottom: 20px; 
}

.input-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-group input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e1e1e1;
  border-radius: 12px;
  font-size: 15px;
  color: #1d1d1f;
  background: #fafafa;
  box-sizing: border-box;
  transition: all 0.3s;
}

.input-group input:focus { 
  outline: none; 
  border-color: #0071e3; 
  background: #fff; 
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,113,227,0.1);
}

.error-msg {
  background: #ffebee;
  color: #c62828;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  word-break: break-word;
}

.register-btn {
  width: 100%;
  padding: 16px;
  background: #1d1d1f;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 24px;
}

.register-btn:hover:not(:disabled) { 
  background: #000; 
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}

.register-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.divider {
  text-align: center;
  margin-bottom: 20px;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e5e5e5;
}

.divider span {
  position: relative;
  background: white;
  padding: 0 16px;
  color: #86868b;
  font-size: 14px;
}

.login-link {
  display: block;
  text-align: center;
  padding: 14px;
  border: 2px solid #1d1d1f;
  border-radius: 12px;
  color: #1d1d1f;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.login-link:hover {
  background: #1d1d1f;
  color: white;
}

@media (max-width: 968px) {
  .split-container { 
    grid-template-columns: 1fr; 
  }
  .brand-side { 
    display: none; 
  }
  .form-side { 
    padding: 20px; 
    justify-content: center;
  }
  .register-card { 
    width: 100%; 
    max-width: 400px; 
    padding: 30px; 
  }
}
</style>
