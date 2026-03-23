<template>
  <div class="ai-tutor-page">
    <Navigation />
    
    <div class="main-content">
      <!-- 历史记录侧边栏 -->
      <div class="history-sidebar" :class="{ 'collapsed': !showHistory }">
        <div class="history-header">
          <h3>💬 历史记录</h3>
          <button class="toggle-btn" @click="showHistory = !showHistory">
            {{ showHistory ? '◀' : '▶' }}
          </button>
        </div>
        <div class="history-list" v-if="showHistory">
          <div 
            v-for="(session, index) in chatHistory" 
            :key="index"
            :class="['history-item', { 'active': currentSessionIndex === index }]"
            @click="loadSession(index)"
          >
            <div class="session-title">{{ session.title || '新对话' }}</div>
            <div class="session-time">{{ formatTime(session.time) }}</div>
          </div>
          <button class="new-chat-btn" @click="startNewChat">+ 新建对话</button>
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="chat-area">
        <h1>🤖 AI 智能辅导</h1>
        <p class="subtitle">输入你的数学问题，AI 将为你提供详细解答</p>
        
        <div class="chat-box" ref="chatBox">
          <div class="messages" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.type]">
              <div class="avatar">{{ msg.type === 'user' ? '👤' : '🤖' }}</div>
              <div class="content">
                <div v-if="msg.type === 'ai' && msg.loading" class="loading-dots">
                  <span></span><span></span><span></span>
                </div>
                <div v-else-if="msg.type === 'user'" class="message-text">{{ msg.content }}</div>
                <div v-else class="message-text" v-html="formatContent(msg.content)"></div>
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
      showHistory: true,
      chatHistory: [],
      currentSessionIndex: 0,
      mathJaxLoaded: false
    }
  },
  mounted() {
    this.loadMathJax()
    this.loadChatHistory()
    this.loadCurrentSession()
  },
  updated() {
    // 每次更新后渲染 MathJax
    this.renderMathJax()
  },
  methods: {
    // 加载 MathJax
    loadMathJax() {
      if (window.MathJax) {
        this.mathJaxLoaded = true
        return
      }
      
      window.MathJax = {
        tex: {
          inlineMath: [['$', '$'], ['\\(', '\\)']],
          displayMath: [['$$', '$$'], ['\\[', '\\]']]
        },
        svg: { fontCache: 'global' },
        startup: {
          pageReady: () => {
            this.mathJaxLoaded = true
            this.renderMathJax()
          }
        },
        options: {
          skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
          ignoreHtmlClass: 'tex2jax_ignore'
        }
      }
      
      const script = document.createElement('script')
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js'
      script.async = true
      script.crossOrigin = 'anonymous'
      document.head.appendChild(script)
    },
    
    // 渲染 MathJax
    renderMathJax() {
      if (!this.mathJaxLoaded || !window.MathJax) return
      
      this.$nextTick(() => {
        const messageTexts = this.$refs.messageText
        if (messageTexts) {
          // 更新每个消息的 HTML 内容
          this.messages.forEach((msg, index) => {
            if (messageTexts[index] && msg.type === 'ai' && !msg.loading) {
              messageTexts[index].innerHTML = this.formatContent(msg.content)
            }
          })
          
          // 触发 MathJax 渲染
          window.MathJax.typesetPromise(messageTexts).catch(err => {
            console.error('MathJax error:', err)
          })
        }
      })
    },
    
    // 格式化内容（处理换行和特殊格式）
    formatContent(content) {
      if (!content) return ''
      
      // 转义 HTML
      let html = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
      
      // 处理步骤标题（如 ### 💡 思路点拨）
      html = html.replace(/#{1,3}\s*(💡|📝|❓|✅|🔍|💭|⭐|🎯|📌|⚠️)\s*([^\n]+)/g, 
        '<div class="step-header"><span class="step-icon">$1</span><span class="step-title">$2</span></div>')
      
      // 先处理常见 LaTeX 命令（在公式处理之前）
      html = html.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)')
      html = html.replace(/\\sum/g, '∑')
      html = html.replace(/\\cdot/g, '·')
      html = html.replace(/\\times/g, '×')
      html = html.replace(/\\leq/g, '≤')
      html = html.replace(/\\geq/g, '≥')
      html = html.replace(/\\neq/g, '≠')
      html = html.replace(/\\infty/g, '∞')
      html = html.replace(/\\pi/g, 'π')
      // 处理 \quad \text{(1)} 这种标注
      html = html.replace(/\\quad\s*\\text\{\(([^)]+)\)\}/g, ' ($1)')
      html = html.replace(/\\text\{\(([^)]+)\)\}/g, '($1)')
      // 处理 \quad 空格
      html = html.replace(/\\quad/g, '  ')
      
      // 处理下标（将 a_1 转换为 a₁）- 在公式处理之前
      html = html.replace(/([a-zA-Z])_(\d+|\{[^}]+\})/g, (match, p1, p2) => {
        const subscripts = {
          '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
          '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
          'n': 'ₙ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ'
        }
        // 去掉花括号
        const num = p2.replace(/\{(.+)\}/, '$1')
        // 转换每个数字
        const sub = num.split('').map(c => subscripts[c] || c).join('')
        return p1 + sub
      })
      
      // 处理上标（将 ^2 转换为 ²）- 在公式处理之前
      html = html.replace(/\^(\d+|\{[^}]+\})/g, (match, p1) => {
        const superscripts = {
          '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
          '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
          'n': 'ⁿ'
        }
        const num = p1.replace(/\{(.+)\}/, '$1')
        const sup = num.split('').map(c => superscripts[c] || c).join('')
        return sup
      })
      
      // 处理 LaTeX 公式 - 使用简单样式包装（最后处理）
      // 先处理 \( ... \) 格式的行内公式
      html = html.replace(/\\\(([^)]+?)\\\)/g, '<span class="math-formula">$1</span>')
      // 再处理块级公式 $$...$$
      html = html.replace(/\$\$\s*([^$]+?)\s*\$\$/g, '<div class="math-formula-block">$1</div>')
      // 再处理行内公式 $...$（非贪婪匹配，避免跨行）
      html = html.replace(/\$([^$\n]+?)\$/g, '<span class="math-formula">$1</span>')
      
      // 处理列表项（1. 2. 3.）
      html = html.replace(/(\d+)\.\s+([^<\n]+)/g, '<div class="list-item"><span class="list-number">$1.</span> $2</div>')
      
      // 处理换行 - 保留多个换行作为段落分隔
      html = html.replace(/\n\n+/g, '</p><p>')
      html = html.replace(/\n/g, '<br>')
      
      // 包装在段落中
      if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>'
      }
      
      return html
    },
    
    // 加载历史记录
    loadChatHistory() {
      const saved = localStorage.getItem('chatHistory')
      if (saved) {
        this.chatHistory = JSON.parse(saved)
      }
      if (this.chatHistory.length === 0) {
        this.startNewChat()
      }
    },
    
    // 保存历史记录
    saveChatHistory() {
      localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory))
    },
    
    // 加载当前会话
    loadCurrentSession() {
      const saved = localStorage.getItem('currentSession')
      if (saved) {
        this.messages = JSON.parse(saved)
      }
    },
    
    // 保存当前会话
    saveCurrentSession() {
      localStorage.setItem('currentSession', JSON.stringify(this.messages))
      // 同时更新历史记录
      if (this.chatHistory[this.currentSessionIndex]) {
        this.chatHistory[this.currentSessionIndex].messages = this.messages
        this.chatHistory[this.currentSessionIndex].time = Date.now()
        if (this.messages.length > 0 && this.messages[0].type === 'user') {
          this.chatHistory[this.currentSessionIndex].title = this.messages[0].content.slice(0, 30)
        }
        this.saveChatHistory()
      }
    },
    
    // 开始新对话
    startNewChat() {
      // 保存当前会话
      if (this.messages.length > 0) {
        this.saveCurrentSession()
      }
      
      // 创建新会话
      this.messages = []
      this.currentSessionIndex = this.chatHistory.length
      this.chatHistory.push({
        title: '新对话',
        time: Date.now(),
        messages: []
      })
      this.saveChatHistory()
    },
    
    // 加载指定会话
    loadSession(index) {
      this.saveCurrentSession()
      this.currentSessionIndex = index
      this.messages = this.chatHistory[index].messages || []
      this.saveCurrentSession()
    },
    
    // 格式化时间
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
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
        content: userQuestion
      })
      
      this.question = ''
      this.loading = true
      
      // 添加 AI 消息
      const aiMsg = { 
        type: 'ai', 
        content: '',
        loading: true 
      }
      this.messages.push(aiMsg)
      const aiMsgIndex = this.messages.length - 1
      
      this.scrollToBottom()
      
      try {
        const token = localStorage.getItem('token')
        
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
          this.$router.push('/')
          return
        }
        
        if (!response.ok) {
          throw new Error('请求失败')
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        let buffer = ''
        
        this.messages[aiMsgIndex].loading = false
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            // 处理缓冲区中剩余的数据
            if (buffer) {
              const lines = buffer.split('\n')
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.substring(6)
                  if (data && data !== '[DONE]') {
                    fullContent += data
                  }
                }
              }
              if (fullContent && this.messages[aiMsgIndex]) {
                this.messages[aiMsgIndex].content = fullContent
              }
            }
            break
          }
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          // 保留最后一行（可能不完整）到缓冲区
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.substring(6)
              if (data && data !== '[DONE]') {
                fullContent += data
                if (this.messages[aiMsgIndex]) {
                  this.messages[aiMsgIndex].content = fullContent
                  this.scrollToBottom()
                }
              }
            }
          }
        }
        
        // 保存会话
        this.saveCurrentSession()
        
      } catch (error) {
        console.error('发送失败:', error)
        if (this.messages[aiMsgIndex]) {
          this.messages[aiMsgIndex].loading = false
          this.messages[aiMsgIndex].content = '抱歉，发生了错误，请稍后重试。'
        }
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

.main-content {
  display: flex;
  min-height: 100vh;
}

/* 历史记录侧边栏 */
.history-sidebar {
  width: 250px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.history-sidebar.collapsed {
  width: 50px;
}

.history-sidebar.collapsed .history-header h3 {
  display: none;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.history-header h3 {
  color: white;
  margin: 0;
  font-size: 16px;
}

.toggle-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.history-item {
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.history-item.active {
  background: rgba(255, 255, 255, 0.3);
  border-left: 3px solid #fff;
}

.session-title {
  color: white;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  margin-top: 4px;
}

.new-chat-btn {
  width: calc(100% - 20px);
  margin: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px dashed rgba(255, 255, 255, 0.4);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 聊天区域 */
.chat-area {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 防止flex子项溢出 */
}

h1 {
  color: white;
  text-align: center;
  margin-bottom: 10px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  margin-bottom: 20px;
}

.chat-box {
  flex: 1;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 500px;
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
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.8;
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

/* 步骤标题样式 */
:deep(.step-header) {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 20px 0 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

:deep(.step-icon) {
  font-size: 20px;
}

:deep(.step-title) {
  font-weight: 600;
  color: #667eea;
  font-size: 1.05em;
}

.message-text {
  word-wrap: break-word;
  line-height: 1.8;
}

:deep(.message-text p) {
  margin: 12px 0;
}

/* 列表项样式 */
:deep(.list-item) {
  margin: 8px 0;
  padding-left: 8px;
}

:deep(.list-number) {
  font-weight: 600;
  color: #667eea;
  margin-right: 4px;
}

/* MathJax 公式样式 */
:deep(.MathJax) {
  font-size: 1.1em;
  margin: 0 4px;
}

/* 备用公式样式（当 MathJax 加载失败时使用） */
:deep(.math-formula) {
  font-family: 'Cambria Math', 'Segoe UI Symbol', 'Times New Roman', serif;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8ecf4 100%);
  padding: 4px 10px;
  border-radius: 6px;
  margin: 0 4px;
  color: #1a237e;
  font-size: 1.1em;
  letter-spacing: 0.8px;
  border: 1px solid #c5cae9;
  white-space: nowrap;
  font-weight: 500;
}

:deep(.math-formula-block) {
  font-family: 'Cambria Math', 'Segoe UI Symbol', 'Times New Roman', serif;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8ecf4 100%);
  padding: 20px 24px;
  border-radius: 10px;
  margin: 16px 0;
  text-align: center;
  color: #1a237e;
  font-size: 1.2em;
  letter-spacing: 1px;
  border: 1px solid #c5cae9;
  box-shadow: 0 2px 8px rgba(26, 35, 126, 0.1);
  font-weight: 500;
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

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    flex-direction: column;
  }
  
  .history-sidebar {
    width: 100%;
    max-height: 200px;
  }
  
  .history-sidebar.collapsed {
    width: 100%;
    max-height: 60px;
  }
  
  .chat-area {
    padding: 10px;
  }
}
</style>
