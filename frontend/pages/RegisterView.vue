<template>
  <div class="register-container">
    <h1>注册账号</h1>
    
    <form @submit.prevent="handleRegister">
      <div class="form-item">
        <label>用户名：</label>
        <input 
          v-model="form.username"
          type="text"
          placeholder="设置用户名"
        />
      </div>
      
      <div class="form-item">
        <label>密码：</label>
        <input 
          v-model="form.password"
          type="password"
          placeholder="设置密码"
        />
      </div>
      
      <div class="form-item">
        <label>确认密码：</label>
        <input 
          v-model="form.confirmPassword"
          type="password"
          placeholder="再次输入密码"
        />
      </div>
      
      <button type="submit" class="register-btn" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
    </form>
    
    <p class="login-link">
      已有账号？<router-link to="/">去登录</router-link>
    </p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/apiService'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const router = useRouter()

const handleRegister = async () => {
  if (form.password !== form.confirmPassword) {
    alert('两次输入的密码不一致！')
    return
  }
  
  if (!form.username || !form.password) {
    alert('请填写完整信息！')
    return
  }
  
  try {
    loading.value = true
    await authAPI.register({
      username: form.username,
      password: form.password
    })
    
    alert('注册成功！请登录')
    router.push('/')
  } catch (error) {
    alert('注册失败：' + (error.message || '请稍后重试'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
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

.register-btn {
  width: 100%;
  padding: 12px;
  background-color: #52c41a;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.register-btn:hover {
  background-color: #389e0d;
}

.register-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}
</style>