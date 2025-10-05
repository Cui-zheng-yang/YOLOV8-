<template>
  <div v-if="store.showFallAlert" class="fall-alert-backdrop">
    <!-- 核心弹窗容器 -->
    <div class="fall-alert-container" :class="{ 'expanded': showSmsEditor }">
      <!-- 原弹窗内容（默认显示） -->
      <div v-if="!showSmsEditor">
        <!-- 头部 -->
        <div class="alert-header">
          <h2>⚠️ 检测到跌倒</h2>
          <p>已自动定位，建议立即采取行动</p>
        </div>

        <!-- 位置信息 -->
        <div class="location-info">
          <p>位置：{{ latitude }}, {{ longitude }}</p>
          <p>{{ locationText }}</p>
        </div>

        <!-- 操作按钮区 -->
        <div class="action-buttons">
          <button 
            class="call-btn" 
            @click="handleCallClick"
            :disabled="isProcessing && actionType === 'call'"
          >
            <i class="fas fa-phone"></i>
            {{ isProcessing && actionType === 'call' ? '呼叫中...' : '呼叫紧急联系人' }}
          </button>
          <button 
            class="sms-btn" 
            @click="handleSmsClick"
            :disabled="isProcessing && actionType === 'sms'"
          >
            <i class="fas fa-comment"></i>
            {{ isProcessing && actionType === 'sms' ? '发送中...' : '发送紧急短信' }}
          </button>
          <button 
            class="cancel-btn" 
            @click="handleCancel"
          >
            <i class="fas fa-times"></i>
            取消
          </button>
        </div>

        <!-- 联系人管理区域 -->
        <div class="contacts-section">
          <button class="settings-toggle" @click="showSettings = !showSettings">
            <i class="fas fa-cog"></i>
            <span>紧急联系人设置</span>
            <i class="fas" :class="showSettings ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
          </button>
          
          <transition name="slide-down">
            <div v-show="showSettings" class="contacts-form">
              <EmergencyContacts ref="contactsComponentRef" />
            </div>
          </transition>
        </div>
      </div>

      <!-- 短信编辑界面（点击发送短信时显示） -->
      <div v-if="showSmsEditor" class="sms-editor">
        <!-- 编辑界面头部 -->
        <div class="editor-header">
          <button class="back-btn" @click="showSmsEditor = false">
            <i class="fas fa-arrow-left"></i> 返回
          </button>
          <h2>编辑紧急短信</h2>
        </div>

        <!-- 接收人信息 -->
        <div class="recipient-info">
          <p>接收人：{{ smsRecipientName }}（{{ smsRecipientPhone }}）</p>
        </div>

        <!-- 短信内容编辑区 -->
        <div class="sms-content">
          <textarea 
            v-model="smsContent" 
            placeholder="请输入紧急信息..."
            maxlength="200"
          ></textarea>
          <div class="char-count">{{ smsContent.length }}/200</div>
        </div>

        <!-- 位置信息（只读） -->
        <div class="location-preview">
          <p><i class="fas fa-map-marker-alt"></i> 位置信息：</p>
          <p>{{ latitude }}, {{ longitude }}</p>
        </div>

        <!-- 编辑界面操作按钮 -->
        <div class="editor-actions">
          <button class="cancel-editor-btn" @click="showSmsEditor = false">
            取消
          </button>
          <button class="confirm-send-btn" @click="handleConfirmSend">
            <i class="fas fa-paper-plane"></i> 确认发送
          </button>
        </div>
      </div>

      <!-- 提示消息 -->
      <div v-if="showToast" class="toast" :class="toastType">
        {{ toastMessage }}
      </div>
    </div>

    <!-- 全屏通话界面 -->
    <div v-if="isInCall" class="fullscreen-call">
      <!-- 通话界面内容不变 -->
      <div class="call-status-bar">
        <span class="signal-icon">📶</span>
        <span class="time">{{ currentTime }}</span>
        <span class="battery-icon">🔋</span>
      </div>
      <div class="call-content">
        <div class="contact-avatar">
          <div class="avatar-inner">{{ currentCallName.charAt(0) }}</div>
        </div>
        <div class="contact-info">
          <h3 class="contact-name">{{ currentCallName }}</h3>
          <p class="contact-number">{{ currentCallNumber }}</p>
          <p class="call-status">正在呼叫中...</p>
        </div>
        <div class="call-timer">{{ callDuration }}</div>
      </div>
      <div class="call-actions">
        <button class="action-btn speaker-btn" @click="toggleSpeaker">
          <i class="fas fa-volume-up"></i>
          <span>扬声器</span>
        </button>
        <button class="action-btn keypad-btn" @click="toggleKeypad">
          <i class="fas fa-keyboard"></i>
          <span>键盘</span>
        </button>
        <button class="action-btn mute-btn" @click="toggleMute">
          <i class="fas" :class="isMuted ? 'fa-microphone-slash' : 'fa-microphone'"></i>
          <span>{{ isMuted ? '取消静音' : '静音' }}</span>
        </button>
        <button class="action-btn end-call-btn" @click="endCall">
          <i class="fas fa-phone-slash"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useDetectionStore } from '../stores/detection'
import EmergencyContacts from './EmergencyContacts.vue'
import { makeEmergencyCall, sendEmergencySms } from '../api/emergency'

// 状态管理
const store = useDetectionStore()
const contactsComponentRef = ref(null)

// 新增：短信编辑相关状态
const showSmsEditor = ref(false) // 控制编辑界面显示/隐藏
const smsRecipientPhone = ref('') // 接收人电话
const smsRecipientName = ref('') // 接收人姓名
const smsContent = ref('') // 短信内容
const defaultSmsTemplate = ref('【紧急通知】检测到行人跌倒，位置：{latitude},{longitude}，请尽快处理！')

// 原有状态
const showSettings = ref(false)
const isInCall = ref(false)
const currentCallNumber = ref('')
const currentCallName = ref('')
const callDuration = ref('00:00')
const callStartTime = ref(null)
let callTimer = null

const isMuted = ref(false)
const isSpeakerOn = ref(false)
const showKeypad = ref(false)
const currentTime = ref('')

const latitude = ref('36.306700')
const longitude = ref('113.075500')
const locationText = ref('检测到行人跌倒，请立即处理')

const isProcessing = ref(false)
const actionType = ref('')
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

// 取消按钮处理
const handleCancel = () => {
  store.showFallAlert = false
  if (store.setShowFallAlert) store.setShowFallAlert(false)
  if (isInCall.value) endCall()
}

// 监视联系人组件加载
watch(
  () => contactsComponentRef.value,
  (newVal) => {
    if (newVal) console.log('联系人组件加载成功')
  }
)

// 获取地理位置
const getLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        latitude.value = position.coords.latitude.toFixed(6)
        longitude.value = position.coords.longitude.toFixed(6)
      },
      (error) => {
        console.error('位置获取失败:', error.message)
        showToastMessage('无法获取精确位置，使用默认位置', 'warning')
      }
    )
  } else {
    showToastMessage('浏览器不支持位置获取，使用默认位置', 'warning')
  }
}

// 显示提示消息
const showToastMessage = (message, type = 'info') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => showToast.value = false, 3000)
}

// 呼叫按钮点击
const handleCallClick = () => {
  nextTick(() => makeEmergencyCallHandler())
}

// 发送短信按钮点击（改为显示编辑界面）
const handleSmsClick = () => {
  console.log('发送短信按钮被点击，显示编辑界面')
  nextTick(() => prepareSmsEditor())
}

// 新增：准备短信编辑界面
const prepareSmsEditor = async () => {
  if (!contactsComponentRef.value) {
    showToastMessage('系统错误：无法获取联系人组件', 'error')
    return
  }

  let contactsList
  try {
    contactsList = contactsComponentRef.value.getContacts()
    console.log('获取到的联系人列表:', contactsList)
  } catch (err) {
    console.error('调用getContacts()失败:', err.message)
    showToastMessage('系统错误：无法获取联系人信息', 'error')
    return
  }

  if (!contactsList || contactsList.length === 0) {
    showToastMessage('请先设置紧急联系人', 'error')
    showSettings.value = true
    return
  }

  if (!latitude.value || !longitude.value) {
    showToastMessage('正在获取位置信息，请稍候', 'info')
    return
  }

  // 填充接收人信息和默认短信内容
  const targetContact = contactsList[0]
  smsRecipientPhone.value = targetContact.phone
  smsRecipientName.value = targetContact.name
  // 替换模板中的位置信息
  smsContent.value = defaultSmsTemplate.value
    .replace('{latitude}', latitude.value)
    .replace('{longitude}', longitude.value)

  // 显示编辑界面
  showSmsEditor.value = true
}

// 新增：确认发送短信
const handleConfirmSend = async () => {
  if (!smsContent.value.trim()) {
    showToastMessage('短信内容不能为空', 'error')
    return
  }

  isProcessing.value = true
  actionType.value = 'sms'

  try {
    const response = await sendEmergencySms(
      smsRecipientPhone.value,
      latitude.value,
      longitude.value,
      smsContent.value // 传递编辑后的内容
    )

    if (response.success) {
      showToastMessage(`已向 ${smsRecipientName.value} 发送紧急短信`, 'success')
      showSmsEditor.value = false // 隐藏编辑界面
    } else {
      throw new Error(response.error || '发送失败')
    }
  } catch (error) {
    console.error('短信发送失败:', error.message)
    // 备用方案：尝试系统短信
    try {
      const smsUrl = `sms:${smsRecipientPhone.value}?body=${encodeURIComponent(smsContent.value)}`
      window.location.href = smsUrl
      showToastMessage(`正在发送短信给 ${smsRecipientPhone.value}`, 'success')
      showSmsEditor.value = false
    } catch (smsError) {
      showToastMessage(`发送失败：${smsError.message}`, 'error')
    }
  } finally {
    isProcessing.value = false
    actionType.value = ''
  }
}

// 通话功能
const toggleMute = () => {
  isMuted.value = !isMuted.value
  showToastMessage(isMuted.value ? '已静音' : '取消静音', 'info')
}

const toggleSpeaker = () => {
  isSpeakerOn.value = !isSpeakerOn.value
  showToastMessage(isSpeakerOn.value ? '扬声器已开启' : '扬声器已关闭', 'info')
}

const toggleKeypad = () => {
  showKeypad.value = !showKeypad.value
}

const startCallTimer = () => {
  callStartTime.value = new Date()
  callTimer = setInterval(() => {
    const now = new Date()
    const diff = Math.floor((now - callStartTime.value) / 1000)
    const minutes = Math.floor(diff / 60).toString().padStart(2, '0')
    const seconds = (diff % 60).toString().padStart(2, '0')
    callDuration.value = `${minutes}:${seconds}`
  }, 1000)
}

const endCall = () => {
  isInCall.value = false
  if (callTimer) clearInterval(callTimer)
  callStartTime.value = null
  currentCallNumber.value = ''
  currentCallName.value = ''
  isProcessing.value = false
  actionType.value = ''
  showToastMessage('通话已结束', 'info')
}

// 紧急呼叫处理
const makeEmergencyCallHandler = async () => {
  if (!contactsComponentRef.value) {
    showToastMessage('系统错误：无法获取联系人组件', 'error')
    return
  }

  let contactsList
  try {
    contactsList = contactsComponentRef.value.getContacts()
  } catch (err) {
    showToastMessage('系统错误：无法获取联系人信息', 'error')
    return
  }

  if (!contactsList || contactsList.length === 0) {
    showToastMessage('请先设置紧急联系人', 'error')
    showSettings.value = true
    return
  }

  if (!latitude.value || !longitude.value) {
    showToastMessage('正在获取位置信息，请稍候', 'info')
    return
  }

  isProcessing.value = true
  actionType.value = 'call'
  const targetContact = contactsList[0]

  try {
    currentCallNumber.value = targetContact.phone
    currentCallName.value = targetContact.name
    isInCall.value = true
    startCallTimer()

    const response = await makeEmergencyCall(
      targetContact.phone,
      latitude.value,
      longitude.value
    )

    if (!response.success) throw new Error(response.error || '呼叫失败')
  } catch (error) {
    console.error('呼叫API失败:', error.message)
    try {
      const telUrl = `tel:${targetContact.phone}`
      window.location.href = telUrl
    } catch (telError) {
      showToastMessage(`呼叫失败：${telError.message}`, 'error')
      endCall()
    }
  }
}

// 初始化
onMounted(() => {
  getLocation()
  
  const updateCurrentTime = () => {
    const now = new Date()
    currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  }
  updateCurrentTime()
  setInterval(updateCurrentTime, 60000)

  const checkContactsComponent = () => {
    if (contactsComponentRef.value) {
      console.log('联系人组件加载成功')
    } else {
      setTimeout(checkContactsComponent, 1000)
    }
  }
  checkContactsComponent()

  if (typeof store.showFallAlert === 'undefined') {
    store.showFallAlert = true
  }
})
</script>

<style scoped>
/* 原有样式基础上新增以下样式 */

/* 弹窗扩展样式（编辑界面显示时） */
.fall-alert-container {
  transition: max-height 0.3s ease;
  max-height: 600px; /* 默认高度 */
}

.fall-alert-container.expanded {
  max-height: 800px; /* 编辑界面显示时的高度 */
}

/* 短信编辑界面样式 */
.sms-editor {
  padding: 15px 0;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.back-btn {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.recipient-info {
  background: #f8f9fa;
  padding: 12px 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  color: #666;
  font-size: 14px;
}

.sms-content {
  margin-bottom: 15px;
}

.sms-content textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: vertical;
  font-size: 15px;
  line-height: 1.5;
}

.sms-content textarea:focus {
  outline: none;
  border-color: #3498db;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.location-preview {
  background: #f8f9fa;
  padding: 12px 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
}

.location-preview p:first-child {
  margin: 0 0 8px 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 5px;
}

.location-preview p:last-child {
  margin: 0;
  font-family: monospace;
  color: #666;
}

.editor-actions {
  display: flex;
  gap: 10px;
}

.cancel-editor-btn {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.confirm-send-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: #3498db;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

/* 其他原有样式保持不变 */
.fall-alert-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.fall-alert-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.alert-header {
  text-align: center;
  margin-bottom: 20px;
}

.alert-header h2 {
  color: #e74c3c;
  margin: 0 0 10px 0;
  font-size: 22px;
}

.alert-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.location-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.location-info p {
  margin: 5px 0;
  color: #333;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-buttons button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.call-btn {
  background: #2ecc71;
  color: white;
}

.sms-btn {
  background: #3498db;
  color: white;
}

.cancel-btn {
  background: #e74c3c;
  color: white;
}

.contacts-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.settings-toggle {
  width: 100%;
  background: #f1f5f9;
  border: none;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #333;
}

.contacts-form {
  margin-top: 15px;
  animation: slideDown 0.3s ease;
}

.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  z-index: 3000;
}

.toast.info { background: #3498db; }
.toast.success { background: #2ecc71; }
.toast.error { background: #e74c3c; }
.toast.warning { background: #f39c12; }

/* 通话界面样式保持不变 */
.fullscreen-call {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #1a237e 0%, #121212 100%);
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 2000;
}

.fall-alert-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.fall-alert-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* 头部样式（保留原有） */
.alert-header {
  text-align: center;
  margin-bottom: 20px;
}

.alert-header h2 {
  color: #e74c3c;
  margin: 0 0 10px 0;
  font-size: 22px;
}

.alert-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.fall-alert-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.fall-alert-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* 头部样式（保留原有） */
.alert-header {
  text-align: center;
  margin-bottom: 20px;
}

.alert-header h2 {
  color: #e74c3c;
  margin: 0 0 10px 0;
  font-size: 22px;
}

.alert-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

/* 位置信息样式 */
.location-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.location-info p {
  margin: 5px 0;
  color: #333;
  font-size: 14px;
}

/* 按钮样式 */
.action-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-buttons button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: opacity 0.2s;
}

.call-btn {
  background: #2ecc71;
  color: white;
}

.sms-btn {
  background: #3498db;
  color: white;
}

.cancel-btn {
  background: #e74c3c;
  color: white;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 联系人区域样式 */
.contacts-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.settings-toggle {
  width: 100%;
  background: #f1f5f9;
  border: none;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #333;
}

.contacts-form {
  margin-top: 15px;
  animation: slideDown 0.3s ease;
}

/* 提示消息样式 */
.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  z-index: 3000;
}

.toast.info { background: #3498db; }
.toast.success { background: #2ecc71; }
.toast.error { background: #e74c3c; }
.toast.warning { background: #f39c12; }

/* 全屏通话界面样式（美化后） */
.fullscreen-call {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #1a237e 0%, #121212 100%);
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 2000;
}

/* 通话顶部状态条 */
.call-status-bar {
  height: 44px;
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  opacity: 0.9;
}

/* 通话主体内容 */
.call-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
}

/* 联系人头像 */
.contact-avatar {
  width: 160px;
  height: 160px;
  margin-bottom: 30px;
  position: relative;
}

.avatar-inner {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #4a148c, #880e4f);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60px;
  font-weight: bold;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.avatar-inner::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  70% { transform: scale(1.2); opacity: 0; }
  100% { transform: scale(1); opacity: 0; }
}

/* 联系人信息 */
.contact-info {
  text-align: center;
  margin-bottom: 40px;
}

.contact-name {
  font-size: 28px;
  margin: 0 0 8px 0;
  font-weight: 500;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.contact-number {
  font-size: 16px;
  color: #e0e0e0;
  margin: 0 0 12px 0;
  opacity: 0.9;
}

.call-status {
  font-size: 14px;
  color: #bb86fc;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.call-status::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #00e676;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 通话时长 */
.call-timer {
  font-size: 42px;
  font-weight: 300;
  color: #f5f5f5;
  letter-spacing: 2px;
  margin-top: 20px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

/* 通话操作区 */
.call-actions {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px 10px;
  background-color: rgba(18, 18, 18, 0.6);
  backdrop-filter: blur(10px);
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn span {
  font-size: 12px;
  margin-top: 8px;
}

.action-btn:not(.end-call-btn):hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.speaker-btn { background-color: rgba(66, 165, 245, 0.2); }
.keypad-btn { background-color: rgba(76, 175, 80, 0.2); }
.mute-btn { background-color: rgba(255, 152, 0, 0.2); }

.end-call-btn {
  width: 72px;
  height: 72px;
  background-color: #e53935;
  box-shadow: 0 4px 15px rgba(229, 57, 53, 0.4);
}

.end-call-btn:hover {
  background-color: #d32f2f;
  transform: scale(1.1);
}

/* 动画与响应式 */
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 375px) {
  .contact-avatar { width: 140px; height: 140px; }
  .contact-name { font-size: 24px; }
  .call-timer { font-size: 36px; }
  .action-btn { width: 56px; height: 56px; }
  .end-call-btn { width: 64px; height: 64px; }
}
</style>