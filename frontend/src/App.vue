<template>
  <div class="app-container">
    <!-- 头部 -->
    <AppHeader />
    
    <!-- 主内容 -->
    <div class="main-container">
      <!-- 模式选择器 -->
      <ModeSelector v-model="currentMode" />
      
      <!-- 图片检测模式 -->
      <ImageDetector 
        v-if="currentMode === 'image'"
        @detection-complete="handleDetectionResult"
      />
      
      <!-- 视频检测模式 -->
      <VideoDetector 
        v-if="currentMode === 'video'"
        @detection-complete="handleDetectionResult"
      />
      
      <!-- 统计面板 -->
      <StatsPanel />
      
      <!-- 检测记录 -->
      <DetectionHistory />
    </div>
    
    <!-- 跌倒警告弹窗 -->
    <FallAlert />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDetectionStore } from './stores/detection'
import AppHeader from './components/AppHeader.vue'
import ModeSelector from './components/ModeSelector.vue'
import ImageDetector from './components/ImageDetector.vue'
import VideoDetector from './components/VideoDetector.vue'
import StatsPanel from './components/StatsPanel.vue'
import DetectionHistory from './components/DetectionHistory.vue'
import FallAlert from './components/FallAlert.vue'
import { checkBackendHealth } from './api/detection'

const currentMode = ref('image')
const detectionStore = useDetectionStore()

// 处理检测结果
const handleDetectionResult = (result) => {
  detectionStore.addDetectionResult(result)
}

// 检查后端连接
onMounted(async () => {
  try {
    await checkBackendHealth()
    console.log('✅ 后端连接成功')
  } catch (error) {
    console.error('❌ 后端连接失败:', error)
    alert('无法连接到后端服务！\n请确保后端服务已启动：\npython app.py')
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: fadeInUp 0.8s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>