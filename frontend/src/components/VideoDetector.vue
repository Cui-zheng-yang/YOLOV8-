<template>
  <div class="video-detector">
    <!-- 视频检测核心区域（摄像头+结果） -->
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
          <p>{{ isStreaming ? '等待检测结果...' : (isProcessing ? '本地视频检测中...' : '启动视频后显示检测结果') }}</p>
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

    <!-- 扩展检测控制区（整合所有控制按钮） -->
    <div class="controls">
      <!-- 摄像头控制按钮 -->
      <button 
        v-if="!isStreaming && !isProcessing"
        class="btn btn-primary"
        @click="startVideo"
        :disabled="isStarting"
      >
        <i :class="isStarting ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
        {{ isStarting ? '正在启动...' : '启动摄像头检测' }}
      </button>
      <button 
        v-else-if="isStreaming && !isProcessing"
        class="btn btn-danger"
        @click="stopVideo"
      >
        <i class="fas fa-stop"></i>
        停止摄像头检测
      </button>
      
      <!-- 文件/本地视频检测按钮 -->
      <button 
        @click="startFileDetection" 
        :disabled="!selectedFile || isStreaming || isProcessing"
        class="btn btn-info"
      >
        {{ isProcessing ? '文件检测中...' : '开始文件检测' }}
      </button>
      <button 
        @click="stopFileDetection" 
        :disabled="!isProcessing"
        class="btn btn-secondary"
      >
        停止检测
      </button>
      <button 
        @click="detectLocalVideo" 
        :disabled="isStreaming || isProcessing"
        class="btn btn-success"
      >
        <i class="fas fa-file-video"></i>
        检测本地视频
      </button>
      <button 
        @click="resetDetector" 
        :disabled="isProcessing"
        class="btn btn-warning"
      >
        <i class="fas fa-redo"></i>
        重置检测器
      </button>
      
      <!-- 检测频率设置 -->
      <div class="settings">
        <label>检测频率：</label>
        <select v-model.number="detectionInterval" :disabled="isStreaming || isProcessing">
          <option :value="250">快速 (4 FPS)</option>
          <option :value="500">标准 (2 FPS)</option>
          <option :value="1000">省电 (1 FPS)</option>
        </select>
      </div>
    </div>

    <!-- 处理状态提示 -->
    <div v-if="processingStatus" class="processing-status">
      <i class="fas fa-info-circle"></i>
      {{ processingStatus }}
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
// 引入本地视频检测API（原代码中的detectionAPI）
import { detectLocalVideo as apiDetectLocalVideo} from '@/api/detection'
const emit = defineEmits(['detection-complete'])

// 摄像头相关状态
const videoElement = ref(null)
const canvasElement = ref(null)
const isStreaming = ref(false)
const isStarting = ref(false)
const resultFrame = ref(null)
const error = ref(null)
const detectionInterval = ref(500)
const fps = ref(0)

// 文件/本地视频检测相关状态
const selectedFile = ref(null) // 原代码中的选中文件
const isProcessing = ref(false)
const processingStatus = ref('')

// 内部资源引用
let mediaStream = null
let detectionTimer = null
let fpsTimer = null
let frameCount = 0
let fileDetectionAbortController = null // 文件检测中断控制器

// ---------------------- 摄像头检测逻辑 ----------------------
const startVideo = async () => {
  if (isStarting.value || isStreaming.value || isProcessing.value) return
  
  error.value = null
  isStarting.value = true
  isStreaming.value = true // 先设置为true以渲染video元素
  
  try {
    await nextTick() // 等待DOM更新
    
    // 1. 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('浏览器不支持摄像头访问，请使用Chrome、Firefox或Edge')
    }
    
    // 2. 请求摄像头权限
    const constraints = {
      video: {
        width: { ideal: 1280, max: 1920 },
        height: { ideal: 720, max: 1080 },
        facingMode: 'user'
      },
      audio: false
    }
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    // 3. 检查视频轨道
    const videoTracks = mediaStream.getVideoTracks()
    if (videoTracks.length === 0) {
      throw new Error('未找到视频轨道')
    }
    
    // 4. 设置视频流
    if (!videoElement.value) throw new Error('视频元素未找到')
    videoElement.value.srcObject = mediaStream
    
    // 5. 等待视频元数据加载
    await new Promise((resolve, reject) => {
      const video = videoElement.value
      const timeout = setTimeout(() => reject(new Error('视频加载超时（10秒）')), 10000)
      
      video.onloadedmetadata = () => {
        clearTimeout(timeout)
        resolve()
      }
      video.onerror = (e) => {
        clearTimeout(timeout)
        reject(new Error('视频元素加载失败'))
      }
    })
    
    // 6. 尝试播放视频
    try {
      await videoElement.value.play()
    } catch (playErr) {
      console.warn('自动播放失败，但流已设置:', playErr.message)
    }
    
    // 7. 最终检查
    if (videoElement.value.videoWidth === 0 || videoElement.value.videoHeight === 0) {
      throw new Error('视频尺寸为0，可能未正确加载')
    }
    
    // 8. 初始化完成
    isStarting.value = false
    await new Promise(resolve => setTimeout(resolve, 500))
    startDetection()
    startFpsCounter()
    
  } catch (err) {
    console.error('摄像头启动失败:', err)
    isStarting.value = false
    isStreaming.value = false
    
    // 清理资源
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      mediaStream = null
    }
    if (videoElement.value) videoElement.value.srcObject = null
    
    // 错误消息处理
    if (err.name === 'NotAllowedError') {
      error.value = '摄像头权限被拒绝，请点击地址栏🔒图标允许访问后刷新'
    } else if (err.name === 'NotFoundError') {
      error.value = '未检测到摄像头设备，请确保设备已连接'
    } else if (err.name === 'NotReadableError') {
      error.value = '摄像头被其他程序占用，请关闭Zoom/Teams等后重试'
    } else if (err.name === 'OverconstrainedError') {
      error.value = '摄像头不支持请求配置，请降低分辨率'
    } else {
      error.value = `摄像头启动失败：${err.message}`
    }
  }
}

const stopVideo = () => {
  // 清理摄像头相关资源
  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }
  if (fpsTimer) {
    clearInterval(fpsTimer)
    fpsTimer = null
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  if (videoElement.value) {
    videoElement.value.srcObject = null
    videoElement.value.load()
  }
  
  // 重置状态
  isStreaming.value = false
  resultFrame.value = null
  fps.value = 0
  frameCount = 0
  error.value = null
}

const startDetection = () => {
  detectionTimer = setInterval(async () => {
    await captureAndDetect()
  }, detectionInterval.value)
}

const captureAndDetect = async () => {
  const video = videoElement.value
  const canvas = canvasElement.value
  
  if (!video || !canvas || !isStreaming.value || isProcessing.value) return
  if (video.readyState < 2 || video.videoWidth === 0) {
    console.warn('视频尚未准备好，跳过本帧')
    return
  }
  
  try {
    // 绘制视频帧到画布
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    // 转换为Base64并调用检测接口
    const frameData = canvasToBase64(canvas, 'image/jpeg', 0.8)
    const response = await detectVideoFrame(frameData)
    
    if (response.success) {
      resultFrame.value = response.result_frame
      emit('detection-complete', response)
      frameCount++
    }
  } catch (err) {
    console.error('帧检测失败:', err.message)
  }
}

const startFpsCounter = () => {
  let lastCount = 0
  fpsTimer = setInterval(() => {
    fps.value = frameCount - lastCount
    lastCount = frameCount
  }, 1000)
}

// ---------------------- 本地视频检测逻辑 ----------------------
const detectLocalVideo = async () => {
  try {
    isProcessing.value = true
    processingStatus.value = '正在选择本地视频文件...'
    
    // 创建文件选择器
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'video/*'
    input.onchange = async (event) => {
      const file = event.target.files[0]
      if (!file) {
        isProcessing.value = false
        processingStatus.value = ''
        return
      }
      
      // 记录选中文件（适配原startFileDetection逻辑）
      selectedFile.value = file
      processingStatus.value = `正在检测视频: ${file.name}`
      
      try {
        // 创建中断控制器（支持停止检测）
        fileDetectionAbortController = new AbortController()
        // 调用本地视频检测API
        const response = await apiDetectLocalVideo(
          file,
          true,
          'video_results',
          { signal: fileDetectionAbortController.signal } // 传入中断信号
        )
        
        if (response.success) {
          const result = response
          processingStatus.value = `检测完成! 总帧数: ${result.total_frames}, 跌倒检测: ${result.fall_detections}`
          showLocalVideoResult(result) // 显示结果弹窗
          // 若有结果帧，更新预览
          if (result.result_frame) resultFrame.value = result.result_frame
        } else {
          processingStatus.value = `检测失败: ${response.error}`
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          processingStatus.value = '本地视频检测已手动停止'
        } else {
          console.error('本地视频检测失败:', error)
          processingStatus.value = `检测失败: ${error.message}`
        }
      } finally {
        isProcessing.value = false
        selectedFile.value = null
        fileDetectionAbortController = null
      }
    }
    
    input.click()
  } catch (error) {
    console.error('本地视频检测初始化失败:', error)
    isProcessing.value = false
    processingStatus.value = `初始化失败: ${error.message}`
  }
}

const showLocalVideoResult = (result) => {
  // 创建结果展示模态框
  const modal = document.createElement('div')
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.8); display: flex; align-items: center;
    justify-content: center; z-index: 1000;
  `
  
  const content = document.createElement('div')
  content.style.cssText = `
    background: white; padding: 20px; border-radius: 10px;
    max-width: 80%; max-height: 80%; overflow: auto;
  `
  
  // 模态框内容
  content.innerHTML = `
    <h3 style="margin-top: 0;">本地视频检测结果</h3>
    <p><strong>视频文件:</strong> ${result.video_path || '未知文件'}</p>
    <p><strong>总帧数:</strong> ${result.total_frames || 0}</p>
    <p><strong>检测目标总数:</strong> ${result.total_detections || 0}</p>
    <p><strong>跌倒检测次数:</strong> ${result.fall_detections || 0}</p>
    <p><strong>输出路径:</strong> ${result.output_path || '未保存'}</p>
    
    <h4 style="margin-top: 15px;">检测摘要</h4>
    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; border-radius: 5px;">
      ${result.detection_summary 
        ? result.detection_summary.map((frame, index) => `
            <div style="border-bottom: 1px solid #eee; padding: 8px 0; margin-bottom: 5px;">
              <strong>帧 ${frame.frame}:</strong> 检测目标 ${frame.detection_count || 0} 个，跌倒 ${frame.fall_count || 0} 次
            </div>
          `).join('') 
        : '<p style="color: #666;">无详细检测数据</p>'}
    </div>
    
    <button onclick="this.parentElement.parentElement.remove()" style="
      margin-top: 20px; padding: 10px 20px; background: #007bff; 
      color: white; border: none; border-radius: 5px; cursor: pointer;
    ">
      关闭
    </button>
  `
  
  modal.appendChild(content)
  document.body.appendChild(modal)
  
  // 点击背景关闭模态框
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove()
  })
}

// ---------------------- 文件检测逻辑（原startFileDetection） ----------------------
const startFileDetection = async () => {
  if (!selectedFile.value || isProcessing.value || isStreaming.value) return
  
  isProcessing.value = true
  processingStatus.value = `正在处理文件: ${selectedFile.value.name}`
  
  try {
    fileDetectionAbortController = new AbortController()
    
    const response = await apiDetectLocalVideo(
      selectedFile.value,
      true,
      'file_results',
      { signal: fileDetectionAbortController.signal }
    )
    
    if (response.success) {
      const result = response
      processingStatus.value = `文件检测完成: 目标数 ${result.total_detections}`
      showLocalVideoResult(result) // 复用结果弹窗
    } else {
      processingStatus.value = `文件检测失败: ${response.error}`
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      processingStatus.value = '文件检测已手动停止'
    } else {
      console.error('文件检测失败:', error)
      processingStatus.value = `文件检测失败: ${error.message}`
    }
  } finally {
    isProcessing.value = false
    selectedFile.value = null
    fileDetectionAbortController = null
  }
}

const stopFileDetection = () => {
  // 中断文件/本地视频检测
  if (fileDetectionAbortController) {
    fileDetectionAbortController.abort()
    fileDetectionAbortController = null
  }
  isProcessing.value = false
  processingStatus.value = '检测已停止'
}

const resetDetector = () => {
  // 重置所有检测状态
  stopVideo() // 停止摄像头
  stopFileDetection() // 停止文件检测
  
  // 重置所有状态变量
  selectedFile.value = null
  isProcessing.value = false
  processingStatus.value = ''
  resultFrame.value = null
  error.value = null
  fps.value = 0
  frameCount = 0
}

// 组件卸载时清理资源
onUnmounted(() => {
  stopVideo()
  stopFileDetection()
})
</script>

<style scoped>
.video-detector {
  margin-top: 30px;
  padding: 0 20px;
}

/* 检测区域布局 */
.detection-area {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  margin-bottom: 25px;
}

/* 预览框样式 */
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

/* 摄像头占位符 */
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

/* 视频/结果容器 */
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

.video-wrapper video, .result-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

/* 视频覆盖层（状态提示） */
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

/* FPS徽章 */
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

/* 空状态 */
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

/* 控制按钮区域 */
.controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.btn {
  padding: 12px 25px;
  border: none;
  border-radius: 25px;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* 按钮颜色主题 */
.btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.btn-danger { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
.btn-info { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
.btn-success { background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%); color: white; }
.btn-warning { background: linear-gradient(135deg, #ffd166 0%, #fca500 100%); color: white; }
.btn-secondary { background: linear-gradient(135deg, #6c757d 0%, #343a40 100%); color: white; }

.btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 设置项样式 */
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

/* 处理状态提示 */
.processing-status {
  margin: 10px 0;
  padding: 12px 20px;
  background: #e3f2fd;
  border: 1px solid #bbdefb;
  border-radius: 10px;
  color: #1976d2;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: center;
}

/* 错误提示 */
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

/* 动画效果 */
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.fa-spinner {
  animation: spin 1s linear infinite;
}

/* 响应式布局 */
@media (max-width: 968px) {
  .detection-area {
    grid-template-columns: 1fr;
  }
  
  .controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
  
  .settings {
    width: 100%;
    justify-content: center;
  }
}
</style>