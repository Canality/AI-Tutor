<template>
  <div class="ai-tutor-container">
    <h1>AI Tutor</h1>
    <div class="chat-container">
      <div class="chat-messages">
        <div class="message user-message">
          <div class="message-content">Hello, AI Tutor!</div>
        </div>
        <div class="message ai-message">
          <div class="message-content">Hello! How can I help you today?</div>
        </div>
      </div>
      <QuestionInput @submit-question="handleQuestion" />
    </div>
  </div>
</template>

<script setup>
import QuestionInput from '../components/QuestionInput.vue';

const handleQuestion = (question) => {
  console.log('用户提问：', question);
};
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