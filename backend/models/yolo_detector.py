from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class YOLODetector:
    """YOLOv8姿态检测器"""
    
    def __init__(self, model_path: str, confidence: float = 0.5):
        """
        初始化YOLO检测器
        
        Args:
            model_path: 模型文件路径
            confidence: 置信度阈值
        """
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """加载YOLO模型"""
        try:
            logger.info(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise
    
    def detect(self, image: np.ndarray, verbose: bool = False) -> List[Dict]:
        """
        检测图像中的人体姿态
        
        Args:
            image: 输入图像 (numpy数组)
            verbose: 是否显示详细信息
            
        Returns:
            检测结果列表，每个元素包含bbox、keypoints等信息
        """
        if self.model is None:
            raise RuntimeError("模型未加载")
        
        try:
            results = self.model(image, verbose=verbose, conf=self.confidence)
            detections = self._parse_results(results)
            logger.debug(f"检测到 {len(detections)} 个人体")
            return detections
        except Exception as e:
            logger.error(f"检测失败: {str(e)}")
            return []
    
    def _parse_results(self, results) -> List[Dict]:
        """
        解析YOLO检测结果
        
        Args:
            results: YOLO检测结果对象
            
        Returns:
            解析后的检测结果列表
        """
        detections = []
        
        for result in results:
            if result.keypoints is None:
                continue
                
            keypoints_data = result.keypoints.data.cpu().numpy()
            boxes = result.boxes.xyxy.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            
            for i, (box, keypoints, conf) in enumerate(zip(boxes, keypoints_data, confidences)):
                detection = {
                    'id': i,
                    'bbox': box.tolist(),  # [x1, y1, x2, y2]
                    'confidence': float(conf),
                    'keypoints': keypoints.tolist(),  # [[x, y, conf], ...]
                    'keypoints_array': keypoints  # numpy数组，用于计算
                }
                detections.append(detection)
        
        return detections
    
    def draw_detections(
        self, 
        image: np.ndarray, 
        detections: List[Dict],
        is_fall_list: Optional[List[bool]] = None,
        fall_scores: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        Args:
            image: 原始图像
            detections: 检测结果列表
            is_fall_list: 是否跌倒列表
            fall_scores: 跌倒分数列表
            
        Returns:
            标注后的图像
        """
        result_image = image.copy()
        
        for i, detection in enumerate(detections):
            bbox = detection['bbox']
            keypoints = detection['keypoints']
            
            # 确定颜色
            is_fall = is_fall_list[i] if is_fall_list and i < len(is_fall_list) else False
            color = (0, 0, 255) if is_fall else (0, 255, 0)  # BGR格式
            
            # 绘制边界框
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 绘制关键点
            for kp in keypoints:
                if kp[2] > 0.5:  # 置信度阈值
                    x, y = int(kp[0]), int(kp[1])
                    cv2.circle(result_image, (x, y), 4, color, -1)
            
            # 绘制骨架连接
            self._draw_skeleton(result_image, keypoints, color)
            
            # 添加标签
            label = "FALL!" if is_fall else "Normal"
            score = fall_scores[i] if fall_scores and i < len(fall_scores) else 0.0
            text = f"{label} ({score:.2f})"
            
            # 文本背景
            (text_width, text_height), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                result_image, 
                (x1, y1 - text_height - 10), 
                (x1 + text_width, y1), 
                color, 
                -1
            )
            
            # 绘制文本
            cv2.putText(
                result_image, 
                text, 
                (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                (255, 255, 255), 
                2
            )
        
        return result_image
    
    def _draw_skeleton(self, image: np.ndarray, keypoints: List, color: Tuple[int, int, int]):
        """
        绘制人体骨架
        
        Args:
            image: 图像
            keypoints: 关键点列表
            color: 颜色
        """
        # COCO骨架连接 (17个关键点)
        skeleton = [
            [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],  # 腿部
            [6, 12], [7, 13],  # 躯干
            [6, 8], [7, 9], [8, 10], [9, 11],  # 手臂
            [6, 7],  # 肩膀
            [1, 2], [0, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6]  # 头部和脸
        ]
        
        for connection in skeleton:
            try:
                pt1_idx, pt2_idx = connection[0] - 1, connection[1] - 1  # 转换为0索引
                
                if pt1_idx < 0 or pt2_idx < 0 or pt1_idx >= len(keypoints) or pt2_idx >= len(keypoints):
                    continue
                
                kp1 = keypoints[pt1_idx]
                kp2 = keypoints[pt2_idx]
                
                if kp1[2] > 0.5 and kp2[2] > 0.5:
                    pt1 = (int(kp1[0]), int(kp1[1]))
                    pt2 = (int(kp2[0]), int(kp2[1]))
                    cv2.line(image, pt1, pt2, color, 2)
            except:
                continue
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_path': str(self.model_path),
            'model_name': self.model_path.split('/')[-1] if isinstance(self.model_path, str) else 'yolov8n-pose',
            'confidence_threshold': self.confidence,
            'loaded': self.model is not None
        }