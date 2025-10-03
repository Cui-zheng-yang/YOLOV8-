<template>
  <div class="video-detector">
    <div class="detection-area">
      <!-- 摄像头预览区 -->
      <div class="preview-box">
        <h3><i class="fas fa-camera"></i> 摄像头画面</h3>
        <div v-if="!isStreaming" class="camera-placeholder" @click="startVideo">
          <i class="fas fa-video"></i>
          <p>点击下方按钮启动摄像头</p>
          <small>需要授权访问摄像头</small>
        </div>
        <div v-else class="video-wrapper">
          <video 
            ref="videoElement" 
            autoplay 
            playsinline
            muted
          ></video>
          <canvas ref="canvasElement" style="display: none;"></canvas>
          <div class="video-overlay">
            <div class="video-status">
              <span class="status-indicator"></span>
              正在监测中
            </div>
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
        <div v-else class="result-wrapper">
          <img :src="resultFrame" alt="检测结果" />
          <div class="fps-badge">
            <i class="fas fa-tachometer-alt"></i>
            {{ fps.toFixed(1) }} FPS
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
        :disabled="isStarting"
      >
        <i :class="isStarting ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
        {{ isStarting ? '正在启动...' : '启动检测' }}
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

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <div>
        <strong>错误：</strong>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick } from 'vue'
import { detectVideoFrame } from '@/api/detection'
import { canvasToBase64 } from '@/utils/fileHelper'

const emit = defineEmits(['detection-complete'])

const videoElement = ref(null)
const canvasElement = ref(null)
const isStreaming = ref(false)
const isStarting = ref(false)
const resultFrame = ref(null)
const error = ref(null)
const detectionInterval = ref(500)
const fps = ref(0)

let mediaStream = null
let detectionTimer = null
let fpsTimer = null
let frameCount = 0

const startVideo = async () => {
  if (isStarting.value || isStreaming.value) return
  
  error.value = null
  isStarting.value = true
  isStreaming.value = true // 先设置 isStreaming 为 true 以渲染 video 元素
  
  try {
    await nextTick() // 等待 DOM 更新，确保 video 元素已渲染
    
    console.log('🎥 开始启动摄像头...')
    
    // 1. 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('浏览器不支持摄像头访问，请使用 Chrome、Firefox 或 Edge')
    }
    
    console.log('✅ 浏览器支持摄像头API')
    
    // 2. 请求摄像头权限和视频流
    const constraints = {
      video: {
        width: { ideal: 1280, max: 1920 },
        height: { ideal: 720, max: 1080 },
        facingMode: 'user'
      },
      audio: false
    }
    
    console.log('📹 请求摄像头...', constraints)
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    console.log('✅ 摄像头流获取成功')
    
    // 3. 检查视频轨道
    const videoTracks = mediaStream.getVideoTracks()
    if (videoTracks.length === 0) {
      throw new Error('未找到视频轨道')
    }
    
    console.log('📹 视频轨道信息:', {
      label: videoTracks[0].label,
      enabled: videoTracks[0].enabled,
      readyState: videoTracks[0].readyState
    })
    
    // 4. 设置视频元素的流
    if (!videoElement.value) {
      throw new Error('视频元素未找到')
    }
    
    videoElement.value.srcObject = mediaStream
    console.log('✅ 视频流已设置到video元素')
    
    // 5. 等待视频元数据加载
    await new Promise((resolve, reject) => {
      const video = videoElement.value
      const timeout = setTimeout(() => {
        reject(new Error('视频加载超时（10秒）'))
      }, 10000)
      
      video.onloadedmetadata = () => {
        clearTimeout(timeout)
        console.log('✅ 视频元数据加载完成')
        console.log('📺 视频尺寸:', video.videoWidth, 'x', video.videoHeight)
        resolve()
      }
      
      video.onerror = (e) => {
        clearTimeout(timeout)
        console.error('❌ 视频元素错误:', e)
        reject(new Error('视频元素加载失败'))
      }
    })
    
    // 6. 确保视频播放
    try {
      await videoElement.value.play()
      console.log('✅ 视频播放成功')
    } catch (playErr) {
      console.warn('⚠️ 自动播放失败，但流已设置:', playErr.message)
    }
    
    // 7. 最终检查
    if (videoElement.value.videoWidth === 0 || videoElement.value.videoHeight === 0) {
      throw new Error('视频尺寸为0，可能未正确加载')
    }
    
    // 8. 标记为成功
    isStarting.value = false
    
    console.log('🎉 摄像头启动完全成功！')
    console.log('📊 最终状态:', {
      videoWidth: videoElement.value.videoWidth,
      videoHeight: videoElement.value.videoHeight,
      paused: videoElement.value.paused,
      readyState: videoElement.value.readyState
    })
    
    // 9. 启动检测和FPS计数
    await new Promise(resolve => setTimeout(resolve, 500))
    startDetection()
    startFpsCounter()
    
  } catch (err) {
    console.error('❌ 摄像头启动失败:', err)
    isStarting.value = false
    isStreaming.value = false
    
    // 清理资源
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      mediaStream = null
    }
    if (videoElement.value) {
      videoElement.value.srcObject = null
    }
    
    // 设置友好的错误消息
    if (err.name === 'NotAllowedError') {
      error.value = '摄像头权限被拒绝。请点击地址栏的 🔒 图标，允许访问摄像头后刷新页面。'
    } else if (err.name === 'NotFoundError') {
      error.value = '未检测到摄像头设备。请确保摄像头已正确连接并且驱动已安装。'
    } else if (err.name === 'NotReadableError') {
      error.value = '摄像头被其他程序占用。请关闭 Zoom、Teams、Skype 等程序后重试。'
    } else if (err.name === 'OverconstrainedError') {
      error.value = '摄像头不支持请求的配置。请尝试使用其他摄像头或降低分辨率。'
    } else {
      error.value = `摄像头启动失败：${err.message}`
    }
  }
}

const stopVideo = () => {
  console.log('🛑 停止摄像头')
  
  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }
  
  if (fpsTimer) {
    clearInterval(fpsTimer)
    fpsTimer = null
  }
  
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => {
      track.stop()
      console.log('✅ 停止轨道:', track.kind, track.label)
    })
    mediaStream = null
  }
  
  if (videoElement.value) {
    videoElement.value.srcObject = null
    videoElement.value.load()
  }
  
  isStreaming.value = false
  resultFrame.value = null
  fps.value = 0
  frameCount = 0
  error.value = null
}

const startDetection = () => {
  console.log(`⏱️ 启动检测定时器，间隔: ${detectionInterval.value}ms`)
  
  detectionTimer = setInterval(async () => {
    await captureAndDetect()
  }, detectionInterval.value)
}

const captureAndDetect = async () => {
  const video = videoElement.value
  const canvas = canvasElement.value
  
  if (!video || !canvas || !isStreaming.value) {
    return
  }
  
  if (video.readyState < 2 || video.videoWidth === 0) {
    console.warn('⚠️ 视频尚未准备好，跳过本帧')
    return
  }
  
  try {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    const frameData = canvasToBase64(canvas, 'image/jpeg', 0.8)
    
    const response = await detectVideoFrame(frameData)
    
    if (response.success) {
      resultFrame.value = response.result_frame
      emit('detection-complete', response)
      frameCount++
    }
  } catch (err) {
    console.error('❌ 帧检测失败:', err.message)
  }
}

const startFpsCounter = () => {
  let lastCount = 0
  
  fpsTimer = setInterval(() => {
    fps.value = frameCount - lastCount
    lastCount = frameCount
  }, 1000)
}

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
  cursor: pointer;
  transition: all 0.3s;
}

.camera-placeholder:hover {
  background: #f0f0f0;
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

.video-wrapper, .result-wrapper {
  flex: 1;
  position: relative;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-wrapper video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.result-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
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
  background: #00ff00;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.fps-badge {
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

.fps-badge i {
  margin-right: 5px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  background: white;
  border-radius: 10px;
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

.btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
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
  align-items: flex-start;
  gap: 12px;
  line-height: 1.6;
}

.error-message i {
  font-size: 1.5em;
  flex-shrink: 0;
  margin-top: 2px;
}

.error-message strong {
  display: block;
  margin-bottom: 5px;
}

.fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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