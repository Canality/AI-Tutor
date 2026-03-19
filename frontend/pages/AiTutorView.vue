<template>
  <div class="ai-tutor-container">
    <h1>AI Tutor</h1>
    <div class="chat-container">
      <div class="chat-messages">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.type === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>
      <QuestionInput @submit-question="handleQuestion" :disabled="loading" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import QuestionInput from '../components/QuestionInput.vue'
import { chatAPI } from '../services/apiService'

const messages = ref([
  { type: 'user', content: 'Hello, AI Tutor!' },
  { type: 'ai', content: 'Hello! How can I help you today?' }
])
const loading = ref(false)

// 加载聊天历史
onMounted(async () => {
  try {
    const history = await chatAPI.getChatHistory()
    if (history.messages && history.messages.length > 0) {
      messages.value = history.messages
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
})

// 处理用户提问
const handleQuestion = async (question) => {
  // 添加用户消息到聊天记录
  messages.value.push({ type: 'user', content: question })
  
  try {
    loading.value = true
    const response = await chatAPI.sendMessage(question)
    // 添加 AI 回复到聊天记录
    messages.value.push({ type: 'ai', content: response.response })
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({ type: 'ai', content: '抱歉，发送消息失败，请稍后重试。' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-tutor-container {
  max-width: 800px;
  margin: 50px auto;
  padding: 20px;
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

.chat-container {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.message {
  margin-bottom: 15px;
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 18px;
  word-wrap: break-word;
}

.user-message {
  align-self: flex-end;
  background-color: #4a90e2;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message {
  align-self: flex-start;
  background-color: #e9e9e9;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
}
</style>