<!-- src/pages/RegisterView.vue -->
<template>
  <div class="register-page">
    <div class="split-container">
      <!-- 左侧品牌区 -->
      <div class="brand-side">
        <div class="brand-content">
          <div class="brand-icon">🚀</div>
          <h1 class="brand-title">开启学习</h1>
          <p class="brand-slogan">加入我们，让AI成为你的私人教师</p>
          <p class="brand-sub">智能辅导 • 个性推荐 • 成长追踪</p>
          
          <div class="brand-features">
            <div class="feature-dot">✓ 免费使用基础功能</div>
            <div class="feature-dot">✓ 无限次AI题目解析</div>
            <div class="feature-dot">✓ 个性化学习路径规划</div>
          </div>
        </div>
      </div>
      
      <!-- 右侧表单区 -->
      <div class="form-side">
        <div class="register-card">
          <div class="card-header">
            <div class="logo-icon">📝</div>
            <h2>创建账户</h2>
            <p>填写以下信息开始你的学习之旅</p>
          </div>
          
          <form @submit.prevent="handleRegister">
            <!-- 用户名 -->
            <div class="input-group" :class="{ 'has-error': errors.username }">
              <label>用户名</label>
              <input 
                v-model="form.username"
                type="text"
                placeholder="设置一个独特的用户名"
                @blur="validateUsername"
              />
              <span class="error-msg" v-if="errors.username">{{ errors.username }}</span>
            </div>

            <!-- 邮箱 -->
            <div class="input-group" :class="{ 'has-error': errors.email }">
              <label>邮箱</label>
              <input 
                v-model="form.email"
                type="email"
                placeholder="example@email.com"
                @blur="validateEmail"
              />
              <span class="error-msg" v-if="errors.email">{{ errors.email }}</span>
            </div>
            
            <!-- 密码 -->
            <div class="input-group" :class="{ 'has-error': errors.password }">
              <label>密码</label>
              <div class="password-input">
                <input 
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="设置密码（至少6位）"
                  @input="checkPasswordStrength"
                />
                <span class="toggle-pwd" @click="showPassword = !showPassword">
                  {{ showPassword ? '🙈' : '👁️' }}
                </span>
              </div>
              <!-- 密码强度条 -->
              <div class="strength-bar" v-if="form.password">
                <div class="strength-fill" :class="passwordStrength"></div>
              </div>
              <span class="strength-text" v-if="form.password">
                密码强度: {{ strengthText }}
              </span>
              <span class="error-msg" v-if="errors.password">{{ errors.password }}</span>
            </div>
            
            <!-- 确认密码 -->
            <div class="input-group" :class="{ 'has-error': errors.confirmPassword }">
              <label>确认密码</label>
              <input 
                v-model="form.confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="再次输入密码"
                @blur="validateConfirmPassword"
              />
              <span class="error-msg" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
            </div>

            <!-- 用户协议 -->
            <div class="agreement" :class="{ 'has-error': errors.agreement }">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.agreement" />
                <span>我已阅读并同意 <a href="#" class="link">用户协议</a> 和 <a href="#" class="link">隐私政策</a></span>
              </label>
              <span class="error-msg" v-if="errors.agreement">{{ errors.agreement }}</span>
            </div>
            
            <button 
              type="submit" 
              class="register-btn"
              :disabled="isSubmitting || !isFormValid"
              :class="{ 'loading': isSubmitting }"
            >
              {{ isSubmitting ? '注册中...' : '立即注册' }}
            </button>
          </form>
          
          <!-- 底部特性 -->
          <div class="feature-trio">
            <div class="feature-item">
              <div class="feature-icon">🔒</div>
              <div class="feature-text">数据安全</div>
            </div>
            <div class="divider"></div>
            <div class="feature-item">
              <div class="feature-icon">⚡</div>
              <div class="feature-text">极速响应</div>
            </div>
            <div class="divider"></div>
            <div class="feature-item">
              <div class="feature-icon">🎯</div>
              <div class="feature-text">精准推荐</div>
            </div>
          </div>
          
          <div class="footer">
            <span>已有账号？</span>
            <router-link to="/" class="login-link">直接登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: false
})

const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: ''
})

const showPassword = ref(false)
const isSubmitting = ref(false)
const passwordStrength = ref('')

// 密码强度文本
const strengthText = computed(() => {
  if (passwordStrength.value === 'weak') return '弱'
  if (passwordStrength.value === 'medium') return '中'
  if (passwordStrength.value === 'strong') return '强'
  return ''
})

// 密码强度检测
const checkPasswordStrength = () => {
  const pwd = form.password
  if (!pwd) {
    passwordStrength.value = ''
    return
  }
  if (pwd.length < 6) {
    passwordStrength.value = 'weak'
  } else if (pwd.length >= 6 && /[a-zA-Z]/.test(pwd) && /[0-9]/.test(pwd)) {
    passwordStrength.value = 'strong'
  } else {
    passwordStrength.value = 'medium'
  }
}

// 验证函数
const validateUsername = () => {
  if (!form.username.trim()) {
    errors.username = '用户名不能为空'
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
  } else {
    errors.username = ''
  }
}

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email) {
    errors.email = '请输入邮箱'
  } else if (!emailRegex.test(form.email)) {
    errors.email = '邮箱格式不正确'
  } else {
    errors.email = ''
  }
}

const validatePassword = () => {
  if (!form.password) {
    errors.password = '请输入密码'
  } else if (form.password.length < 6) {
    errors.password = '密码至少6位'
  } else {
    errors.password = ''
  }
}

const validateConfirmPassword = () => {
  if (!form.confirmPassword) {
    errors.confirmPassword = '请确认密码'
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
  } else {
    errors.confirmPassword = ''
  }
}

const isFormValid = computed(() => {
  return form.username && form.email && form.password && 
         form.confirmPassword && form.agreement &&
         !errors.username && !errors.email && !errors.password && !errors.confirmPassword
})

const handleRegister = async () => {
  // 验证所有字段
  validateUsername()
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  
  if (!form.agreement) {
    errors.agreement = '请同意用户协议'
  } else {
    errors.agreement = ''
  }

  if (!isFormValid.value) return

  isSubmitting.value = true
  
  // 模拟API调用
  setTimeout(() => {
    isSubmitting.value = false
    
    // 保存注册用户信息到 localStorage（供主界面读取）
    localStorage.setItem('user_info', JSON.stringify({
      username: form.username,
      name: form.username,
      email: form.email,
      avatar: '👤',
      registerTime: new Date().toISOString()
    }))
    
    alert('🎉 注册成功！欢迎加入AI Tutor')
    router.push('/')
  }, 1500)
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

/* 分屏布局 */
.split-container {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  height: 100%;
  width: 100%;
  place-items: center;
}

/* 左侧品牌面板 */
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
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.brand-title { 
  font-size: 48px; 
  font-weight: 700; 
  margin: 0 0 15px 0; 
  letter-spacing: -1px;
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
  margin: 0 0 40px 0; 
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
  padding: 0 20px;
}

.feature-dot {
  font-size: 14px;
  color: #e1e1e1;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 右侧表单区 */
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

/* 注册卡片 */
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
  justify-content: center;
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
  display: inline-block;
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

/* 输入框组 */
.input-group { 
  margin-bottom: 20px; 
  position: relative;
}

.input-group.has-error input {
  border-color: #ff4d4f;
  background-color: #fff2f0;
}

.error-msg {
  display: block;
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 6px;
  margin-left: 4px;
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

/* 密码输入框 */
.password-input {
  position: relative;
}

.password-input input {
  padding-right: 45px;
}

.toggle-pwd {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  font-size: 18px;
  opacity: 0.6;
  transition: opacity 0.3s;
  user-select: none;
}

.toggle-pwd:hover {
  opacity: 1;
}

/* 密码强度条 */
.strength-bar {
  height: 4px;
  background: #e1e1e1;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  width: 0;
  transition: all 0.3s;
  border-radius: 2px;
}

.strength-fill.weak {
  width: 33%;
  background: #ff4d4f;
}

.strength-fill.medium {
  width: 66%;
  background: #faad14;
}

.strength-fill.strong {
  width: 100%;
  background: #52c41a;
}

.strength-text {
  display: block;
  font-size: 12px;
  margin-top: 4px;
  color: #666;
}

/* 用户协议 */
.agreement {
  margin-bottom: 24px;
}

.agreement.has-error .checkbox-label {
  color: #ff4d4f;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  line-height: 1.5;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 2px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.link {
  color: #0071e3;
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  text-decoration: underline;
}

/* 注册按钮 */
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
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
}

.register-btn:hover:not(:disabled) { 
  background: #000; 
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}

.register-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.7;
}

.register-btn.loading {
  color: transparent;
}

.register-btn.loading::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  top: 50%;
  left: 50%;
  margin-left: -10px;
  margin-top: -10px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spinner 0.8s linear infinite;
}

@keyframes spinner {
  to { transform: rotate(360deg); }
}

/* 底部特性 Trio */
.feature-trio {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.feature-item { 
  text-align: center; 
  flex: 1; 
}

.feature-icon { 
  font-size: 24px; 
  margin-bottom: 6px; 
  transition: transform 0.3s;
}

.feature-item:hover .feature-icon {
  transform: scale(1.1);
}

.feature-text { 
  font-size: 13px; 
  font-weight: 600; 
  color: #1d1d1f; 
}

.divider { 
  width: 1px; 
  height: 30px; 
  background: #ddd; 
}

/* 底部链接 */
.footer { 
  text-align: center; 
  font-size: 14px; 
  color: #86868b; 
  margin-top: 10px; 
}

.login-link { 
  color: #0071e3; 
  text-decoration: none; 
  font-weight: 700; 
  margin-left: 4px;
  transition: all 0.3s;
}

.login-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

/* 响应式 */
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
    max-height: 95vh;
  }
}
</style>
