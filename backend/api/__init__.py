# backend/api/__init__.py
"""
API模块初始化
"""
from .detection import detection_bp
from .health import health_bp

__all__ = ['detection_bp', 'health_bp']