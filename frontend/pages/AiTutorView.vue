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

const messages = ref([
  { type: 'user', content: 'Hello, AI Tutor!' },
  { type: 'ai', content: 'Hello! How can I help you today?' }
])
const loading = ref(false)
const selectedImage = ref(null)
const questionInput = ref(null)
const currentAiResponse = ref('')
const isStreaming = ref(false)

// 计算属性，用于显示普通文本
const renderMathInElement = (text) => {
  if (!text) return ''
  
  // 处理特殊字符
  // 处理换行符
  let html = text.replace(/\\n/g, '<br>')
  // 处理制表符
  html = html.replace(/\\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;')
  // 处理空格
  html = html.replace(/\\s/g, ' ')
  
  // 处理分段和分点内容
  // 1. 清理文本，移除多余的空白
  html = html.trim()
  
  // 2. 处理思路点拨、详细引导、轮到你了等部分
  // 先将整个内容包装在一个容器中
  let result = '<div class="content-wrapper">'
  
  // 处理各个部分
  const sections = html.split(/\*\*\s*[💡📝❓]\s*[^*]+\s*\*\*/g)
  const sectionTitles = html.match(/\*\*\s*[💡📝❓]\s*[^*]+\s*\*\*/g) || []
  
  // 遍历每个部分
  for (let i = 0; i < sections.length; i++) {
    let section = sections[i].trim()
    if (!section) continue
    
    // 添加标题（如果有）
    if (i < sectionTitles.length) {
      const title = sectionTitles[i].replace(/\*\*/g, '').trim()
      result += `<h3 class="section-title">${title}</h3>`
    }
    
    // 处理分点内容
    if (section.includes('- ')) {
      result += '<ul class="points-list">'
      const points = section.split(/\s*-\s+/)
      points.forEach((point, index) => {
        if (point.trim()) {
          // 直接显示原始文本，不进行数学公式渲染
          result += `<li>${point.trim()}</li>`
        }
      })
      result += '</ul>'
    } else {
      // 处理普通段落
      // 直接显示原始文本，不进行数学公式渲染
      result += `<p class="content-paragraph">${section}</p>`
    }
  }
  
  result += '</div>'
  
  return result
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
      (accumulatedData) => {
        // 处理流式响应
        console.log('收到响应:', accumulatedData)
        // 直接替换当前 AI 回复，而不是追加
        currentAiResponse.value = accumulatedData
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



/* 内容包装器样式 */
.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 分点内容样式 */
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.points-list {
  margin: 0 0 16px 0;
  padding-left: 24px;
  list-style-type: none;
}

.points-list li {
  margin-bottom: 10px;
  line-height: 1.5;
  position: relative;
  padding-left: 16px;
}

.points-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #4a90e2;
  font-weight: bold;
  font-size: 16px;
}

/* 段落样式 */
.content-paragraph {
  margin: 0 0 16px 0;
  line-height: 1.6;
  color: #333;
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