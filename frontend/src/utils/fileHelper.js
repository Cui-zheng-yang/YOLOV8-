/**
 * 文件处理工具函数
 */

/**
 * 将文件转换为Base64
 * @param {File} file - 文件对象
 * @returns {Promise<string>} Base64字符串
 */
export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (event) => {
      resolve(event.target.result)
    }
    
    reader.onerror = (error) => {
      reject(error)
    }
    
    reader.readAsDataURL(file)
  })
}

/**
 * 将Canvas转换为Base64
 * @param {HTMLCanvasElement} canvas - Canvas元素
 * @param {string} type - 图片类型 (image/jpeg, image/png)
 * @param {number} quality - 图片质量 (0-1)
 * @returns {string} Base64字符串
 */
export const canvasToBase64 = (canvas, type = 'image/jpeg', quality = 0.8) => {
  if (!canvas || !canvas.toDataURL) {
    throw new Error('Invalid canvas element')
  }
  return canvas.toDataURL(type, quality)
}

/**
 * 验证文件类型
 * @param {File} file - 文件对象
 * @param {string[]} allowedTypes - 允许的MIME类型数组
 * @returns {boolean}
 */
export const validateFileType = (file, allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']) => {
  if (!file || !file.type) {
    return false
  }
  return allowedTypes.includes(file.type)
}

/**
 * 验证文件大小
 * @param {File} file - 文件对象
 * @param {number} maxSize - 最大大小（字节），默认10MB
 * @returns {boolean}
 */
export const validateFileSize = (file, maxSize = 10 * 1024 * 1024) => {
  if (!file || !file.size) {
    return false
  }
  return file.size <= maxSize
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  if (!bytes) return 'Unknown'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 创建图片预览URL
 * @param {File} file - 文件对象
 * @returns {Promise<string>} 预览URL
 */
export const createImagePreview = (file) => {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('No file provided'))
      return
    }
    
    const url = URL.createObjectURL(file)
    resolve(url)
  })
}

/**
 * 释放预览URL
 * @param {string} url - 预览URL
 */
export const revokeImagePreview = (url) => {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url)
  }
}

/**
 * 压缩图片
 * @param {File} file - 原始文件
 * @param {number} maxWidth - 最大宽度
 * @param {number} maxHeight - 最大高度
 * @param {number} quality - 压缩质量
 * @returns {Promise<string>} 压缩后的Base64
 */
export const compressImage = (file, maxWidth = 1920, maxHeight = 1080, quality = 0.8) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      const img = new Image()
      
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let width = img.width
        let height = img.height
        
        // 计算缩放比例
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width *= ratio
          height *= ratio
        }
        
        canvas.width = width
        canvas.height = height
        
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, width, height)
        
        const compressed = canvas.toDataURL('image/jpeg', quality)
        resolve(compressed)
      }
      
      img.onerror = reject
      img.src = e.target.result
    }
    
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * 下载Base64图片
 * @param {string} base64 - Base64字符串
 * @param {string} filename - 文件名
 */
export const downloadBase64Image = (base64, filename = 'image.jpg') => {
  const link = document.createElement('a')
  link.href = base64
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export default {
  fileToBase64,
  canvasToBase64,
  validateFileType,
  validateFileSize,
  formatFileSize,
  createImagePreview,
  revokeImagePreview,
  compressImage,
  downloadBase64Image
}