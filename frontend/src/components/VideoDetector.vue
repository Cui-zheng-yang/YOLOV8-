<template>
  <div class="preview-box">
    <h3><i class="fas fa-video"></i> 实时视频</h3>
    <div class="video-preview">
      <video 
        ref="videoElement" 
        autoplay muted playsinline 
        style="width: 100%; height: 350px; border-radius: 10px;"
      ></video>
    </div>
    <div class="control-buttons">
      <button 
        class="btn btn-primary" 
        :disabled="isStreaming" 
        @click="startVideoStream"
      >
        <i class="fas fa-play"></i> 开始检测
      </button>
      <button 
        class="btn btn-danger" 
        :disabled="!isStreaming" 
        @click="stopVideoStream"
      >
        <i class="fas fa-stop"></i> 停止检测
      </button>
    </div>
  </div>
</template>

<script>
import { startVideoDetection, getVideoDetectionResult } from '@/api/detection';

export default {
  data() {
    return { isStreaming: false, videoStream: null, detectionInterval: null };
  },
  mounted() {
    this.setupCamera();
  },
  beforeDestroy() {
    this.stopVideoStream();
  },
  methods: {
    setupCamera() {
      const video = this.$refs.videoElement;
      if (navigator.mediaDevices?.getUserMedia) {
        navigator.mediaDevices
          .getUserMedia({ video: true })
          .then((stream) => {
            video.srcObject = stream;
            this.videoStream = stream;
          })
          .catch((err) => {
            console.error('摄像头访问失败:', err);
            alert('无法访问摄像头，请检查权限');
          });
      }
    },
    async startVideoStream() {
      this.isStreaming = true;
      try {
        await startVideoDetection(); // 通知后端开始视频检测
        // 轮询获取检测结果（每秒1次）
        this.detectionInterval = setInterval(async () => {
          try {
            const { data } = await getVideoDetectionResult();
            this.$emit('detection-result', data); // 向父组件传递结果
          } catch (err) {
            console.error('视频结果获取失败:', err);
          }
        }, 1000);
      } catch (err) {
        console.error('视频检测启动失败:', err);
        alert('启动视频检测失败');
        this.isStreaming = false;
      }
    },
    stopVideoStream() {
      this.isStreaming = false;
      if (this.detectionInterval) clearInterval(this.detectionInterval);
      // 可选：通知后端停止视频检测（若有对应API）
    },
  },
};
</script>