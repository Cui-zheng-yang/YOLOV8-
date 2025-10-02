<template>
  <div class="preview-box">
    <h3><i class="fas fa-upload"></i> 原始图片</h3>
    <div class="upload-demo" @click="openFileSelector">
      <i class="fas fa-cloud-upload-alt"></i>
      <p>点击上传图片</p>
      <small>支持 JPG, PNG 格式</small>
      <input 
        type="file" 
        ref="fileInput" 
        accept="image/jpeg, image/png" 
        @change="handleFileSelect"
        class="hidden"
      >
    </div>
    <div v-if="selectedImage" class="selected-image-preview">
      <img :src="selectedImage" alt="Selected Image" style="width: 100%; height: auto; border-radius: 10px;">
    </div>
    <div class="control-buttons" v-if="selectedImage">
      <button class="btn btn-primary" @click="detectImage">
        <i class="fas fa-play"></i> 开始检测
      </button>
      <button class="btn btn-danger" @click="resetImage">
        <i class="fas fa-redo"></i> 重置
      </button>
    </div>
  </div>
</template>

<script>
import { uploadImageForDetection } from '@/api/detection';

export default {
  data() {
    return { selectedImage: null, file: null };
  },
  methods: {
    openFileSelector() {
      this.$refs.fileInput.click();
    },
    handleFileSelect(e) {
      const file = e.target.files[0];
      if (file) {
        this.file = file;
        const reader = new FileReader();
        reader.onload = (event) => {
          this.selectedImage = event.target.result;
        };
        reader.readAsDataURL(file);
      }
    },
    async detectImage() {
      if (!this.file) return;
      const formData = new FormData();
      formData.append('image', this.file);
      try {
        const { data } = await uploadImageForDetection(formData);
        this.$emit('detection-result', data); // 向父组件传递检测结果
      } catch (error) {
        console.error('图片检测失败:', error);
        alert('检测失败，请重试');
      }
    },
    resetImage() {
      this.selectedImage = null;
      this.file = null;
      this.$refs.fileInput.value = '';
    },
  },
};
</script>

<style scoped>
.hidden { display: none; }
.selected-image-preview { margin-top: 20px; }
</style>