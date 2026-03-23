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
              <div v-else class="message-text" v-html="msg.renderedContent || renderContent(msg.content)"></div>
            </div>
          </div>
        </div>
        
        <!-- 图片预览 -->
        <div v-if="selectedImage" class="image-preview">
          <img :src="imagePreviewUrl" alt="预览" />
          <button class="remove-image" @click="removeImage">×</button>
        </div>
        
        <div class="input-area">
          <textarea
            v-model="question"
            placeholder="请输入你的数学问题..."
            @keydown.enter.prevent="sendQuestionHandler"
            rows="3"
          ></textarea>
          <div class="actions">
            <input
              type="file"
              ref="imageInput"
              accept="image/*"
              style="display: none"
              @change="handleImageSelect"
            />
            <button class="upload-btn" @click="$refs.imageInput.click()" :disabled="loading">
              📷 上传图片
            </button>
            <button @click="sendQuestionHandler" :disabled="loading || (!question.trim() && !selectedImage)">
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

export default {
  name: 'AiTutorView',
  components: {
    Navigation
  },
  data() {
    return {
      question: '',
      messages: [],
      loading: false,
      selectedImage: null,
      imagePreviewUrl: null
    }
  },
  mounted() {
    this.loadMathJax()
  },
  methods: {
    // 加载 MathJax
    loadMathJax() {
      if (window.MathJax) return
      
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.min.js'
      script.async = true
      
      window.MathJax = {
        tex: {
          inlineMath: [['$', '$'], ['\\(', '\\)']],
          displayMath: [['$$', '$$'], ['\\[', '\\]']]
        },
        svg: { fontCache: 'global' },
        startup: { pageReady: () => console.log('MathJax ready') }
      }
      
      document.head.appendChild(script)
    },
    
    // 渲染内容（处理换行）
    renderContent(content) {
      if (!content) return ''
      return content.replace(/\n/g, '<br>')
    },
    
    // 触发 MathJax 渲染
    renderMath() {
      this.$nextTick(() => {
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise().catch(err => console.error('MathJax error:', err))
        }
      })
    },
    
    // 选择图片
    handleImageSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.selectedImage = file
        this.imagePreviewUrl = URL.createObjectURL(file)
      }
    },
    
    // 移除图片
    removeImage() {
      this.selectedImage = null
      this.imagePreviewUrl = null
      if (this.$refs.imageInput) {
        this.$refs.imageInput.value = ''
      }
    },
    
    // 发送问题
    async sendQuestionHandler() {
      if ((!this.question.trim() && !this.selectedImage) || this.loading) return
      
      const userQuestion = this.question.trim() || '请分析图片中的题目'
      
      // 添加用户消息
      this.messages.push({ 
        type: 'user', 
        content: userQuestion,
        renderedContent: this.renderContent(userQuestion)
      })
      
      this.question = ''
      this.loading = true
      
      // 添加 AI 消息（初始为空）
      const aiMsgIndex = this.messages.length
      this.messages.push({ 
        type: 'ai', 
        content: '',
        renderedContent: '',
        loading: true 
      })
      
      this.scrollToBottom()
      
      try {
        const token = localStorage.getItem('token')
        const formData = new FormData()
        formData.append('question', userQuestion)
        if (this.selectedImage) {
          formData.append('image', this.selectedImage)
        }
        
        const response = await fetch('/api/chat/ask-stream', {
          method: 'POST',
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: formData
        })
        
        if (!response.ok) {
          throw new Error('请求失败')
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        
        // 关闭 loading，开始显示内容
        this.messages[aiMsgIndex].loading = false
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.substring(6)
              if (data && data !== '[DONE]') {
                fullContent += data
                // 实时更新显示
                this.messages[aiMsgIndex].content = fullContent
                this.messages[aiMsgIndex].renderedContent = this.renderContent(fullContent)
                this.scrollToBottom()
                // 每接收一定内容触发 MathJax 渲染
                if (fullContent.length % 50 === 0) {
                  this.renderMath()
                }
              }
            }
          }
        }
        
        // 最终渲染
        this.renderMath()
        
      } catch (error) {
        console.error('发送失败:', error)
        this.messages[aiMsgIndex].loading = false
        this.messages[aiMsgIndex].content = '抱歉，发生了错误，请稍后重试。'
        this.messages[aiMsgIndex].renderedContent = '抱歉，发生了错误，请稍后重试。'
      } finally {
        this.loading = false
        this.removeImage()
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

.message-text {
  word-wrap: break-word;
}

/* MathJax 公式样式 */
.message-text :deep(.MathJax) {
  font-size: 1.1em;
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

/* 图片预览 */
.image-preview {
  padding: 10px 20px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 10px;
}

.image-preview img {
  max-height: 100px;
  max-width: 200px;
  border-radius: 8px;
  border: 2px solid #ddd;
}

.remove-image {
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-btn {
  padding: 10px 20px;
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.actions button:last-child {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.actions button:last-child:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
