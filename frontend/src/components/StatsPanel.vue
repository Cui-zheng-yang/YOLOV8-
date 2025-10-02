<template>
  <div class="stats-panel">
    <div class="stat-card" :class="{ warning: fallStatus === '跌倒' }">
      <h4>跌倒状态</h4>
      <div class="value">{{ fallStatus }}</div>
    </div>
    <div class="stat-card">
      <h4>检测人数</h4>
      <div class="value">{{ personCount }}</div>
    </div>
    <div class="stat-card">
      <h4>跌倒次数</h4>
      <div class="value">{{ fallCount }}</div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    fallStatus: { type: String, default: '正常' },
    personCount: { type: Number, default: 0 },
    fallCount: { type: Number, default: 0 },
  },
};
</script>