<template>
  <div class="ai-tutor-container">
    <Navigation />
    <h1>AI Tutor</h1>
    <div class="chat-container">
      <div class="chat-messages">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.type === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content" v-html="renderMathInElement(message.content)"></div>
        </div>
        <div v-if="isStreaming && currentAiResponse" class="message ai-message">
          <div class="message-content" v-html="renderMathInElement(currentAiResponse)"></div>
        </div>
        <div v-else-if="loading" class="message ai-message">
          <div class="message-content">AI 正在思考中...</div>
        </div>
      </div>
      <div class="input-area">
        <div class="input-with-image">
          <QuestionInput 
            @submit-question="handleQuestion" 
            :disabled="loading" 
            ref="questionInput"
          />
          <div class="upload-area">
            <input 
              type="file" 
              accept="image/*" 
              @change="handleImageSelect" 
              :disabled="loading"
              class="file-input"
              id="image-upload"
            />
            <label for="image-upload" class="upload-btn" :disabled="loading">
              📷 {{ selectedImage ? '已选择图片' : '上传图片' }}
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import QuestionInput from '../components/QuestionInput.vue'
import Navigation from '../components/Navigation.vue'
import { chatAPI } from '../services/apiService'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const messages = ref([
  { type: 'user', content: 'Hello, AI Tutor!' },
  { type: 'ai', content: 'Hello! How can I help you today?' }
])
const loading = ref(false)
const selectedImage = ref(null)
const questionInput = ref(null)
const currentAiResponse = ref('')
const isStreaming = ref(false)

// 计算属性，用于渲染数学公式
const renderMathInElement = (text) => {
  if (!text) return ''
  
  // 处理数学公式，将 \( 和 \) 之间的内容渲染为行内公式
  // 将 \[ 和 \] 之间的内容渲染为块级公式
  let html = text
  
  // 处理行内公式
  html = html.replace(/\\\((.*?)\\\)/g, (match, formula) => {
    try {
      return katex.renderToString(formula, {
        throwOnError: false
      })
    } catch (error) {
      console.error('KaTeX 渲染错误:', error)
      return match
    }
  })
  
  // 处理块级公式
  html = html.replace(/\\\[(.*?)\\\]/g, (match, formula) => {
    try {
      return `<div class="katex-block">${katex.renderToString(formula, {
        throwOnError: false,
        displayMode: true
      })}</div>`
    } catch (error) {
      console.error('KaTeX 渲染错误:', error)
      return match
    }
  })
  
  return html
}

// 处理用户提问
const handleQuestion = async (question) => {
  if (!question.trim() && !selectedImage.value) return
  
  // 添加用户消息到聊天记录
  let userMessage = question.trim()
  if (selectedImage.value) {
    userMessage += ' (上传了一张图片)'
  }
  messages.value.push({ type: 'user', content: userMessage })
  
  try {
    loading.value = true
    isStreaming.value = true
    currentAiResponse.value = ''
    
    // 使用流式接口发送消息和图片
    await chatAPI.askStream(
      question,
      selectedImage.value,
      (chunk) => {
        // 处理流式响应
        console.log('收到响应:', chunk)
        // 将接收到的 chunk 添加到当前 AI 回复中
        currentAiResponse.value += chunk
      },
      (error) => {
        console.error('发送消息失败:', error)
        messages.value.push({ type: 'ai', content: '抱歉，发送消息失败，请稍后重试。' })
        loading.value = false
        isStreaming.value = false
      }
    )
    
    // 当流式传输结束时，添加完整的 AI 回复到聊天记录
    setTimeout(() => {
      if (currentAiResponse.value) {
        messages.value.push({ type: 'ai', content: currentAiResponse.value })
      }
      loading.value = false
      isStreaming.value = false
      currentAiResponse.value = ''
    }, 500)
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({ type: 'ai', content: '抱歉，发送消息失败，请稍后重试。' })
    loading.value = false
    isStreaming.value = false
  } finally {
    // 重置图片选择
    selectedImage.value = null
    // 重置文件输入
    const fileInput = document.getElementById('image-upload')
    if (fileInput) {
      fileInput.value = ''
    }
  }
}

// 处理图片选择
const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedImage.value = file
    console.log('已选择图片:', file.name)
  }
}
</script>

<style scoped>
.ai-tutor-container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  background-color: white;
  position: relative;
  overflow: hidden;
}

.ai-tutor-container::before {
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
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 700;
  position: relative;
  padding-bottom: 12px;
}

h1::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, #4a90e2, #357abd);
  border-radius: 3px;
}

.chat-container {
  height: 600px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: #f9f9f9;
  position: relative;
}

.chat-messages::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e8e8e8, transparent);
}

.message {
  margin-bottom: 16px;
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
  position: relative;
  animation: messageSlideIn 0.3s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}

@keyframes messageSlideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  align-self: flex-end;
  background: linear-gradient(135deg, #4a90e2, #357abd);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
}

.ai-message {
  align-self: flex-start;
  background-color: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: 1px solid #e8e8e8;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
}

.input-area {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e8e8e8;
}

.input-with-image {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-area {
  position: relative;
  margin-top: 8px;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-btn {
  display: inline-block;
  padding: 10px 20px;
  background-color: #f0f5ff;
  color: #1890ff;
  border: 1px solid #d6e4ff;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.upload-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(24, 144, 255, 0.1);
  transition: left 0.3s ease;
}

.upload-btn:hover::before {
  left: 0;
}

.upload-btn:hover {
  background-color: #e6f7ff;
  border-color: #91d5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);
}

.upload-btn:disabled {
  background-color: #f5f5f5;
  color: #ccc;
  border-color: #e8e8e8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.upload-btn:disabled::before {
  display: none;
}

/* 自定义滚动条 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* KaTeX 样式 */
.katex-block {
  margin: 10px 0;
  text-align: center;
}

.katex {
  font-size: 1.1em !important;
}

.message-content :deep(.katex) {
  display: inline-block;
}

.message-content :deep(.katex-display) {
  margin: 0.5em 0;
}

@media (max-width: 768px) {
  .ai-tutor-container {
    margin: 15px;
    padding: 16px;
  }
  
  .chat-container {
    height: 400px;
  }
  
  .message {
    max-width: 85%;
  }
}
</style>