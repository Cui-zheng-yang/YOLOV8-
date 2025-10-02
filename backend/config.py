import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """基础配置"""
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # 模型配置
    MODEL_NAME = 'yolov8n-pose.pt'
    MODEL_PATH = BASE_DIR / 'models' / 'weights' / MODEL_NAME
    MODEL_CONFIDENCE = float(os.getenv('MODEL_CONFIDENCE', 0.5))
    
    # 跌倒检测配置
    FALL_THRESHOLD = float(os.getenv('FALL_THRESHOLD', 0.6))
    ANGLE_THRESHOLD_HIGH = float(os.getenv('ANGLE_THRESHOLD_HIGH', 60))
    ANGLE_THRESHOLD_MID = float(os.getenv('ANGLE_THRESHOLD_MID', 45))
    HEIGHT_RATIO_HIGH = float(os.getenv('HEIGHT_RATIO_HIGH', 0.3))
    HEIGHT_RATIO_MID = float(os.getenv('HEIGHT_RATIO_MID', 0.5))
    HISTORY_LENGTH = int(os.getenv('HISTORY_LENGTH', 5))
    
    # 图像处理配置
    MAX_IMAGE_SIZE = (1920, 1080)
    JPEG_QUALITY = int(os.getenv('JPEG_QUALITY', 85))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # API配置
    API_PREFIX = '/api'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """获取配置对象"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])