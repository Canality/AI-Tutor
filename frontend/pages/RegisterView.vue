<template>
  <div class="register-container">
    <div class="register-card">
      <h1>注册账号</h1>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-item">
          <label>用户名</label>
          <input 
            v-model="form.username"
            type="text"
            placeholder="设置用户名"
            class="form-input"
          />
        </div>
        
        <div class="form-item">
          <label>密码</label>
          <input 
            v-model="form.password"
            type="password"
            placeholder="设置密码"
            class="form-input"
          />
        </div>
        
        <div class="form-item">
          <label>确认密码</label>
          <input 
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            class="form-input"
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
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.register-card {
  max-width: 420px;
  width: 100%;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.register-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #52c41a, #389e0d);
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
  background: linear-gradient(90deg, #52c41a, #389e0d);
  border-radius: 3px;
}

.register-form {
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
  border-color: #52c41a;
  box-shadow: 0 0 0 3px rgba(82, 196, 26, 0.1);
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #999;
  transition: color 0.3s ease;
}

.form-input:focus::placeholder {
  color: #ccc;
}

.register-btn {
  padding: 14px;
  background: linear-gradient(135deg, #52c41a, #389e0d);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.2);
  margin-top: 10px;
}

.register-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.2);
  transition: left 0.3s ease;
}

.register-btn:hover::before {
  left: 0;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.register-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.register-btn:disabled::before {
  display: none;
}

.login-link {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #666;
}

.login-link router-link {
  color: #52c41a;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.login-link router-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background-color: #52c41a;
  transition: width 0.3s ease;
}

.login-link router-link:hover::after {
  width: 100%;
}

.login-link router-link:hover {
  color: #389e0d;
}

@media (max-width: 768px) {
  .register-card {
    padding: 30px 20px;
  }
  
  h1 {
    font-size: 20px;
  }
}
</style>