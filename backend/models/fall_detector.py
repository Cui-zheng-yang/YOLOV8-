import numpy as np
import math
from typing import List, Tuple, Dict
from collections import deque
import logging

logger = logging.getLogger(__name__)

class FallDetector:
    """跌倒检测器"""
    
    # COCO关键点索引
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16
    
    def __init__(
        self, 
        fall_threshold: float = 0.6,
        angle_threshold_high: float = 60,
        angle_threshold_mid: float = 45,
        height_ratio_high: float = 0.3,
        height_ratio_mid: float = 0.5,
        history_length: int = 5
    ):
        """
        初始化跌倒检测器
        
        Args:
            fall_threshold: 跌倒判断阈值
            angle_threshold_high: 高风险角度阈值
            angle_threshold_mid: 中风险角度阈值
            height_ratio_high: 高风险高度比阈值
            height_ratio_mid: 中风险高度比阈值
            history_length: 历史记录长度
        """
        self.fall_threshold = fall_threshold
        self.angle_threshold_high = angle_threshold_high
        self.angle_threshold_mid = angle_threshold_mid
        self.height_ratio_high = height_ratio_high
        self.height_ratio_mid = height_ratio_mid
        self.history_length = history_length
        
        # 每个检测对象的历史记录
        self.history = {}
        
    def detect(self, keypoints: np.ndarray, object_id: int = 0) -> Tuple[bool, float, Dict]:
        """
        检测是否跌倒
        
        Args:
            keypoints: 关键点数组 [17, 3] (x, y, confidence)
            object_id: 对象ID
            
        Returns:
            (是否跌倒, 跌倒分数, 详细信息)
        """
        # 计算跌倒分数
        score, details = self.calculate_fall_score(keypoints)
        
        # 更新历史记录
        if object_id not in self.history:
            self.history[object_id] = deque(maxlen=self.history_length)
        
        self.history[object_id].append(score)
        
        # 使用历史平均值判断
        avg_score = sum(self.history[object_id]) / len(self.history[object_id])
        is_fall = avg_score > self.fall_threshold
        
        details['avg_score'] = avg_score
        details['history_length'] = len(self.history[object_id])
        
        logger.debug(f"对象 {object_id}: 分数={score:.3f}, 平均={avg_score:.3f}, 跌倒={is_fall}")
        
        return is_fall, score, details
    
    def calculate_fall_score(self, keypoints: np.ndarray) -> Tuple[float, Dict]:
        """
        计算跌倒分数
        
        Args:
            keypoints: 关键点数组
            
        Returns:
            (跌倒分数, 详细信息字典)
        """
        details = {}
        
        # 检查关键点有效性
        if keypoints is None or len(keypoints) == 0:
            return 0.0, {'error': 'No keypoints'}
        
        # 提取关键点
        try:
            nose = keypoints[self.NOSE]
            left_shoulder = keypoints[self.LEFT_SHOULDER]
            right_shoulder = keypoints[self.RIGHT_SHOULDER]
            left_hip = keypoints[self.LEFT_HIP]
            right_hip = keypoints[self.RIGHT_HIP]
            left_ankle = keypoints[self.LEFT_ANKLE]
            right_ankle = keypoints[self.RIGHT_ANKLE]
        except IndexError:
            return 0.0, {'error': 'Invalid keypoints'}
        
        # 检查关键点置信度
        min_confidence = 0.3
        if not all([
            kp[2] > min_confidence 
            for kp in [left_shoulder, right_shoulder, left_hip, right_hip]
        ]):
            return 0.0, {'error': 'Low confidence keypoints'}
        
        # 1. 计算身体角度
        angle_score, angle = self._calculate_body_angle(
            left_shoulder, right_shoulder, left_hip, right_hip
        )
        details['body_angle'] = angle
        details['angle_score'] = angle_score
        
        # 2. 计算头部高度比例
        height_score, height_ratio = self._calculate_height_ratio(
            nose, left_ankle, right_ankle
        )
        details['height_ratio'] = height_ratio
        details['height_score'] = height_score
        
        # 3. 计算姿态异常分数
        posture_score = self._calculate_posture_score(
            left_shoulder, right_shoulder, left_hip, right_hip
        )
        details['posture_score'] = posture_score
        
        # 4. 综合评分
        fall_score = angle_score + height_score + posture_score
        fall_score = min(fall_score, 1.0)
        
        details['total_score'] = fall_score
        
        return fall_score, details
    
    def _calculate_body_angle(
        self, 
        left_shoulder: np.ndarray, 
        right_shoulder: np.ndarray,
        left_hip: np.ndarray, 
        right_hip: np.ndarray
    ) -> Tuple[float, float]:
        """
        计算身体角度（躯干与垂直方向的夹角）
        
        Returns:
            (角度分数, 角度值)
        """
        # 计算肩部和髋部中心点
        shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
        hip_center_x = (left_hip[0] + right_hip[0]) / 2
        hip_center_y = (left_hip[1] + right_hip[1]) / 2
        
        # 计算躯干向量
        dx = hip_center_x - shoulder_center_x
        dy = hip_center_y - shoulder_center_y
        
        # 计算与垂直方向的夹角
        if dy != 0:
            angle = abs(math.atan(dx / dy) * 180 / math.pi)
        else:
            angle = 90.0
        
        # 角度评分
        if angle > self.angle_threshold_high:
            score = 0.4
        elif angle > self.angle_threshold_mid:
            score = 0.2
        else:
            score = 0.0
        
        return score, angle
    
    def _calculate_height_ratio(
        self, 
        nose: np.ndarray,
        left_ankle: np.ndarray, 
        right_ankle: np.ndarray
    ) -> Tuple[float, float]:
        """
        计算头部高度比例
        
        Returns:
            (高度分数, 高度比例)
        """
        # 计算脚踝平均位置
        ankle_y = (left_ankle[1] + right_ankle[1]) / 2
        
        # 处理无效情况
        if ankle_y <= 0 or nose[1] <= 0:
            return 0.0, 1.0
        
        # 计算高度比例（头部位置 / 脚踝位置）
        # 注意：图像坐标系y轴向下
        height_ratio = (ankle_y - nose[1]) / ankle_y
        
        # 高度评分
        if height_ratio < self.height_ratio_high:
            score = 0.4
        elif height_ratio < self.height_ratio_mid:
            score = 0.2
        else:
            score = 0.0
        
        return score, height_ratio
    
    def _calculate_posture_score(
        self,
        left_shoulder: np.ndarray,
        right_shoulder: np.ndarray,
        left_hip: np.ndarray,
        right_hip: np.ndarray
    ) -> float:
        """
        计算姿态异常分数
        
        Returns:
            姿态分数
        """
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
        hip_center_y = (left_hip[1] + right_hip[1]) / 2
        
        # 如果肩部低于髋部（人体倒置或弯曲严重）
        if shoulder_center_y > hip_center_y:
            return 0.2
        
        return 0.0
    
    def reset_history(self, object_id: int = None):
        """
        重置历史记录
        
        Args:
            object_id: 对象ID，如果为None则重置所有
        """
        if object_id is None:
            self.history.clear()
            logger.info("已重置所有对象的历史记录")
        elif object_id in self.history:
            del self.history[object_id]
            logger.info(f"已重置对象 {object_id} 的历史记录")
    
    def get_config(self) -> Dict:
        """获取配置信息"""
        return {
            'fall_threshold': self.fall_threshold,
            'angle_threshold_high': self.angle_threshold_high,
            'angle_threshold_mid': self.angle_threshold_mid,
            'height_ratio_high': self.height_ratio_high,
            'height_ratio_mid': self.height_ratio_mid,
            'history_length': self.history_length
        }