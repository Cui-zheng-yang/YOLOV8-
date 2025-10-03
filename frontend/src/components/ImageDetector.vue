<template>
  <div class="image-detector">
    <!-- 检测区域 -->
    <div class="detection-area">
      <!-- 原始图片区 -->
      <div class="preview-box">
        <h3><i class="fas fa-upload"></i> 原始图片</h3>
        <div 
          v-if="!originalImage" 
          class="upload-zone"
          @click="triggerFileInput"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
          :class="{ 'drag-over': isDragging }"
        >
          <i class="fas fa-cloud-upload-alt"></i>
          <p class="upload-text">点击或拖拽上传图片</p>
          <small>支持 JPG, PNG 格式，最大 10MB</small>
        </div>
        <div v-else class="image-preview">
          <img :src="originalImage" alt="原始图片" />
          <button class="remove-btn" @click="removeImage">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <input 
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/jpg"
          @change="handleFileSelect"
          style="display: none"
        />
      </div>

      <!-- 检测结果区 -->
      <div class="preview-box">
        <h3><i class="fas fa-search"></i> 检测结果</h3>
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>正在检测中...</p>
          <small>请稍候</small>
        </div>
        <div v-else-if="!resultImage" class="empty-state">
          <i class="fas fa-image"></i>
          <p>等待检测结果</p>
        </div>
        <div v-else class="image-preview">
          <img :src="resultImage" alt="检测结果" />
        </div>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="controls">
      <button 
        class="btn btn-primary"
        :disabled="!originalImage || loading"
        @click="startDetection"
      >
        <i class="fas fa-play"></i>
        {{ loading ? '检测中...' : '开始检测' }}
      </button>
      <button 
        class="btn btn-secondary"
        :disabled="!originalImage"
        @click="reset"
      >
        <i class="fas fa-redo"></i>
        重置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { detectImage } from '@/api/detection'
import { fileToBase64, validateFileType, validateFileSize } from '@/utils/fileHelper'

const emit = defineEmits(['detection-complete'])

const fileInput = ref(null)
const originalImage = ref(null)
const resultImage = ref(null)
const loading = ref(false)
const isDragging = ref(false)

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (file) {
    await processFile(file)
  }
}

// 处理文件
const processFile = async (file) => {
  // 验证文件类型
  if (!validateFileType(file)) {
    alert('请上传 JPG 或 PNG 格式的图片！')
    return
  }
  
  // 验证文件大小
  if (!validateFileSize(file)) {
    alert('图片大小不能超过 10MB！')
    return
  }
  
  try {
    const base64 = await fileToBase64(file)
    originalImage.value = base64
    resultImage.value = null
  } catch (error) {
    console.error('文件读取失败:', error)
    alert('文件读取失败，请重试！')
  }
}

// 拖拽相关
const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = () => {
  isDragging.value = false
}

const onDrop = async (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    await processFile(file)
  }
}

// 移除图片
const removeImage = () => {
  originalImage.value = null
  resultImage.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 开始检测
const startDetection = async () => {
  if (!originalImage.value || loading.value) return
  
  loading.value = true
  resultImage.value = null
  
  try {
    const response = await detectImage(originalImage.value)
    
    if (response.success) {
      resultImage.value = response.result_image
      emit('detection-complete', response)
      
      if (response.fall_detected) {
        console.log('⚠️ 检测到跌倒！')
      }
    } else {
      alert('检测失败：' + (response.error || '未知错误'))
    }
  } catch (error) {
    console.error('检测错误:', error)
    alert('检测失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 重置
const reset = () => {
  removeImage()
}
</script>

<style scoped>
.image-detector {
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

.upload-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px dashed #ccc;
}

.upload-zone:hover, .upload-zone.drag-over {
  background: #f0f0f0;
  border-color: #667eea;
}

.upload-zone i {
  font-size: 5em;
  color: #667eea;
  margin-bottom: 20px;
}

.upload-text {
  font-size: 1.2em;
  color: #666;
  margin-bottom: 10px;
}

.upload-zone small {
  color: #999;
}

.image-preview {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: white;
  border-radius: 10px;
  overflow: hidden;
}

.image-preview img {
  max-width: 100%;
  max-height: 450px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 0, 0, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  width: 35px;
  height: 35px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.2em;
}

.remove-btn:hover {
  background: rgba(255, 0, 0, 1);
  transform: scale(1.1);
}

.loading-state, .empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(102, 126, 234, 0.2);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p, .empty-state p {
  font-size: 1.2em;
  margin-bottom: 5px;
}

.loading-state small {
  color: #bbb;
}

.empty-state i {
  font-size: 4em;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  gap: 15px;
  justify-content: center;
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

.btn-secondary {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
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