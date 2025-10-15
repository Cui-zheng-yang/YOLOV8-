from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class YOLODetector:
    """仅支持目标检测的 YOLO 跌倒检测器"""
    
    def __init__(self, model_path: str, confidence: float = 0.85):
        """
        初始化 YOLO 检测器
        
        Args:
            model_path: 目标检测模型文件路径
            confidence: 置信度阈值
        """
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """加载 YOLO 目标检测模型"""
        try:
            logger.info(f"正在加载目标检测模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise
    
    def detect(self, image: np.ndarray, verbose: bool = False) -> List[Dict]:
        """
        检测图像中的目标（仅目标检测）
        
        Args:
            image: 输入图像 (numpy 数组)
            verbose: 是否显示详细信息
            
        Returns:
            检测结果列表，每个元素包含 bbox、类别、置信度等信息
        """
        if self.model is None:
            raise RuntimeError("模型未加载")
        
        try:
            results = self.model(image, verbose=verbose, conf=self.confidence)
            detections = self._parse_results(results)
            logger.debug(f"检测到 {len(detections)} 个目标")
            return detections
        except Exception as e:
            logger.error(f"检测失败: {str(e)}")
            return []
    
    def _parse_results(self, results) -> List[Dict]:
        """
        解析 YOLO 目标检测结果
        
        Args:
            results: YOLO 检测结果对象
            
        Returns:
            解析后的检测结果列表
        """
        detections = []
        
        for result in results:
            # 提取目标检测核心信息
            boxes = result.boxes.xyxy.cpu().numpy()  # 边界框 [x1, y1, x2, y2]
            confidences = result.boxes.conf.cpu().numpy()  # 置信度
            classes = result.boxes.cls.cpu().numpy()  # 类别 ID
            
            # 遍历每个检测目标
            for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                detection = {
                    'id': i,
                    'bbox': box.tolist(),
                    'confidence': float(conf),
                    'class_id': int(cls),
                    'class_name': self.model.names[int(cls)] if hasattr(self.model, 'names') else f'class_{int(cls)}'
                }
                detections.append(detection)
        
        return detections
    
    def judge_fall(self, detections: List[Dict]) -> Tuple[List[bool], List[float]]:
        """
        判断每个检测目标是否为跌倒（基于类别名）
        
        Args:
            detections: 解析后的检测结果
            
        Returns:
            is_fall_list: 是否跌倒的布尔列表
            fall_scores: 跌倒置信度分数列表（直接用目标检测置信度）
        """
        is_fall_list = []
        fall_scores = []
        
        for det in detections:
            # 若类别名为 fall/跌倒/Fall，判定为跌倒
            is_fall = det['class_name'] in ['fall', '跌倒', 'Fall']
            score = det['confidence']  # 复用目标检测的置信度作为跌倒分数
            
            is_fall_list.append(is_fall)
            fall_scores.append(score)
        
        return is_fall_list, fall_scores
    
    def draw_detections(
        self, 
        image: np.ndarray, 
        detections: List[Dict],
        is_fall_list: Optional[List[bool]] = None,
        fall_scores: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        在图像上绘制目标检测和跌倒结果
        
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
            
            # 确定颜色：跌倒为红色，否则为绿色
            is_fall = is_fall_list[i] if is_fall_list and i < len(is_fall_list) else False
            color = (0, 0, 255) if is_fall else (0, 255, 0)  # BGR 格式
            
            # 绘制边界框
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 确定标签：跌倒优先，否则用类别名
            label = "FALL!" if is_fall else detection['class_name']
            score = fall_scores[i] if fall_scores and i < len(fall_scores) else detection['confidence']
            text = f"{label} ({score:.2f})"
            
            # 绘制文本背景和文本
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
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_path': str(self.model_path),
            'model_name': self.model_path.split('/')[-1] if isinstance(self.model_path, str) else 'yolov8n',
            'confidence_threshold': self.confidence,
            'loaded': self.model is not None,
            'type': 'object_detection'  # 标记为目标检测类型
        }

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 初始化检测器（替换为你的目标检测模型路径）
    detector = YOLODetector(
        model_path="path/to/your/object_detection_model.pt",
        confidence=0.5
    )
    
    # 读取测试图像
    image_path = "path/to/your/test_image.jpg"
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"无法读取图像: {image_path}")
        exit(1)
    
    # 执行检测
    detections = detector.detect(image)
    
    # 判断是否跌倒
    is_fall_list, fall_scores = detector.judge_fall(detections)
    
    # 绘制结果
    result_image = detector.draw_detections(
        image,
        detections,
        is_fall_list=is_fall_list,
        fall_scores=fall_scores
    )
    
    # 保存并显示结果
    output_path = "fall_detection_result.jpg"
    cv2.imwrite(output_path, result_image)
    logger.info(f"检测结果已保存至: {output_path}")
    
    # 显示结果
    cv2.imshow("Fall Detection Result", result_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()