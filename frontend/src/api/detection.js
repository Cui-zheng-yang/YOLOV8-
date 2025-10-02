import axios from 'axios';

const API_BASE_URL = 'http://0.0.0.0:5000/api';

/** 上传图片检测 */
export const uploadImageForDetection = (formData) => {
  return axios.post(`${API_BASE_URL}/image-detect`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

/** 启动视频检测（通知后端） */
export const startVideoDetection = () => {
  return axios.post(`${API_BASE_URL}/video-start`);
};

/** 获取视频检测结果（轮询用） */
export const getVideoDetectionResult = () => {
  return axios.get(`${API_BASE_URL}/video-result`);
};

/** 获取检测历史 */
export const getDetectionHistory = () => {
  return axios.get(`${API_BASE_URL}/detection-history`);
};