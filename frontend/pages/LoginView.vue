<template>
  <div class="login-container">
    <h1>AI Tutor 登录</h1>
    
    <form @submit.prevent="handleLogin">
      <div class="form-item">
        <label>用户名：</label>
        <input 
          v-model="form.username"
          type="text"
          placeholder="请输入用户名"
        />
      </div>
      
      <div class="form-item">
        <label>密码：</label>
        <input 
          v-model="form.password"
          type="password"
          placeholder="请输入密码"
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
  max-width: 400px;
  margin: 100px auto;
  padding: 40px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  background-color: white;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.form-item {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #4a90e2;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.login-btn:hover {
  background-color: #357abd;
}

.login-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

router-link {
  color: #4a90e2;
  text-decoration: none;
}
</style>