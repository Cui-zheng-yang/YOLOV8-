import request from './detection'

/**
 * 发起紧急呼叫
 * @param {string} phone - 电话号码
 * @param {string} latitude - 纬度
 * @param {string} longitude - 经度
 */
export const makeEmergencyCall = (phone, latitude, longitude) => {
  return request.post('/emergency/call', {
    phone,
    latitude,
    longitude
  })
}

/**
 * 发送紧急短信
 * @param {string} phone - 电话号码
 * @param {string} latitude - 纬度
 * @param {string} longitude - 经度
 */
export const sendEmergencySms = (phone, latitude, longitude) => {
  return request.post('/emergency/sms', {
    phone,
    latitude,
    longitude
  })
}