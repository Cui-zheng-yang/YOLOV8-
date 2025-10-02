<template>
  <div id="app">
    <!-- 页面头部 -->
    <div class="header">
      <h1><i class="fas fa-brain"></i> YOLOv8 行人跌倒检测系统</h1>
      <p>基于深度学习的实时跌倒监测与预警系统</p>
      <div style="margin-top: 15px;">
        <span class="feature-badge"><i class="fas fa-check"></i> 图片检测</span>
        <span class="feature-badge"><i class="fas fa-video"></i> 实时视频</span>
        <span class="feature-badge"><i class="fas fa-bell"></i> 智能预警</span>
        <span class="feature-badge"><i class="fas fa-chart-line"></i> 数据统计</span>
      </div>
    </div>

    <!-- 主内容容器 -->
    <div class="main-container">
      <!-- 模式选择器 -->
      <div class="mode-selector">
        <div 
          class="mode-btn" 
          :class="{ active: currentMode === 'image' }"
          @click="handleModeChanged('image')"
        >
          <i class="fas fa-image"></i>
          <h3>图片检测</h3>
          <p>上传图片进行分析</p>
        </div>
        <div 
          class="mode-btn" 
          :class="{ active: currentMode === 'video' }"
          @click="handleModeChanged('video')"
        >
          <i class="fas fa-video"></i>
          <h3>实时视频</h3>
          <p>摄像头实时监测</p>
        </div>
      </div>

      <!-- 检测区域 -->
      <div class="content-area">
        <!-- 左侧：根据模式显示图片上传或视频流 -->
        <div class="preview-box">
          <!-- 图片上传模式 -->
          <div v-if="currentMode === 'image'">
            <h3><i class="fas fa-upload"></i> 原始图片</h3>
            <div 
              class="upload-demo" 
              @click="openFileSelector"
              style="cursor: pointer;"
            >
              <i class="fas fa-cloud-upload-alt"></i>
              <p>点击上传图片</p>
              <small>支持 JPG, PNG 格式</small>
              <input 
                type="file" 
                ref="fileInput" 
                accept="image/jpeg, image/png" 
                @change="handleFileSelect"
                style="display: none;"
              >
            </div>
            
            <!-- 显示已选择的图片 -->
            <div v-if="selectedImage" class="selected-image">
              <img 
                :src="selectedImage" 
                alt="已选择的图片" 
                style="width: 100%; height: 350px; object-fit: contain; border-radius: 10px; margin-top: 15px;"
              >
            </div>
          </div>
          
          <!-- 视频检测模式 -->
          <div v-else>
            <h3><i class="fas fa-video"></i> 实时视频</h3>
            <div class="video-container">
              <video 
                ref="videoElement" 
                autoplay 
                muted 
                playsinline 
                style="width: 100%; height: 350px; border-radius: 10px; background-color: #000;"
                v-if="isVideoActive"
              ></video>
              <div v-else class="video-placeholder">
                <i class="fas fa-video" style="font-size: 5em; color: #667eea; margin-bottom: 20px;"></i>
                <p>点击"开始检测"启动摄像头</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧：检测结果展示 -->
        <div class="preview-box">
          <h3><i class="fas fa-search"></i> 检测结果</h3>
          <div class="result-container">
            <!-- 初始状态 -->
            <div v-if="!detectionResult" class="result-demo">
              <i class="fas fa-robot"></i>
              <p>等待检测结果...</p>
            </div>

            <!-- 检测结果展示 -->
            <div v-else class="detection-visualization">
              <img 
                :src="detectionResult.imageUrl" 
                alt="检测结果" 
                class="result-image"
              >
              <!-- 动态绘制边界框 -->
              <div 
                class="detection-bbox"
                v-for="(box, index) in detectionResult.bboxes"
                :key="index"
                :style="{
                  top: box.y + 'px',
                  left: box.x + 'px',
                  width: box.width + 'px',
                  height: box.height + 'px',
                  borderColor: box.isFall ? '#ff3e3e' : '#4CAF50'
                }"
              >
                <div class="bbox-label" :style="{
                  backgroundColor: box.isFall ? '#ff3e3e' : '#4CAF50'
                }">
                  {{ box.isFall ? '跌倒' : '正常' }} ({{ box.confidence.toFixed(2) }})
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="control-buttons">
        <button 
          class="btn btn-primary" 
          @click="handleStartDetection"
          :disabled="isProcessing"
        >
          <i class="fas fa-play"></i>
          <span>{{ isProcessing ? '处理中...' : '开始检测' }}</span>
        </button>
        <button 
          class="btn btn-danger" 
          @click="handleResetDetection"
        >
          <i class="fas fa-redo"></i>
          <span>重置</span>
        </button>
      </div>

      <!-- 统计面板 -->
      <div class="stats-panel">
        <div class="stat-card" :class="{ warning: stats.fallStatus === '跌倒' }">
          <h4>跌倒状态</h4>
          <div class="value">{{ stats.fallStatus }}</div>
        </div>
        <div class="stat-card">
          <h4>检测人数</h4>
          <div class="value">{{ stats.personCount }}</div>
        </div>
        <div class="stat-card">
          <h4>跌倒次数</h4>
          <div class="value">{{ stats.fallCount }}</div>
        </div>
      </div>

      <!-- 检测记录列表 -->
      <div class="detection-list">
        <h3><i class="fas fa-list"></i> 检测记录</h3>
        
        <div 
          class="detection-item" 
          v-for="(item, idx) in detectionRecords" 
          :key="idx"
          :class="{ fall: item.status === '跌倒' }"
        >
          <div class="detection-info">
            <strong>{{ item.status === '跌倒' ? '⚠️ 跌倒警告' : '✓ 正常状态' }}</strong>
            <p>风险评分: {{ item.riskScore.toFixed(2) }} | {{ item.time }}</p>
          </div>
          <div class="detection-icon">{{ item.status === '跌倒' ? '🚨' : '👤' }}</div>
        </div>
      </div>

      <!-- 功能说明 -->
      <div class="info-section">
        <h4><i class="fas fa-info-circle"></i> 系统功能说明</h4>
        <ul>
          <li>支持单张图片上传检测，可同时识别多人</li>
          <li>实时视频流检测，检测频率可调（默认0.5秒/次）</li>
          <li>智能跌倒判断：基于身体角度、头部高度、姿态异常三维度分析</li>
          <li>检测到跌倒时自动弹窗警告并播放警报音</li>
          <li>完整的检测历史记录，支持最近20条记录查看</li>
          <li>实时统计：跌倒状态、检测人数、累计跌倒次数</li>
        </ul>
      </div>
    </div>

    <!-- 跌倒警告弹窗 -->
    <div class="alert-modal" v-if="showFallAlert">
      <div class="alert-content">
        <div class="alert-icon">⚠️</div>
        <h3>检测到跌倒事件！</h3>
        <p>时间：{{ new Date().toLocaleString() }}</p>
        <p>位置：摄像头监控区域</p>
        <button class="alert-btn" @click="showFallAlert = false">确认</button>
      </div>
    </div>
  </div>
</template>

<script>
import { uploadImageForDetection, startVideoDetection, getVideoDetectionResult } from './api/detection';

export default {
  name: 'App',
  data() {
    return {
      // 模式状态
      currentMode: 'image', // 'image' 或 'video'
      
      // 图片相关
      selectedImage: null,
      selectedFile: null,
      
      // 视频相关
      isVideoActive: false,
      videoStream: null,
      videoPollingId: null,
      
      // 检测结果
      detectionResult: null,
      
      // 处理状态
      isProcessing: false,
      
      // 统计数据
      stats: {
        fallStatus: '正常',
        personCount: 0,
        fallCount: 0
      },
      
      // 检测记录
      detectionRecords: [],
      
      // 警告状态
      showFallAlert: false
    };
  },
  methods: {
    // 处理模式切换
    handleModeChanged(mode) {
      this.currentMode = mode;
      this.handleResetDetection();
    },
    
    // 打开文件选择器
    openFileSelector() {
      if (this.currentMode === 'image') {
        this.$refs.fileInput.click();
      }
    },
    
    // 处理文件选择
    handleFileSelect(e) {
      const file = e.target.files[0];
      if (file) {
        this.selectedFile = file;
        // 预览图片
        const reader = new FileReader();
        reader.onload = (event) => {
          this.selectedImage = event.target.result;
        };
        reader.readAsDataURL(file);
      }
    },
    
    // 处理检测结果
    handleDetectionResult(result) {
      this.detectionResult = result;
      this.isProcessing = false;
      
      // 更新统计数据
      this.stats.personCount = result.bboxes.length;
      const hasFall = result.bboxes.some(box => box.isFall);
      this.stats.fallStatus = hasFall ? '跌倒' : '正常';
      
      // 如果有跌倒，更新计数并显示警告
      if (hasFall) {
        this.stats.fallCount += 1;
        this.showFallAlert = true;
      }
      
      // 添加到记录列表
      this.addDetectionRecord(result, hasFall);
    },
    
    // 添加检测记录
    addDetectionRecord(result, hasFall) {
      const newRecord = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        status: hasFall ? '跌倒' : '正常',
        riskScore: result.bboxes.reduce((sum, box) => sum + (box.isFall ? box.confidence : 0), 0) / (result.bboxes.length || 1),
        personCount: result.bboxes.length
      };
      
      // 保持最新20条记录
      this.detectionRecords.unshift(newRecord);
      if (this.detectionRecords.length > 20) {
        this.detectionRecords.pop();
      }
    },
    
    // 开始检测
    async handleStartDetection() {
      this.isProcessing = true;
      
      if (this.currentMode === 'image') {
        // 图片检测
        if (!this.selectedFile) {
          alert('请先上传图片');
          this.isProcessing = false;
          return;
        }
        
        try {
          const formData = new FormData();
          formData.append('image', this.selectedFile);
          const response = await uploadImageForDetection(formData);
          this.handleDetectionResult(response.data);
        } catch (error) {
          console.error('图片检测失败:', error);
          alert('检测失败: ' + (error.response?.data?.message || error.message));
          this.isProcessing = false;
        }
      } else {
        // 视频检测
        try {
          // 启动摄像头
          if (!this.isVideoActive) {
            this.videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.$refs.videoElement.srcObject = this.videoStream;
            this.isVideoActive = true;
          }
          
          // 通知后端开始视频检测
          await startVideoDetection();
          
          // 轮询获取检测结果
          this.videoPollingId = setInterval(async () => {
            try {
              const response = await getVideoDetectionResult();
              this.handleDetectionResult(response.data);
            } catch (error) {
              console.error('获取视频检测结果失败:', error);
            }
          }, 1000); // 每秒获取一次结果
          
          this.isProcessing = false;
        } catch (error) {
          console.error('视频检测启动失败:', error);
          alert('启动摄像头失败: ' + error.message);
          this.isVideoActive = false;
          this.isProcessing = false;
        }
      }
    },
    
    // 重置检测
    handleResetDetection() {
      // 重置状态
      this.selectedImage = null;
      this.selectedFile = null;
      this.detectionResult = null;
      this.isProcessing = false;
      
      // 重置文件输入
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
      
      // 停止视频
      if (this.videoStream) {
        this.videoStream.getTracks().forEach(track => track.stop());
        this.videoStream = null;
        this.isVideoActive = false;
      }
      
      // 清除轮询
      if (this.videoPollingId) {
        clearInterval(this.videoPollingId);
        this.videoPollingId = null;
      }
      
      // 重置统计（保留总跌倒次数）
      this.stats = {
        ...this.stats,
        fallStatus: '正常',
        personCount: 0
      };
    }
  },
  beforeUnmount() {
    // 组件卸载时清理资源
    this.handleResetDetection();
  }
};
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
  animation: fadeInDown 0.8s ease;
}

.header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header p {
  font-size: 1.2em;
  opacity: 0.9;
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: fadeInUp 0.8s ease;
}

.mode-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.mode-btn {
  padding: 30px;
  border: 3px solid #e0e0e0;
  border-radius: 15px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.mode-btn:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.mode-btn.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.mode-btn i {
  font-size: 3em;
  display: block;
  margin-bottom: 15px;
}

.mode-btn h3 {
  font-size: 1.5em;
  margin-bottom: 8px;
}

.mode-btn p {
  font-size: 1em;
  opacity: 0.8;
}

.content-area {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-top: 30px;
}

.preview-box {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 25px;
  min-height: 450px;
  display: flex;
  flex-direction: column;
  border: 2px dashed #ccc;
}

.preview-box h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.5em;
  text-align: center;
}

.upload-demo {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.upload-demo:hover {
  background: #e9ecef;
}

.upload-demo i {
  font-size: 5em;
  color: #667eea;
  margin-bottom: 20px;
}

.upload-demo p {
  color: #666;
  font-size: 1.2em;
  margin-bottom: 10px;
}

.upload-demo small {
  color: #999;
}

.video-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  height: 350px;
}

.result-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
  min-height: 350px;
}

.result-demo {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
}

.result-demo i {
  font-size: 4em;
  color: #999;
  margin-bottom: 15px;
}

.result-demo p {
  color: #999;
  font-size: 1.1em;
}

.result-image {
  width: 100%;
  height: 350px;
  object-fit: contain;
  background-color: #f5f5f5;
}

.detection-visualization {
  position: relative;
  width: 100%;
  height: 350px;
}

.detection-bbox {
  position: absolute;
  border: 2px solid;
  box-sizing: border-box;
}

.bbox-label {
  position: absolute;
  top: -25px;
  left: 0;
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
}

.control-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 25px;
}

.btn {
  padding: 15px 40px;
  border: none;
  border-radius: 25px;
  font-size: 1.1em;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-weight: 500;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
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

.stats-panel {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.stat-card.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  animation: pulse 1.5s infinite;
}

.stat-card h4 {
  font-size: 1em;
  opacity: 0.9;
  margin-bottom: 12px;
  font-weight: normal;
}

.stat-card .value {
  font-size: 2.5em;
  font-weight: bold;
}

.detection-list {
  margin-top: 30px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 10px;
}

.detection-list h3 {
  color: #333;
  margin-bottom: 15px;
  font-size: 1.3em;
}

.detection-item {
  background: white;
  padding: 18px;
  margin-bottom: 12px;
  border-radius: 10px;
  border-left: 4px solid #667eea;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detection-item.fall {
  border-left-color: #f5576c;
  background: #fff5f5;
}

.detection-info strong {
  display: block;
  font-size: 1.1em;
  margin-bottom: 5px;
}

.detection-info p {
  color: #666;
  font-size: 0.9em;
}

.detection-icon {
  font-size: 2.5em;
}

.feature-badge {
  display: inline-block;
  background: #4CAF50;
  color: white;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.9em;
  margin: 5px;
  animation: fadeInUp 1s ease;
}

.info-section {
  background: #e3f2fd;
  padding: 20px;
  border-radius: 10px;
  margin-top: 30px;
  border-left: 4px solid #2196F3;
}

.info-section h4 {
  color: #1976D2;
  margin-bottom: 10px;
}

.info-section ul {
  list-style: none;
  padding-left: 0;
}

.info-section li {
  padding: 5px 0;
  color: #555;
}

.info-section li:before {
  content: "✓ ";
  color: #4CAF50;
  font-weight: bold;
  margin-right: 8px;
}

.alert-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

.alert-content {
  background-color: white;
  padding: 30px;
  border-radius: 15px;
  text-align: center;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
}

.alert-icon {
  font-size: 50px;
  color: #ff3e3e;
  margin-bottom: 20px;
}

.alert-btn {
  margin-top: 20px;
  padding: 10px 30px;
  background-color: #ff3e3e;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>