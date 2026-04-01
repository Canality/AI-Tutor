<template>
  <div class="question-input-container" ref="inputContainer">
    <textarea
      v-model="question"
      placeholder="请输入您的问题..."
      @keydown.enter.exact="handleSubmit"
      :disabled="disabled"
      class="question-textarea"
      ref="textarea"
    ></textarea>
    <button 
      @click="handleSubmit" 
      :disabled="disabled"
      class="submit-btn"
    >
      <span v-if="!disabled">↑</span>
      <span v-else>...</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['submit-question'])
const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const question = ref('')
const inputContainer = ref(null)
const textarea = ref(null)

const handleSubmit = () => {
  if (question.value.trim() && !props.disabled) {
    emit('submit-question', question.value)
    question.value = ''
  }
}

// 暴露方法给父组件
defineExpose({
  question,
  textarea,
  handleSubmit
})
</script>

<style scoped>
.question-input-container {
  display: flex;
  gap: 12px;
  padding: 0;
  border: none;
  background-color: transparent;
}

.question-textarea {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #e8e8e8;
  border-radius: 20px;
  resize: none;
  font-size: 14px;
  min-height: 44px;
  max-height: 100px;
  transition: all 0.3s ease;
  font-family: inherit;
  outline: none;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.question-textarea:focus {
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  transform: translateY(-1px);
}

.question-textarea:disabled {
  background-color: #f5f5f5;
  border-color: #e8e8e8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.question-textarea::placeholder {
  color: #999;
  transition: color 0.3s ease;
}

.question-textarea:focus::placeholder {
  color: #ccc;
}

.submit-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #4a90e2, #357abd);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background-color: rgba(255,255,255,0.2);
  transition: left 0.3s ease;
}

.submit-btn:hover::before {
  left: 0;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.submit-btn:disabled::before {
  display: none;
}

@media (max-width: 768px) {
  .question-input-container {
    flex-direction: row;
  }
  
  .submit-btn {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .question-textarea {
    min-height: 40px;
  }
}
</style>