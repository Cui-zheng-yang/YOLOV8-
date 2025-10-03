<template>
  <div class="stats-panel">
    <div class="stat-card" :class="{ warning: store.currentFallDetected }">
      <div class="stat-icon">
        <i :class="store.currentFallDetected ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle'"></i>
      </div>
      <div class="stat-content">
        <h4>跌倒状态</h4>
        <div class="stat-value">
          {{ store.currentFallDetected ? '⚠️ 警告' : '✓ 正常' }}
        </div>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">
        <i class="fas fa-users"></i>
      </div>
      <div class="stat-content">
        <h4>检测人数</h4>
        <div class="stat-value">{{ store.totalDetectionCount }}</div>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">
        <i class="fas fa-exclamation-circle"></i>
      </div>
      <div class="stat-content">
        <h4>跌倒次数</h4>
        <div class="stat-value fall-count">{{ store.totalFallCount }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useDetectionStore } from '@/stores/detection'

const store = useDetectionStore()
</script>

<style scoped>
.stats-panel {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 35px;
  margin-bottom: 25px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.stat-card.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}

.stat-icon {
  font-size: 3em;
  opacity: 0.9;
  min-width: 60px;
  text-align: center;
}

.stat-content {
  flex: 1;
}

.stat-content h4 {
  font-size: 0.95em;
  opacity: 0.9;
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2.2em;
  font-weight: bold;
  line-height: 1;
}

.fall-count {
  color: #ffeb3b;
}

@media (max-width: 968px) {
  .stats-panel {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .stat-card {
    padding: 20px;
  }
  
  .stat-icon {
    font-size: 2.5em;
  }
  
  .stat-value {
    font-size: 1.8em;
  }
}
</style>