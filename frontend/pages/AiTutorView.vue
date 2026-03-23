<template>
  <div class="ai-tutor-page" :class="{ 'nav-collapsed': !navOpen }">
    <Navigation @toggle="navOpen = $event" />
    
    <div class="tutor-container">
      <h1>🤖 AI 智能辅导</h1>
      <p class="subtitle">输入你的数学问题，AI 将为你提供详细解答</p>
      
      <!-- 可拖动调整大小的对话框 -->
      <div 
        class="chat-wrapper" 
        ref="chatWrapper"
        :style="{ height: chatHeight + 'px' }"
      >
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
        
        <!-- 拖动调整大小的手柄 -->
        <div 
          class="resize-handle" 
          @mousedown="startResize"
          @touchstart="startResize"
        >
          <div class="resize-indicator"></div>
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
      imagePreviewUrl: null,
      navOpen: true,
      chatHeight: 500, // 默认高度
      isResizing: false,
      startY: 0,
      startHeight: 0
    }
  },
  mounted() {
    this.loadMathJax()
    // 从本地存储恢复高度设置
    const savedHeight = localStorage.getItem('chatHeight')
    if (savedHeight) {
      this.chatHeight = parseInt(savedHeight)
    }
  },
  beforeUnmount() {
    this.stopResize()
  },
  methods: {
    // 开始拖动调整大小
    startResize(e) {
      this.isResizing = true
      this.startY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY
      this.startHeight = this.chatHeight
      
      document.addEventListener('mousemove', this.onResize)
      document.addEventListener('mouseup', this.stopResize)
      document.addEventListener('touchmove', this.onResize)
      document.addEventListener('touchend', this.stopResize)
      
      document.body.style.cursor = 'ns-resize'
      document.body.style.userSelect = 'none'
    },
    
    // 拖动中
    onResize(e) {
      if (!this.isResizing) return
      
      const currentY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY
      const deltaY = this.startY - currentY
      const newHeight = Math.max(300, Math.min(800, this.startHeight + deltaY))
      
      this.chatHeight = newHeight
    },
    
    // 停止拖动
    stopResize() {
      if (this.isResizing) {
        this.isResizing = false
        // 保存高度到本地存储
        localStorage.setItem('chatHeight', this.chatHeight.toString())
      }
      
      document.removeEventListener('mousemove', this.onResize)
      document.removeEventListener('mouseup', this.stopResize)
      document.removeEventListener('touchmove', this.onResize)
      document.removeEventListener('touchend', this.stopResize)
      
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    },
    
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
    
    // 渲染内容
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
      
      // 添加 AI 消息
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
        
        // 检查 token 是否存在
        if (!token) {
          alert('登录已过期，请重新登录')
          this.$router.push('/')
          return
        }
        
        const formData = new FormData()
        formData.append('question', userQuestion)
        if (this.selectedImage) {
          formData.append('image', this.selectedImage)
        }
        
        const response = await fetch('/api/chat/ask-stream', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })
        
        if (response.status === 401) {
          alert('登录已过期，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('user_info')
          this.$router.push('/')
          return
        }
        
        if (!response.ok) {
          throw new Error('请求失败')
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        
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
                this.messages[aiMsgIndex].content = fullContent
                this.messages[aiMsgIndex].renderedContent = this.renderContent(fullContent)
                this.scrollToBottom()
                if (fullContent.length % 50 === 0) {
                  this.renderMath()
                }
              }
            }
          }
        }
        
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
  margin-left: 250px;
  transition: margin-left 0.3s ease;
}

.ai-tutor-page.nav-collapsed {
  margin-left: 0;
}

.tutor-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 80px 20px 20px;
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

/* 可调整大小的对话框容器 */
.chat-wrapper {
  position: relative;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages {
  flex: 1;
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

/* 拖动调整大小的手柄 */
.resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  background: transparent;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.resize-handle:hover .resize-indicator,
.resize-handle:active .resize-indicator {
  background: #667eea;
}

.resize-indicator {
  width: 60px;
  height: 4px;
  background: #ccc;
  border-radius: 2px;
  transition: background 0.2s;
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-tutor-page {
    margin-left: 0;
  }
  
  .tutor-container {
    padding: 70px 10px 10px;
  }
  
  .content {
    max-width: 85%;
  }
}
</style>
