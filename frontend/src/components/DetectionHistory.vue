<template>
  <div v-if="store.recentHistory.length > 0" class="detection-history">
    <div class="history-header">
      <h3>
        <i class="fas fa-history"></i>
        检测记录
      </h3>
      <button class="clear-btn" @click="clearHistory">
        <i class="fas fa-trash-alt"></i>
        清空记录
      </button>
    </div>

    <div class="history-list">
      <TransitionGroup name="list">
        <div 
          v-for="item in store.recentHistory" 
          :key="item.id"
          class="history-item"
          :class="{ fall: item.isFall }"
        >
          <div class="item-icon">
            {{ item.isFall ? '🚨' : '👤' }}
          </div>
          <div class="item-content">
            <div class="item-status">
              <strong>{{ item.isFall ? '⚠️ 跌倒警告' : '✓ 正常状态' }}</strong>
              <span class="item-time">{{ item.timestamp }}</span>
            </div>
            <div class="item-details">
              <span class="detail-badge">
                <i class="fas fa-chart-line"></i>
                风险评分: {{ item.score.toFixed(2) }}
              </span>
              <span class="detail-badge">
                <i class="fas fa-percentage"></i>
                置信度: {{ (item.confidence * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { useDetectionStore } from '@/stores/detection'

const store = useDetectionStore()

const clearHistory = () => {
  if (confirm('确定要清空所有检测记录吗？')) {
    store.resetStats()
  }
}
</script>

<style scoped>
.detection-history {
  margin-top: 30px;
  background: #f8f9fa;
  border-radius: 15px;
  padding: 25px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-header h3 {
  color: #333;
  font-size: 1.4em;
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-header h3 i {
  color: #667eea;
}

.clear-btn {
  padding: 8px 20px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.95em;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  background: #c82333;
  transform: translateY(-2px);
}

.history-list {
  max-height: 450px;
  overflow-y: auto;
  padding-right: 10px;
}

.history-list::-webkit-scrollbar {
  width: 8px;
}

.history-list::-webkit-scrollbar-track {
  background: #e9ecef;
  border-radius: 10px;
}

.history-list::-webkit-scrollbar-thumb {
  background: #adb5bd;
  border-radius: 10px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: #868e96;
}

.history-item {
  background: white;
  padding: 18px;
  margin-bottom: 12px;
  border-radius: 12px;
  border-left: 5px solid #667eea;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 15px;
  transition: all 0.3s ease;
}

.history-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.history-item.fall {
  border-left-color: #f5576c;
  background: linear-gradient(90deg, #fff5f5 0%, white 100%);
}

.item-icon {
  font-size: 2.5em;
  min-width: 50px;
  text-align: center;
}

.item-content {
  flex: 1;
}

.item-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.item-status strong {
  font-size: 1.1em;
  color: #333;
}

.item-time {
  color: #6c757d;
  font-size: 0.9em;
  font-weight: 500;
}

.item-details {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.detail-badge {
  background: #e9ecef;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 0.85em;
  color: #495057;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.detail-badge i {
  color: #667eea;
}

.list-enter-active {
  transition: all 0.4s ease;
}

.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .clear-btn {
    align-self: flex-end;
  }
  
  .item-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .item-details {
    flex-direction: column;
    gap: 8px;
  }
}
</style>