import axios from 'axios'

// 创建axios实例
const request = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    if (error.response) {
      const message = error.response.data?.error || '服务器错误'
      throw new Error(message)
    } else if (error.request) {
      throw new Error('无法连接到服务器，请确保后端服务已启动')
    } else {
      throw new Error(error.message)
    }
  }
)

/**
 * 健康检查
 */
export const checkBackendHealth = () => {
  return request.get('/health')
}

/**
 * 获取系统状态
 */
export const getSystemStatus = () => {
  return request.get('/status')
}

/**
 * 图片检测
 * @param {string} imageBase64 - Base64编码的图片
 */
export const detectImage = (imageBase64) => {
  return request.post('/detect_image', {
    image: imageBase64
  })
}

/**
 * 视频帧检测
 * @param {string} frameBase64 - Base64编码的视频帧
 */
export const detectVideoFrame = (frameBase64) => {
  return request.post('/detect_video', {
    frame: frameBase64
  })
}

/**
 * 重置检测器
 * @param {number} objectId - 对象ID（可选）
 */
export const resetDetector = (objectId = null) => {
  return request.post('/reset', {
    object_id: objectId
  })
}

/**
 * 获取配置信息
 */
export const getConfig = () => {
  return request.get('/config')
}

export default request