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
 * @param {string} type - 图片类型
 * @param {number} quality - 图片质量
 * @returns {string} Base64字符串
 */
export const canvasToBase64 = (canvas, type = 'image/jpeg', quality = 0.8) => {
  return canvas.toDataURL(type, quality)
}

/**
 * 验证文件类型
 * @param {File} file - 文件对象
 * @param {string[]} allowedTypes - 允许的类型
 * @returns {boolean}
 */
export const validateFileType = (file, allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']) => {
  return allowedTypes.includes(file.type)
}

/**
 * 验证文件大小
 * @param {File} file - 文件对象
 * @param {number} maxSize - 最大大小（字节）
 * @returns {boolean}
 */
export const validateFileSize = (file, maxSize = 10 * 1024 * 1024) => {
  return file.size <= maxSize
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string}
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}