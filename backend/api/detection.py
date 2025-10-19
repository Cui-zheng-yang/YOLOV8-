from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import numpy as np
import os
import cv2
from pathlib import Path
from flask import send_file

from models.yolo_detector import YOLODetector
from models.fall_detector import FallDetector
from utils.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

# 创建蓝图
detection_bp = Blueprint('detection', __name__)

# 全局检测器实例（在app.py中初始化）
yolo_detector = None
fall_detector = None

# 新增：跌倒图片保存路径
FALL_IMAGES_DIR = "fall_training_data"
Path(FALL_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(os.path.join(FALL_IMAGES_DIR, "unlabeled")).mkdir(parents=True, exist_ok=True)
Path(os.path.join(FALL_IMAGES_DIR, "labeled")).mkdir(parents=True, exist_ok=True)

def init_detectors(yolo_det, fall_det):
    """初始化检测器"""
    global yolo_detector, fall_detector
    yolo_detector = yolo_det
    fall_detector = fall_det

def convert_numpy_types(obj):
    """递归将numpy类型转换为Python原生类型"""
    if isinstance(obj, (np.float32, np.float64, np.floating)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.integer)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # 将numpy数组转换为Python列表
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj  # 其他类型保持不变

# 新增：保存跌倒图片
def save_fall_image(image, detection_id, details):
    """保存检测到跌倒的图片用于后续训练"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"fall_{detection_id}_{timestamp}.jpg"
    filepath = os.path.join(FALL_IMAGES_DIR, "unlabeled", filename)
    
    # 保存原始图片
    cv2.imwrite(filepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    # 保存标注信息
    label_filename = f"fall_{detection_id}_{timestamp}.txt"
    label_filepath = os.path.join(FALL_IMAGES_DIR, "unlabeled", label_filename)
    with open(label_filepath, "w") as f:
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Details: {str(details)}\n")
    
    logger.info(f"已保存跌倒图片: {filepath}")
    return filepath

@detection_bp.route('/detect_image', methods=['POST'])
def detect_image():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': '缺少图像数据'
            }), 400
        
        image_data = data.get('image', '')
        
        # 解码图像
        image = ImageProcessor.base64_to_image(image_data)
        original_image = image.copy()  # 保存原始图像用于可能的跌倒图片保存
        if image is None:
            return jsonify({
                'success': False,
                'error': '图像解码失败'
            }), 400
        
        # YOLO检测
        detections = yolo_detector.detect(image)
        logger.info(f"YOLO检测到 {len(detections)} 个目标")
        
        # 跌倒检测 - 修改为使用基于类别的判断
        fall_detected = False
        fall_results = []
        is_fall_list = []
        fall_scores = []
        fall_details = []
        
        # 使用基于类别的跌倒判断
        is_fall_list, fall_scores = yolo_detector.judge_fall(detections)
        
        # 构建跌倒结果
        for i, detection in enumerate(detections):
            is_fall = is_fall_list[i]
            fall_score = fall_scores[i]
            
            if is_fall:
                fall_detected = True
                fall_details.append({
                    'id': detection['id'],
                    'details': {
                        'confidence': detection['confidence'],
                        'class_name': detection['class_name'],
                        'fall_judgment_basis': '基于目标检测类别'
                    }
                })
            
            fall_results.append({
                'id': detection['id'],
                'bbox': [float(coord) for coord in detection['bbox']],
                'is_fall': is_fall,
                'fall_score': float(fall_score),
                'confidence': float(detection['confidence']),
                'class_name': detection['class_name'],
                'details': {
                    'fall_judgment_basis': '基于目标检测类别'
                }
            })
        
        # 新增：如果检测到跌倒，保存图片
        if fall_detected:
            save_fall_image(original_image, id(original_image), fall_details)
        
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
        
        # 对响应进行类型转换后再序列化
        return jsonify(convert_numpy_types(response))
        
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
        
        # 解码帧图像
        frame = ImageProcessor.base64_to_image(frame_data)
        if frame is None:
            return jsonify({
                'success': False,
                'error': '帧图像解码失败'
            }), 400
        
        # YOLO检测
        detections = yolo_detector.detect(frame)
        logger.info(f"YOLO检测到 {len(detections)} 个目标")
        
        # 跌倒检测
        fall_detected = False
        fall_results = []
        is_fall_list, fall_scores = yolo_detector.judge_fall(detections)
        
        # 构建跌倒结果
        for i, detection in enumerate(detections):
            is_fall = is_fall_list[i]
            fall_score = fall_scores[i]
            
            if is_fall:
                fall_detected = True
            
            fall_results.append({
                'id': detection['id'],
                'bbox': [float(coord) for coord in detection['bbox']],
                'is_fall': is_fall,
                'fall_score': float(fall_score),
                'confidence': float(detection['confidence']),
                'class_name': detection['class_name'],
                'details': {
                    'fall_judgment_basis': '基于目标检测类别'
                }
            })
        
        # 绘制检测结果
        result_frame = yolo_detector.draw_detections(
            frame, detections, is_fall_list, fall_scores
        )
        
        # 编码结果帧
        result_frame_base64 = ImageProcessor.image_to_base64(result_frame)
        
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
            'timestamp': datetime.now().isoformat(),
            'process_time_ms': data.get('process_time_ms', 0)  # 前端处理时间
        }
        
        logger.info(f"视频帧检测完成 - 跌倒: {fall_detected}, 人数: {len(detections)}")
        
        return jsonify(convert_numpy_types(response))
        
    except Exception as e:
        logger.error(f"视频帧检测失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@detection_bp.route('/detect_local_video', methods=['POST'])
def detect_local_video():
    """
    本地视频文件检测接口（支持文件上传）
    
    请求体: multipart/form-data
        - video_file: 视频文件
        - save_results: 是否保存检测结果（可选，默认true）
        - output_dir: 输出目录（可选，默认"output"）
    
    响应:
        {
            "success": true,
            "video_filename": "uploaded_video.mp4",
            "total_frames": 100,
            "total_detections": 50,
            "fall_detections": 3,
            "output_path": "output/video_detection",
            "detection_summary": [...],
            "timestamp": "2025-10-01T10:30:45.123456"
        }
    """
    try:
        if 'video_file' not in request.files:
            return jsonify({
                'success': False,
                'error': '缺少视频文件'
            }), 400
        
        video_file = request.files['video_file']
        
        # 检查文件是否为空
        if video_file.filename == '':
            return jsonify({
                'success': False,
                'error': '未选择文件'
            }), 400
        
        # 验证文件类型
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        file_ext = os.path.splitext(video_file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型: {file_ext}。支持的类型: {", ".join(allowed_extensions)}'
            }), 400
        
        # 创建临时目录保存上传的文件
        upload_dir = "temp_uploads"
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"video_{timestamp}{file_ext}"
        temp_video_path = os.path.join(upload_dir, filename)
        
        # 保存上传的文件
        video_file.save(temp_video_path)
        
        # 获取其他参数
        save_results = request.form.get('save_results', 'true').lower() == 'true'
        output_dir = request.form.get('output_dir', 'output')
        
        # 验证视频文件是否可以打开
        try:
            cap = cv2.VideoCapture(temp_video_path)
            if not cap.isOpened():
                return jsonify({
                    'success': False,
                    'error': '无法打开视频文件，可能文件已损坏'
                }), 400
            cap.release()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'视频文件验证失败: {str(e)}'
            }), 400
        
        # 执行本地视频检测
        video_result = yolo_detector.detect_video(
            video_path=temp_video_path,
            save=save_results,
            save_dir=output_dir
        )
        
        # 清理临时文件
        try:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")
        
        if not video_result.get('success', False):
            return jsonify({
                'success': False,
                'error': video_result.get('error', '视频检测失败'),
                'video_filename': video_file.filename
            }), 500
        # 查找实际生成的视频文件名
        actual_video_filename = None
        output_path = video_result.get('output_path')
        if output_path and os.path.exists(output_path):
            # 查找目录中的.avi文件（YOLO模型生成的格式）
            video_files = [f for f in os.listdir(output_path) 
                         if f.lower().endswith('.avi')]
            if video_files:
                # 获取最新的视频文件（按修改时间排序）
                video_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_path, x)), reverse=True)
                actual_video_filename = video_files[0]
        
        if output_path and not os.path.isabs(output_path):
            # 计算正确的绝对路径：d:\小发明\video_results\video_detection
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            output_path = os.path.join(project_root, 'video_results', 'video_detection')
        # 添加时间戳和文件名信息
        video_result['timestamp'] = datetime.now().isoformat()
        video_result['video_filename'] = video_file.filename
        video_result['video_filename'] = actual_video_filename if actual_video_filename else video_file.filename  # 实际文件名或原始文件名
        logger.info(f"本地视频检测完成 - 文件: {video_file.filename}, 实际结果文件: {actual_video_filename}, 总帧数: {video_result['total_frames']}")
        
        return jsonify(convert_numpy_types(video_result))
        
    except Exception as e:
        logger.error(f"本地视频检测失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

# 新增：获取所有未标注的跌倒图片
@detection_bp.route('/get_unlabeled_falls', methods=['GET'])
def get_unlabeled_falls():
    """获取所有未标注的跌倒图片列表"""
    try:
        unlabeled_dir = os.path.join(FALL_IMAGES_DIR, "unlabeled")
        images = [f for f in os.listdir(unlabeled_dir) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        return jsonify({
            'success': True,
            'count': len(images),
            'images': images
        })
        
    except Exception as e:
        logger.error(f"获取未标注图片失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
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
        # 处理配置中的numpy类型
        config = convert_numpy_types({
            'yolo': yolo_detector.get_model_info(),
            'fall_detector': fall_detector.get_config()
        })
        
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


@detection_bp.route('/get_result_video', methods=['GET'])
def get_result_video():
    """
    获取本地视频检测的结果视频文件
    
    参数:
        - path: 结果视频路径
        - filename: 结果视频文件名
    
    返回:
        视频文件流
    """
    try:
        path = request.args.get('path')
        filename = request.args.get('filename')
        
        if not path or not filename:
            return jsonify({
                'success': False,
                'error': '缺少路径或文件名参数'
            }), 400
        
        # 智能路径处理：优先检查绝对路径
        video_path = None
        
        # 方案1：检查是否为绝对路径
        if os.path.isabs(path):
            video_path = os.path.join(path, filename)
        
        # 方案2：检查项目根目录下的video_results目录
        if not video_path or not os.path.exists(video_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            alternative_path = os.path.join(project_root, 'video_results', 'video_detection', filename)
            if os.path.exists(alternative_path):
                video_path = alternative_path
        
        # 方案3：检查项目根目录下的video_results目录
        if not video_path or not os.path.exists(video_path):
            # 修正项目根目录计算：应该指向d:\小发明目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            alternative_path = os.path.join(project_root, 'video_results', 'video_detection', filename)
            if os.path.exists(alternative_path):
                video_path = alternative_path

        # 方案4：直接检查d:\小发明\video_results\video_detection目录
        if not video_path or not os.path.exists(video_path):
            base_dir = os.getcwd()
            # 如果路径以"video_results"开头，直接拼接
            if path.startswith('video_results'):
                video_path = os.path.join(base_dir, path, filename)
            else:
                # 其他相对路径处理
                video_path = os.path.join(base_dir, path, filename)

       # 最终检查文件是否存在
        if not os.path.exists(video_path):
            return jsonify({
                'success': False,
                'error': f'结果视频文件不存在。尝试路径: {video_path}'
            }), 404
        
        # 检查文件是否为视频文件
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        file_ext = os.path.splitext(video_path)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型: {file_ext}'
            }), 400
        
        # 返回视频文件
        return send_file(
            video_path,
            as_attachment=False,
            download_name=f"detected_{filename}",
            mimetype=f'video/{file_ext[1:]}' if file_ext != '.mkv' else 'video/x-matroska'
        )
        
    except Exception as e:
        logger.error(f"获取结果视频失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取结果视频失败: {str(e)}'
        }), 500

# 新增：获取视频检测结果列表
@detection_bp.route('/get_video_results', methods=['GET'])
def get_video_results():
    """
    获取所有视频检测结果列表
    """
    try:
        results_dir = "video_results"
        if not os.path.exists(results_dir):
            return jsonify({
                'success': True,
                'results': []
            })
        
        results = []
        for item in os.listdir(results_dir):
            item_path = os.path.join(results_dir, item)
            if os.path.isdir(item_path):
                # 检查是否有结果视频文件
                video_files = [f for f in os.listdir(item_path) 
                             if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv'))]
                
                if video_files:
                    results.append({
                        'name': item,
                        'path': item_path,
                        'video_files': video_files,
                        'created_time': os.path.getctime(item_path)
                    })
        
        # 按创建时间排序
        results.sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"获取视频结果列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500