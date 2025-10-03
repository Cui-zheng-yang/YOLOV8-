<template>
  <Transition name="alert">
    <div v-if="store.showFallAlert" class="alert-overlay" @click.self="closeAlert">
      <div class="alert-modal">
        <div class="alert-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <h2 class="alert-title">跌倒警告！</h2>
        <p class="alert-message">
          系统检测到行人跌倒，请立即查看现场情况并采取必要措施。
        </p>
        <div class="alert-time">
          <i class="fas fa-clock"></i>
          {{ currentTime }}
        </div>
        <div class="alert-actions">
          <button class="alert-btn primary" @click="closeAlert">
            <i class="fas fa-check"></i>
            我知道了
          </button>
          <button class="alert-btn secondary" @click="viewDetails">
            <i class="fas fa-list"></i>
            查看详情
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useDetectionStore } from '@/stores/detection'

const store = useDetectionStore()
const currentTime = ref('')

// 更新当前时间
const updateTime = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`
}

// 监听警告显示
watch(() => store.showFallAlert, (show) => {
  if (show) {
    updateTime()
  }
})

// 关闭警告
const closeAlert = () => {
  store.closeFallAlert()
}

// 查看详情
const viewDetails = () => {
  closeAlert()
  // 滚动到检测记录区域
  const historyElement = document.querySelector('.detection-history')
  if (historyElement) {
    historyElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<style scoped>
.alert-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.alert-modal {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
  20%, 40%, 60%, 80% { transform: translateX(10px); }
}

.alert-icon {
  width: 100px;
  height: 100px;
  margin: 0 auto 25px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3em;
  color: white;
  animation: pulse-icon 1.5s infinite;
}

@keyframes pulse-icon {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(245, 87, 108, 0.7);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 20px rgba(245, 87, 108, 0);
  }
}

.alert-title {
  font-size: 2em;
  color: #f5576c;
  margin-bottom: 15px;
  font-weight: bold;
}

.alert-message {
  font-size: 1.1em;
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.alert-time {
  background: #f8f9fa;
  padding: 10px 20px;
  border-radius: 25px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 30px;
  color: #495057;
  font-weight: 600;
}

.alert-time i {
  color: #f5576c;
}

.alert-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.alert-btn {
  padding: 12px 30px;
  border: none;
  border-radius: 25px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.alert-btn.primary {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
}

.alert-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 87, 108, 0.5);
}

.alert-btn.secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.alert-btn.secondary:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
}

/* 过渡动画 */
.alert-enter-active {
  animation: fadeIn 0.3s ease;
}

.alert-leave-active {
  animation: fadeOut 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@media (max-width: 768px) {
  .alert-modal {
    padding: 30px 20px;
  }
  
  .alert-icon {
    width: 80px;
    height: 80px;
    font-size: 2.5em;
  }
  
  .alert-title {
    font-size: 1.6em;
  }
  
  .alert-message {
    font-size: 1em;
  }
  
  .alert-actions {
    flex-direction: column;
  }
  
  .alert-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>