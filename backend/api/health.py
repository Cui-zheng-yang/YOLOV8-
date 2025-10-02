from flask import Blueprint, jsonify
import psutil
import time
from datetime import datetime

health_bp = Blueprint('health', __name__)

# 服务启动时间
START_TIME = time.time()

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    响应:
        {
            "status": "ok",
            "timestamp": "2025-10-01T10:30:45",
            "uptime": 3600.5,
            "model": "yolov8n-pose"
        }
    """
    uptime = time.time() - START_TIME
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': uptime,
        'model': 'yolov8n-pose',
        'version': '1.0.0'
    })

@health_bp.route('/status', methods=['GET'])
def system_status():
    """
    系统状态接口
    
    响应:
        {
            "cpu_percent": 45.2,
            "memory_percent": 62.3,
            "disk_percent": 78.5
        }
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'status': 'ok',
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3)
            },
            'uptime': time.time() - START_TIME
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500