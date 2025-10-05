<template>
  <div class="app-container">
    <!-- 头部 -->
    <AppHeader />
    
    <!-- 标签页导航 -->
    <div class="tabs-container">
      <div class="tab-buttons">
        <button 
          class="tab-btn" 
          :class="{ active: currentTab === 'detection' }"
          @click="currentTab = 'detection'"
        >
          <i class="fas fa-search"></i> 检测中心
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: currentTab === 'knowledge' }"
          @click="currentTab = 'knowledge'"
        >
          <i class="fas fa-network-wired"></i> 知识图谱
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: currentTab === 'analytics' }"
          @click="currentTab = 'analytics'"
        >
          <i class="fas fa-chart-line"></i> 数据分析
        </button>
      </div>
      
      <!-- 标签页内容 -->
      <div class="tab-content">
        <!-- 检测中心标签页 -->
        <div v-if="currentTab === 'detection'" class="detection-tab">
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
        
        <!-- 知识图谱标签页 -->
        <div v-if="currentTab === 'knowledge'" class="knowledge-tab">
          <KnowledgeGraph />
        </div>
        
        <!-- 数据分析标签页 -->
        <div v-if="currentTab === 'analytics'" class="analytics-tab">
          <DataAnalytics />
        </div>
      </div>
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
import KnowledgeGraph from './components/KnowledgeGraph.vue'
import DataAnalytics from './components/DataAnalytics.vue'
import { checkBackendHealth } from './api/detection'

// 标签页和模式管理
const currentTab = ref('detection') // 默认显示检测中心
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

.tabs-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
  animation: fadeInUp 0.8s ease;
}

.tab-buttons {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.tab-btn {
  padding: 16px 24px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: #e9ecef;
}

.tab-btn.active {
  background: white;
  color: #667eea;
  border-bottom: 3px solid #667eea;
}

.tab-content {
  padding: 30px;
  min-height: 600px;
}

.detection-tab, .knowledge-tab, .analytics-tab {
  height: 100%;
}

.knowledge-tab, .analytics-tab {
  height: calc(100vh - 180px);
  overflow: hidden;
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