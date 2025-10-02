from flask import Flask
from flask_cors import CORS
import os
import sys
from pathlib import Path
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}})  # 允许前端域名
# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from models.yolo_detector import YOLODetector
from models.fall_detector import FallDetector
from api.detection import detection_bp, init_detectors
from api.health import health_bp
from utils.logger import setup_logger

def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置环境名称
        
    Returns:
        Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    config = get_config(config_name)
    app.config.from_object(config)
    
    # 设置日志
    logger = setup_logger(
        name='fall_detection',
        log_file=config.LOG_FILE,
        level=config.LOG_LEVEL,
        max_bytes=config.LOG_MAX_BYTES,
        backup_count=config.LOG_BACKUP_COUNT
    )
    
    logger.info("=" * 60)
    logger.info("启动跌倒检测系统")
    logger.info("=" * 60)
    logger.info(f"环境: {config_name or 'development'}")
    logger.info(f"调试模式: {config.DEBUG}")
    
    # 配置CORS
    CORS(app, resources={
        f"{config.API_PREFIX}/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # 初始化模型
    logger.info("初始化检测模型...")
    
    try:
        # 初始化YOLO检测器
        yolo_detector = YOLODetector(
            model_path=config.MODEL_NAME,
            confidence=config.MODEL_CONFIDENCE
        )
        logger.info(f"✓ YOLO模型加载成功: {config.MODEL_NAME}")
        
        # 初始化跌倒检测器
        fall_detector = FallDetector(
            fall_threshold=config.FALL_THRESHOLD,
            angle_threshold_high=config.ANGLE_THRESHOLD_HIGH,
            angle_threshold_mid=config.ANGLE_THRESHOLD_MID,
            height_ratio_high=config.HEIGHT_RATIO_HIGH,
            height_ratio_mid=config.HEIGHT_RATIO_MID,
            history_length=config.HISTORY_LENGTH
        )
        logger.info("✓ 跌倒检测器初始化成功")
        
        # 初始化API检测器
        init_detectors(yolo_detector, fall_detector)
        
    except Exception as e:
        logger.error(f"✗ 模型初始化失败: {str(e)}")
        raise
    
    # 注册蓝图
    app.register_blueprint(detection_bp, url_prefix=f"{config.API_PREFIX}")
    app.register_blueprint(health_bp, url_prefix=f"{config.API_PREFIX}")
    logger.info("✓ API路由注册成功")
    
    # 根路径
    @app.route('/')
    def index():
        return {
            'name': '跌倒检测系统 API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': f"{config.API_PREFIX}/health",
                'status': f"{config.API_PREFIX}/status",
                'detect_image': f"{config.API_PREFIX}/detect_image",
                'detect_video': f"{config.API_PREFIX}/detect_video",
                'config': f"{config.API_PREFIX}/config",
                'reset': f"{config.API_PREFIX}/reset"
            }
        }
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': '接口不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器错误: {str(error)}")
        return {'error': '服务器内部错误'}, 500
    
    logger.info("=" * 60)
    logger.info(f"🚀 服务器启动成功")
    logger.info(f"📡 API地址: http://{config.HOST}:{config.PORT}{config.API_PREFIX}")
    logger.info("=" * 60)
    
    return app

if __name__ == '__main__':
    # 获取环境变量
    env = os.getenv('FLASK_ENV', 'development')
    
    # 创建应用
    app = create_app(env)
    config = get_config(env)
    
    # 运行应用
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )