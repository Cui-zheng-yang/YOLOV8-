<template>
  <div class="mode-selector">
    <div 
      class="mode-btn" 
      :class="{ active: currentMode === 'image' }"
      @click="switchMode('image')"
    >
      <i class="fas fa-image"></i>
      <h3>图片检测</h3>
      <p>上传图片进行分析</p>
    </div>
    <div 
      class="mode-btn" 
      :class="{ active: currentMode === 'video' }"
      @click="switchMode('video')"
    >
      <i class="fas fa-video"></i>
      <h3>实时视频</h3>
      <p>摄像头实时监测</p>
    </div>
  </div>
</template>

<script>
export default {
  props: { currentMode: { type: String, default: 'image' } },
  methods: {
    switchMode(mode) {
      this.$emit('mode-changed', mode);
    },
  },
};
</script>