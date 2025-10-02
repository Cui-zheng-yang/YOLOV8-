from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from models.yolo_detector import YOLODetector
from models.fall_detector import FallDetector
from utils.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

# 创建蓝图
detection_bp = Blueprint('detection', __name__)

# 全局检测器实例（在app.py中初始化）
yolo_detector = None
fall_detector = None

def init_detectors(yolo_det, fall_det):
    """初始化检测器"""
    global yolo_detector, fall_detector
    yolo_detector = yolo_det
    fall_detector = fall_det

@detection_bp.route('/detect_image', methods=['POST'])
def detect_image():
    """
    图片检测接口
    
    请求体:
        {
            "image": "data:image/jpeg;base64,..."
        }
    
    响应:
        {
            "success": true,
            "fall_detected": false,
            "detections": [...],
            "result_image": "data:image/jpeg;base64,...",
            "timestamp": "2025-10-01T10:30:45.123456"
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': '缺少图像数据'
            }), 400
        
        image_data = data.get('image', '')
        logger.info("收到图片检测请求")
        
        # 解码图像
        image = ImageProcessor.base64_to_image(image_data)
        if image is None:
            return jsonify({
                'success': False,
                'error': '图像解码失败'
            }), 400
        
        # 调整图像大小
        image = ImageProcessor.resize_image(image)
        
        # YOLO检测
        detections = yolo_detector.detect(image)
        logger.info(f"YOLO检测到 {len(detections)} 个人体")
        
        # 跌倒检测
        fall_detected = False
        fall_results = []
        is_fall_list = []
        fall_scores = []
        
        for detection in detections:
            keypoints = detection['keypoints_array']
            is_fall, fall_score, details = fall_detector.detect(keypoints, detection['id'])
            
            if is_fall:
                fall_detected = True
            
            is_fall_list.append(is_fall)
            fall_scores.append(fall_score)
            
            fall_results.append({
                'id': detection['id'],
                'bbox': detection['bbox'],
                'is_fall': is_fall,
                'fall_score': float(fall_score),
                'confidence': detection['confidence'],
                'details': {k: float(v) if isinstance(v, (int, float)) else v 
                           for k, v in details.items()}
            })
        
        # 绘制检测结果
        result_image = yolo_detector.draw_detections(
            image, detections, is_fall_list, fall_scores
        )
        
        # 添加水印
        result_image = ImageProcessor.add_watermark(result_image)
        
        # 编码结果图像
        result_image_base64 = ImageProcessor.image_to_base64(result_image)
        
        if result_image_base64 is None:
            return jsonify({
                'success': False,
                'error': '结果图像编码失败'
            }), 500
        
        # 构建响应
        response = {
            'success': True,
            'fall_detected': fall_detected,
            'detection_count': len(detections),
            'detections': fall_results,
            'result_image': result_image_base64,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"检测完成 - 跌倒: {fall_detected}, 人数: {len(detections)}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"图片检测失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@detection_bp.route('/detect_video', methods=['POST'])
def detect_video():
    """
    视频帧检测接口
    
    请求体:
        {
            "frame": "data:image/jpeg;base64,..."
        }
    
    响应:
        {
            "success": true,
            "fall_detected": false,
            "detections": [...],
            "result_frame": "data:image/jpeg;base64,...",
            "timestamp": "2025-10-01T10:30:45.123456"
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'frame' not in data:
            return jsonify({
                'success': False,
                'error': '缺少帧数据'
            }), 400
        
        frame_data = data.get('frame', '')
        
        # 解码图像
        frame = ImageProcessor.base64_to_image(frame_data)
        if frame is None:
            return jsonify({
                'success': False,
                'error': '帧解码失败'
            }), 400
        
        # YOLO检测
        detections = yolo_detector.detect(frame)
        
        # 跌倒检测
        fall_detected = False
        fall_results = []
        is_fall_list = []
        fall_scores = []
        
        for detection in detections:
            keypoints = detection['keypoints_array']
            is_fall, fall_score, details = fall_detector.detect(keypoints, detection['id'])
            
            if is_fall:
                fall_detected = True
            
            is_fall_list.append(is_fall)
            fall_scores.append(fall_score)
            
            fall_results.append({
                'id': detection['id'],
                'is_fall': is_fall,
                'fall_score': float(fall_score),
                'confidence': detection['confidence']
            })
        
        # 绘制检测结果
        result_frame = yolo_detector.draw_detections(
            frame, detections, is_fall_list, fall_scores
        )
        
        # 编码结果帧
        result_frame_base64 = ImageProcessor.image_to_base64(result_frame, quality=75)
        
        if result_frame_base64 is None:
            return jsonify({
                'success': False,
                'error': '结果帧编码失败'
            }), 500
        
        # 构建响应
        response = {
            'success': True,
            'fall_detected': fall_detected,
            'detection_count': len(detections),
            'detections': fall_results,
            'result_frame': result_frame_base64,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"视频帧检测失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@detection_bp.route('/reset', methods=['POST'])
def reset_detector():
    """
    重置检测器历史记录
    
    请求体:
        {
            "object_id": 0  // 可选，不提供则重置所有
        }
    """
    try:
        data = request.get_json() or {}
        object_id = data.get('object_id')
        
        fall_detector.reset_history(object_id)
        
        return jsonify({
            'success': True,
            'message': '检测器已重置'
        })
        
    except Exception as e:
        logger.error(f"重置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@detection_bp.route('/config', methods=['GET'])
def get_config():
    """获取检测器配置"""
    try:
        config = {
            'yolo': yolo_detector.get_model_info(),
            'fall_detector': fall_detector.get_config()
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500