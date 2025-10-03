<template>
  <div class="app-header">
    <h1>
      <i class="fas fa-brain"></i>
      YOLOv8 行人跌倒检测系统
    </h1>
    <p class="subtitle">基于深度学习的实时跌倒监测与预警系统</p>
    <div class="feature-badges">
      <span class="badge">
        <i class="fas fa-check"></i> 图片检测
      </span>
      <span class="badge">
        <i class="fas fa-video"></i> 实时视频
      </span>
      <span class="badge">
        <i class="fas fa-bell"></i> 智能预警
      </span>
      <span class="badge">
        <i class="fas fa-chart-line"></i> 数据统计
      </span>
    </div>
  </div>
</template>

<style scoped>
.app-header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
  animation: fadeInDown 0.8s ease;
}

.app-header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.app-header h1 i {
  margin-right: 15px;
}

.subtitle {
  font-size: 1.2em;
  opacity: 0.9;
  margin-bottom: 20px;
}

.feature-badges {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 0.95em;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.badge:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.badge i {
  margin-right: 5px;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.8em;
  }
  
  .subtitle {
    font-size: 1em;
  }
  
  .feature-badges {
    gap: 10px;
  }
  
  .badge {
    font-size: 0.85em;
    padding: 6px 15px;
  }
}
</style>