<!-- Emergency 文件名：EmergencyContacts.vue
功能：管理紧急联系人（增删改查），提供获取联系人的方法
-->
<template>
  <div class="contacts-container">
    <div class="contacts-header">
      <h3>紧急联系人列表</h3>
      <button class="add-button" @click="addContact">+ 添加联系人</button>
    </div>

    <!-- 联系人列表 -->
    <div class="contacts-list">
      <div v-if="contacts.length === 0" class="empty-hint">
        暂无联系人，请添加
      </div>
      
      <div v-for="(contact, index) in contacts" :key="index" class="contact-item">
        <div class="contact-info">
          <div class="contact-name">{{ contact.name }}</div>
          <div class="contact-phone">{{ contact.phone }}</div>
        </div>
        <div class="contact-actions">
          <button @click="editContact(index)" class="edit-btn">编辑</button>
          <button @click="deleteContact(index)" class="delete-btn">删除</button>
        </div>
      </div>
    </div>

    <!-- 新增/编辑联系人弹窗 -->
    <div v-if="showModal" class="modal-backdrop">
      <div class="modal">
        <h4>{{ isEditing ? '编辑联系人' : '添加联系人' }}</h4>
        <div class="form-group">
          <label>姓名</label>
          <input 
            type="text" 
            v-model="currentContact.name" 
            placeholder="请输入姓名"
            required
          >
        </div>
        <div class="form-group">
          <label>电话</label>
          <input 
            type="tel" 
            v-model="currentContact.phone" 
            placeholder="请输入手机号"
            required
          >
        </div>
        <div class="modal-buttons">
          <button @click="showModal = false">取消</button>
          <button @click="saveContact">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 联系人列表（本地存储持久化）
const contacts = ref([])
// 弹窗状态
const showModal = ref(false)
const isEditing = ref(false)
const currentIndex = ref(-1)
const currentContact = ref({ name: '', phone: '' })

// 初始化：从本地存储加载联系人
onMounted(() => {
  const saved = localStorage.getItem('emergencyContacts')
  if (saved) {
    contacts.value = JSON.parse(saved)
  }
})

// 保存到本地存储
const saveToLocalStorage = () => {
  localStorage.setItem('emergencyContacts', JSON.stringify(contacts.value))
}

// 供外部调用：获取联系人列表
const getContacts = () => {
  return [...contacts.value]  // 返回副本，避免外部直接修改
}

// 添加联系人
const addContact = () => {
  isEditing.value = false
  currentContact.value = { name: '', phone: '' }
  showModal.value = true
}

// 编辑联系人
const editContact = (index) => {
  isEditing.value = true
  currentIndex.value = index
  currentContact.value = { ...contacts.value[index] }
  showModal.value = true
}

// 保存联系人（新增/编辑）
const saveContact = () => {
  if (!currentContact.value.name || !currentContact.value.phone) {
    alert('请填写姓名和电话')
    return
  }
  
  if (isEditing.value) {
    // 编辑模式
    contacts.value[currentIndex.value] = { ...currentContact.value }
  } else {
    // 新增模式
    contacts.value.push({ ...currentContact.value })
  }
  
  saveToLocalStorage()
  showModal.value = false
}

// 删除联系人
const deleteContact = (index) => {
  if (confirm('确定要删除这个联系人吗？')) {
    contacts.value.splice(index, 1)
    saveToLocalStorage()
  }
}

// 暴露方法给父组件（关键：必须暴露getContacts）
defineExpose({
  getContacts
})
</script>

<style scoped>
.contacts-container {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.contacts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.add-button {
  padding: 6px 12px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.contacts-list {
  gap: 10px;
}

.contact-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.contact-info .contact-name {
  font-weight: 500;
}

.contact-info .contact-phone {
  color: #666;
  font-size: 0.9em;
}

.contact-actions {
  display: flex;
  gap: 8px;
}

.edit-btn {
  color: #2196f3;
  background: none;
  border: none;
  cursor: pointer;
}

.delete-btn {
  color: #ff6b6b;
  background: none;
  border: none;
  cursor: pointer;
}

.empty-hint {
  color: #999;
  padding: 20px;
  text-align: center;
  border: 1px dashed #eee;
  border-radius: 4px;
}

/* 弹窗样式 */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  width: 90%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.9em;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.modal-buttons button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.modal-buttons button:first-child {
  background: #f0f0f0;
  border: none;
}

.modal-buttons button:last-child {
  background: #2196f3;
  color: white;
  border: none;
}
</style>