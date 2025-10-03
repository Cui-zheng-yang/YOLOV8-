<template>
  <div class="video-detector">
    <!-- 检测区域 -->
    <div class="detection-area">
      <!-- 摄像头预览区 -->
      <div class="preview-box">
        <h3><i class="fas fa-camera"></i> 摄像头画面</h3>
        <div v-if="!isStreaming" class="camera-placeholder">
          <i class="fas fa-video"></i>
          <p>点击下方按钮启动摄像头</p>
          <small>需要授权访问摄像头</small>
        </div>
        <div v-else class="video-container">
          <video 
            ref="videoElement" 
            autoplay 
            playsinline
            muted
          ></video>
          <canvas ref="canvasElement" style="display: none;"></canvas>
          <div class="video-status">
            <span class="status-indicator active"></span>
            正在监测中
          </div>
        </div>
      </div>

      <!-- 检测结果区 -->
      <div class="preview-box">
        <h3><i class="fas fa-eye"></i> 检测结果</h3>
        <div v-if="!resultFrame" class="empty-state">
          <i class="fas fa-image"></i>
          <p>{{ isStreaming ? '等待检测结果...' : '启动视频后显示检测结果' }}</p>
        </div>
        <div v-else class="result-container">
          <img :src="resultFrame" alt="检测结果" />
          <div class="fps-counter">
            <i class="fas fa-tachometer-alt"></i>
            FPS: {{ fps.toFixed(1) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="controls">
      <button 
        v-if="!isStreaming"
        class="btn btn-primary"
        @click="startVideo"
      >
        <i class="fas fa-play"></i>
        启动检测
      </button>
      <button 
        v-else
        class="btn btn-danger"
        @click="stopVideo"
      >
        <i class="fas fa-stop"></i>
        停止检测
      </button>
      
      <div class="settings">
        <label>检测频率：</label>
        <select v-model.number="detectionInterval" :disabled="isStreaming">
          <option :value="250">快速 (4 FPS)</option>
          <option :value="500">标准 (2 FPS)</option>
          <option :value="1000">省电 (1 FPS)</option>
        </select>
      </div>
    </div>

    <!-- 提示信息 -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { detectVideoFrame } from '@/api/detection'
import { canvasToBase64 } from '@/utils/fileHelper'

const emit = defineEmits(['detection-complete'])

const videoElement = ref(null)
const canvasElement = ref(null)
const isStreaming = ref(false)
const resultFrame = ref(null)
const error = ref(null)
const detectionInterval = ref(500) // 默认500ms
const fps = ref(0)

let mediaStream = null
let detectionTimer = null
let fpsTimer = null
let frameCount = 0

// 启动视频
const startVideo = async () => {
  error.value = null
  
  try {
    // 请求摄像头权限
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      },
      audio: false
    })
    
    // 设置视频流
    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      isStreaming.value = true
      
      // 等待视频加载
      await new Promise((resolve) => {
        videoElement.value.onloadedmetadata = resolve
      })
      
      // 开始检测
      startDetection()
      
      // 开始FPS计算
      startFpsCounter()
    }
  } catch (err) {
    console.error('摄像头启动失败:', err)
    
    if (err.name === 'NotAllowedError') {
      error.value = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头'
    } else if (err.name === 'NotFoundError') {
      error.value = '未检测到摄像头设备'
    } else {
      error.value = '摄像头启动失败：' + err.message
    }
    
    isStreaming.value = false
  }
}

// 停止视频
const stopVideo = () => {
  // 停止检测
  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }
  
  // 停止FPS计数
  if (fpsTimer) {
    clearInterval(fpsTimer)
    fpsTimer = null
  }
  
  // 停止媒体流
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  
  // 清空视频元素
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
  
  isStreaming.value = false
  resultFrame.value = null
  fps.value = 0
  frameCount = 0
}

// 开始检测
const startDetection = () => {
  detectionTimer = setInterval(async () => {
    await captureAndDetect()
  }, detectionInterval.value)
}

// 捕获并检测
const captureAndDetect = async () => {
  const video = videoElement.value
  const canvas = canvasElement.value
  
  if (!video || !canvas || !isStreaming.value) return
  
  try {
    // 设置canvas尺寸
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    // 绘制当前帧
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    // 转换为Base64
    const frameData = canvasToBase64(canvas, 'image/jpeg', 0.8)
    
    // 发送到后端检测
    const response = await detectVideoFrame(frameData)
    
    if (response.success) {
      resultFrame.value = response.result_frame
      emit('detection-complete', response)
      frameCount++
    }
  } catch (err) {
    console.error('检测失败:', err)
    // 不中断检测，继续下一帧
  }
}

// FPS计数器
const startFpsCounter = () => {
  let lastCount = 0
  
  fpsTimer = setInterval(() => {
    fps.value = frameCount - lastCount
    lastCount = frameCount
  }, 1000)
}

// 组件卸载时清理
onUnmounted(() => {
  stopVideo()
})
</script>

<style scoped>
.video-detector {
  margin-top: 30px;
}

.detection-area {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  margin-bottom: 25px;
}

.preview-box {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 25px;
  border: 2px dashed #dee2e6;
  min-height: 500px;
  display: flex;
  flex-direction: column;
}

.preview-box h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.3em;
  text-align: center;
}

.preview-box h3 i {
  margin-right: 8px;
  color: #667eea;
}

.camera-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  color: #999;
}

.camera-placeholder i {
  font-size: 5em;
  margin-bottom: 20px;
  color: #667eea;
}

.camera-placeholder p {
  font-size: 1.2em;
  margin-bottom: 10px;
}

.camera-placeholder small {
  color: #bbb;
}

.video-container, .result-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
}

.video-container video, .result-container img {
  max-width: 100%;
  max-height: 450px;
  border-radius: 8px;
}

.video-status {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.9em;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff0000;
}

.status-indicator.active {
  background: #00ff00;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.fps-counter {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
}

.fps-counter i {
  margin-right: 5px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-state i {
  font-size: 4em;
  margin-bottom: 20px;
}

.empty-state p {
  font-size: 1.1em;
}

.controls {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  padding: 14px 35px;
  border: none;
  border-radius: 25px;
  font-size: 1.1em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-danger {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.settings {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: #f8f9fa;
  border-radius: 20px;
}

.settings label {
  font-weight: 500;
  color: #666;
}

.settings select {
  padding: 8px 15px;
  border: 2px solid #dee2e6;
  border-radius: 10px;
  font-size: 1em;
  cursor: pointer;
  background: white;
}

.settings select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  margin-top: 20px;
  padding: 15px 20px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 10px;
  color: #856404;
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-message i {
  font-size: 1.3em;
}

@media (max-width: 968px) {
  .detection-area {
    grid-template-columns: 1fr;
  }
  
  .controls {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>