<template>
  <div class="profile-page">
    <Navigation />
    <div class="content">
      <h1>👤 学习画像</h1>
      <p>功能开发中...</p>
    </div>
  </div>
</template>

<script setup>
import Navigation from '../components/Navigation.vue'
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin-left: 250px;
}

.content {
  padding: 100px 20px 20px;
  text-align: center;
  color: white;
}

h1 {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .profile-page {
    margin-left: 0;
  }
}
</style>
