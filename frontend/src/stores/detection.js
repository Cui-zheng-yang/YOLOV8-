// filePath：YOLOV8-/frontend/src/stores/detection.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDetectionStore = defineStore('detection', () => {
  // 状态
  const detectionHistory = ref([])
  const currentFallDetected = ref(false)
  const totalDetectionCount = ref(0)
  const totalFallCount = ref(0)
  const showFallAlert = ref(false)
  const currentPersonCount = ref(0)  // 当前检测到的人数
  const maxPersonCount = ref(0)      // 历史最大人数
  
  // 计算属性
  const recentHistory = computed(() => {
    return detectionHistory.value.slice(0, 20)
  })
  
  // 添加检测结果
  const addDetectionResult = (result) => {
    const timestamp = formatTimestamp(new Date())
    
    // 更新当前状态
    currentFallDetected.value = result.fall_detected
    totalDetectionCount.value += result.detection_count || 0
    
    // 更新人数统计
    currentPersonCount.value = result.detection_count || 0
    if (currentPersonCount.value > maxPersonCount.value) {
      maxPersonCount.value = currentPersonCount.value
    }
    
    // 处理每个检测对象
    if (result.detections && result.detections.length > 0) {
      result.detections.forEach(detection => {
        const record = {
          id: Date.now() + Math.random(),
          objectId: detection.id,  // 记录对象ID
          isFall: detection.is_fall,
          score: detection.fall_score,
          timestamp: timestamp,
          confidence: detection.confidence || 0,
          details: detection.details || {}  // 保存详细信息
        }
        
        // 添加到历史记录
        detectionHistory.value.unshift(record)
        
        // 如果检测到跌倒
        if (detection.is_fall) {
          totalFallCount.value++
          showFallAlert.value = true
          playAlertSound()
        }
      })
    }
    
    // 限制历史记录数量
    if (detectionHistory.value.length > 50) {
      detectionHistory.value = detectionHistory.value.slice(0, 50)
    }
  }
  
  // 关闭警告弹窗
  const closeFallAlert = () => {
    showFallAlert.value = false
  }
  
  // 重置统计
  const resetStats = () => {
    detectionHistory.value = []
    currentFallDetected.value = false
    totalDetectionCount.value = 0
    totalFallCount.value = 0
    currentPersonCount.value = 0
    maxPersonCount.value = 0
    showFallAlert.value = false
  }
  
  // 格式化时间戳
  const formatTimestamp = (date) => {
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
  }
  
  // 播放警报音
  const playAlertSound = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.value = 800
      oscillator.type = 'sine'
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
      
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.5)
    } catch (error) {
      console.error('音频播放失败:', error)
    }
  }
  
  return {
    // 状态
    detectionHistory,
    currentFallDetected,
    totalDetectionCount,
    totalFallCount,
    showFallAlert,
    currentPersonCount,
    maxPersonCount,
    // 计算属性
    recentHistory,
    // 方法
    addDetectionResult,
    closeFallAlert,
    resetStats
  }
})