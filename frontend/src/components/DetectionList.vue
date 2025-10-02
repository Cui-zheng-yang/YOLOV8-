<template>
  <div class="detection-list">
    <h3><i class="fas fa-list"></i> 检测记录</h3>
    <div 
      class="detection-item" 
      v-for="(item, idx) in detectionHistory" 
      :key="idx"
      :class="{ fall: item.status === '跌倒' }"
    >
      <div class="detection-info">
        <strong>{{ item.status === '跌倒' ? '⚠️ 跌倒警告' : '✓ 正常状态' }}</strong>
        <p>风险评分: {{ item.riskScore }} | {{ item.time }}</p>
      </div>
      <div class="detection-icon">{{ item.status === '跌倒' ? '🚨' : '👤' }}</div>
    </div>
  </div>
</template>

<script>
import { getDetectionHistory } from '@/api/detection';

export default {
  data() {
    return { detectionHistory: [] };
  },
  mounted() {
    this.fetchHistory();
  },
  methods: {
    async fetchHistory() {
      try {
        const { data } = await getDetectionHistory();
        this.detectionHistory = data;
      } catch (err) {
        console.error('历史记录获取失败:', err);
      }
    },
    addDetectionResult(result) {
      const newItem = {
        status: result.isFall ? '跌倒' : '正常',
        riskScore: result.riskScore.toFixed(2),
        time: new Date().toLocaleTimeString(),
      };
      this.detectionHistory.unshift(newItem);
      if (this.detectionHistory.length > 20) this.detectionHistory.pop(); // 最多保留20条
    },
  },
};
</script>