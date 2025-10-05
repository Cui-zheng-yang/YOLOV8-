from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from config import get_config  # 改为导入获取配置实例的函数

# 获取配置实例（而非配置字典）
config = get_config()

logger = logging.getLogger(__name__)
emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/emergency/call', methods=['POST'])
def emergency_call():
    """处理紧急呼叫请求"""
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not all(k in data for k in ['phone', 'latitude', 'longitude']):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        phone = data['phone']
        latitude = data['latitude']
        longitude = data['longitude']

        # 模拟呼叫过程
        logger.info(f"紧急呼叫: {phone}，位置: {latitude},{longitude}")
        
        # 返回模拟成功响应
        return jsonify({
            'success': True,
            'message': f'已发起对 {phone} 的紧急呼叫',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"紧急呼叫处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500

@emergency_bp.route('/emergency/sms', methods=['POST'])
def emergency_sms():
    """处理紧急短信请求"""
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not all(k in data for k in ['phone', 'latitude', 'longitude']):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        phone = data['phone']
        latitude = data['latitude']
        longitude = data['longitude']
        
        # 生成短信内容（现在可以正确访问配置实例的属性）
        message = config.EMERGENCY_MESSAGE_TEMPLATE.format(
            latitude=latitude,
            longitude=longitude
        )

        # 模拟发送短信
        logger.info(f"向 {phone} 发送紧急短信: {message}")
        
        # 返回模拟成功响应
        return jsonify({
            'success': True,
            'message': f'已向 {phone} 发送紧急短信',
            'sms_content': message,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"紧急短信处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500