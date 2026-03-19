<template>
  <div class="login-container">
    <div class="login-card">
      <h1>AI Tutor 登录</h1>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label>用户名</label>
          <input 
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            class="form-input"
          />
        </div>
        
        <div class="form-item">
          <label>密码</label>
          <input 
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            class="form-input"
          />
        </div>
        
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      
      <p class="register-link">
        还没有账号？<router-link to="/register">去注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/apiService'

// 创建响应式数据
const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const router = useRouter()

// 登录处理函数
const handleLogin = async () => {
  console.log('登录信息：', form.username, form.password)
  
  if (!form.username || !form.password) {
    alert('请填写完整信息！')
    return
  }
  
  try {
    loading.value = true
    const response = await authAPI.login({
      username: form.username,
      password: form.password
    })
    
    // 保存 token 到本地存储
    localStorage.setItem('token', response.access_token)
    
    alert('登录成功！')
    router.push('/ai-tutor')
  } catch (error) {
    alert('登录失败：' + (error.message || '请检查用户名和密码'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.login-card {
  max-width: 420px;
  width: 100%;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.login-card::before {
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
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 700;
  position: relative;
  padding-bottom: 15px;
}

h1::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #4a90e2, #357abd);
  border-radius: 3px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  transition: color 0.3s ease;
}

.form-input {
  padding: 14px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  outline: none;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.form-input:focus {
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #999;
  transition: color 0.3s ease;
}

.form-input:focus::placeholder {
  color: #ccc;
}

.login-btn {
  padding: 14px;
  background: linear-gradient(135deg, #4a90e2, #357abd);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
  margin-top: 10px;
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.2);
  transition: left 0.3s ease;
}

.login-btn:hover::before {
  left: 0;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.login-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-btn:disabled::before {
  display: none;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #666;
}

.register-link router-link {
  color: #4a90e2;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.register-link router-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background-color: #4a90e2;
  transition: width 0.3s ease;
}

.register-link router-link:hover::after {
  width: 100%;
}

.register-link router-link:hover {
  color: #357abd;
}

@media (max-width: 768px) {
  .login-card {
    padding: 30px 20px;
  }
  
  h1 {
    font-size: 20px;
  }
}
</style>