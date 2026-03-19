<template>
  <div class="question-input-container">
    <textarea
      v-model="question"
      placeholder="请输入您的问题..."
      @keydown.enter.exact="handleSubmit"
      :disabled="disabled"
    ></textarea>
    <button @click="handleSubmit" :disabled="disabled">发送</button>
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

const handleSubmit = () => {
  if (question.value.trim() && !props.disabled) {
    emit('submit-question', question.value)
    question.value = ''
  }
}
</script>

<style scoped>
.question-input-container {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-top: 1px solid #eee;
  background-color: white;
}

textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-size: 14px;
  min-height: 60px;
}

textarea:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

button {
  padding: 0 20px;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  align-self: flex-end;
  margin-bottom: 10px;
}

button:hover {
  background-color: #357abd;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>