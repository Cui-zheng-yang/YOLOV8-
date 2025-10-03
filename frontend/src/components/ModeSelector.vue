<template>
  <div class="mode-selector">
    <div 
      class="mode-card"
      :class="{ active: modelValue === 'image' }"
      @click="selectMode('image')"
    >
      <i class="fas fa-image"></i>
      <h3>图片检测</h3>
      <p>上传图片进行跌倒检测分析</p>
    </div>
    
    <div 
      class="mode-card"
      :class="{ active: modelValue === 'video' }"
      @click="selectMode('video')"
    >
      <i class="fas fa-video"></i>
      <h3>实时视频</h3>
      <p>使用摄像头进行实时监测</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: String,
    default: 'image'
  }
})

const emit = defineEmits(['update:modelValue'])

const selectMode = (mode) => {
  emit('update:modelValue', mode)
}
</script>

<style scoped>
.mode-selector {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.mode-card {
  padding: 30px;
  border: 3px solid #e0e0e0;
  border-radius: 15px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.mode-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.mode-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.mode-card i {
  font-size: 3.5em;
  display: block;
  margin-bottom: 15px;
}

.mode-card h3 {
  font-size: 1.5em;
  margin-bottom: 10px;
  font-weight: 600;
}

.mode-card p {
  font-size: 1em;
  opacity: 0.8;
  margin: 0;
}

@media (max-width: 768px) {
  .mode-selector {
    grid-template-columns: 1fr;
  }
}
</style>