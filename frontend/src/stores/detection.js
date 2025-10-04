import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDetectionStore = defineStore('detection', () => {
  // 状态
  const detectionHistory = ref([])
  const currentFallDetected = ref(false)
  const totalDetectionCount = ref(0)
  const totalFallCount = ref(0)
  const showFallAlert = ref(false)
  const maxDetectedPeople = ref(0) // 最大检测人数
  const currentDetectionCount = ref(0) // 当前检测人数
  
  // 计算属性
  const recentHistory = computed(() => {
    return detectionHistory.value.slice(0, 20)
  })
  
  // 添加检测结果
  const addDetectionResult = (result) => {
    const timestamp = formatTimestamp(new Date())
    
    // 更新当前状态
    currentFallDetected.value = result.fall_detected
    
    // 更新检测人数统计
    const detectedCount = result.detection_count || (result.detections ? result.detections.length : 0)
    currentDetectionCount.value = detectedCount
    
    // 更新最大检测人数
    if (detectedCount > maxDetectedPeople.value) {
      maxDetectedPeople.value = detectedCount
    }
    
    // 更新总计数（使用最大值而不是累加）
    totalDetectionCount.value = maxDetectedPeople.value
    
    // 处理每个检测对象
    if (result.detections && result.detections.length > 0) {
      result.detections.forEach(detection => {
        const record = {
          id: Date.now() + Math.random(),
          isFall: detection.is_fall,
          score: detection.fall_score,
          timestamp: timestamp,
          confidence: detection.confidence || 0,
          bbox: detection.bbox || null,
          details: detection.details || {},
          resultImage: result.result_image || null // 保存检测结果图片
        }
        
        // 添加到历史记录
        detectionHistory.value.unshift(record)
        
        // 如果检测到跌倒
        if (detection.is_fall) {
          totalFallCount.value++
          showFallAlert.value = true
          playAlertSound()
          
          // 保存跌倒图片用于训练
          saveFallImageForTraining(record)
        }
      })
    }
    
    // 限制历史记录数量
    if (detectionHistory.value.length > 100) {
      detectionHistory.value = detectionHistory.value.slice(0, 100)
    }
  }
  
  // 保存跌倒图片用于训练
  const saveFallImageForTraining = async (record) => {
    try {
      // 发送到后端保存
      const response = await fetch('http://localhost:5000/api/save_fall_image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: record.resultImage,
          score: record.score,
          timestamp: record.timestamp,
          bbox: record.bbox,
          details: record.details
        })
      })
      
      if (response.ok) {
        console.log('✅ 跌倒图片已保存用于训练')
      }
    } catch (error) {
      console.error('❌ 保存跌倒图片失败:', error)
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
    maxDetectedPeople.value = 0
    currentDetectionCount.value = 0
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
    maxDetectedPeople,
    currentDetectionCount,
    // 计算属性
    recentHistory,
    // 方法
    addDetectionResult,
    closeFallAlert,
    resetStats
  }
})