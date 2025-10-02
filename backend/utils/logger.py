import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logger(
    name: str = 'fall_detection',
    log_file: Path = None,
    level: str = 'INFO',
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_request(logger: logging.Logger, endpoint: str, method: str, data: dict = None):
    """
    记录API请求
    
    Args:
        logger: 日志记录器
        endpoint: 端点
        method: HTTP方法
        data: 请求数据
    """
    logger.info(f"API请求 - {method} {endpoint}")
    if data:
        logger.debug(f"请求数据: {data}")

def log_detection_result(logger: logging.Logger, result: dict):
    """
    记录检测结果
    
    Args:
        logger: 日志记录器
        result: 检测结果
    """
    logger.info(
        f"检测完成 - 人数: {result.get('detection_count', 0)}, "
        f"跌倒: {result.get('fall_detected', False)}"
    )