<template>
  <div class="ai-tutor-page">
    <Navigation />
    
    <div class="tutor-container">
      <h1>🤖 AI 智能辅导</h1>
      <p class="subtitle">输入你的数学问题，AI 将为你提供详细解答</p>
      
      <div class="chat-container">
        <div class="messages" ref="messagesContainer">
          <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.type]">
            <div class="avatar">{{ msg.type === 'user' ? '👤' : '🤖' }}</div>
            <div class="content">
              <div v-if="msg.type === 'ai' && msg.loading" class="loading-dots">
                <span></span><span></span><span></span>
              </div>
              <div v-else v-html="formatMessage(msg.content)"></div>
            </div>
          </div>
        </div>
        
        <div class="input-area">
          <textarea
            v-model="question"
            placeholder="请输入你的数学问题..."
            @keydown.enter.prevent="sendQuestionHandler"
            rows="3"
          ></textarea>
          <div class="actions">
            <button @click="sendQuestionHandler" :disabled="loading || !question.trim()">
              {{ loading ? '思考中...' : '发送问题' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Navigation from '../components/Navigation.vue'
import { chatAPI } from '../services/apiService.js'

export default {
  name: 'AiTutorView',
  components: {
    Navigation
  },
  data() {
    return {
      question: '',
      messages: [],
      loading: false
    }
  },
  methods: {
    async sendQuestionHandler() {
      if (!this.question.trim() || this.loading) return
      
      const userQuestion = this.question.trim()
      this.messages.push({ type: 'user', content: userQuestion })
      this.question = ''
      this.loading = true
      
      // 添加 loading 消息
      const loadingMsg = { type: 'ai', content: '', loading: true }
      this.messages.push(loadingMsg)
      this.scrollToBottom()
      
      try {
        let fullAnswer = ''
        await chatAPI.askStream(userQuestion, null, (full) => {
          fullAnswer = full
          loadingMsg.content = fullAnswer
          loadingMsg.loading = false
          this.scrollToBottom()
        }, (error) => {
          console.error('Stream error:', error)
        })
        
        if (!fullAnswer) {
          loadingMsg.content = '抱歉，暂时无法回答这个问题。'
          loadingMsg.loading = false
        }
      } catch (error) {
        console.error('发送问题失败:', error)
        loadingMsg.content = '抱歉，发生了错误，请稍后重试。'
        loadingMsg.loading = false
      } finally {
        this.loading = false
        this.scrollToBottom()
      }
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    
    formatMessage(content) {
      // 简单的换行格式化
      return content.replace(/\n/g, '<br>')
    }
  }
}
</script>

<style scoped>
.ai-tutor-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.tutor-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  color: white;
  text-align: center;
  margin-bottom: 10px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  margin-bottom: 30px;
}

.chat-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.messages {
  height: 400px;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.message {
  display: flex;
  margin-bottom: 16px;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message.user .content {
  background: #667eea;
  color: white;
}

.message.ai .content {
  background: white;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #eee;
}

.input-area textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  transition: border-color 0.3s;
}

.input-area textarea:focus {
  outline: none;
  border-color: #667eea;
}

.actions {
  margin-top: 12px;
  text-align: right;
}

.actions button {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.actions button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
