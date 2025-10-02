# backend/models/__init__.py
"""
模型模块初始化
"""
from .yolo_detector import YOLODetector
from .fall_detector import FallDetector

__all__ = ['YOLODetector', 'FallDetector']