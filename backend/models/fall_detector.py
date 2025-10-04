# filePath：YOLOV8-/backend/models/fall_detector.py
import numpy as np
import math
from typing import List, Tuple, Dict
from collections import deque
import logging
from datetime import datetime
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
    
    # 新增：骨架连接用于判断身体结构
    SKELETON = [
        [LEFT_SHOULDER, RIGHT_SHOULDER],
        [LEFT_SHOULDER, LEFT_HIP],
        [RIGHT_SHOULDER, RIGHT_HIP],
        [LEFT_HIP, RIGHT_HIP],
        [LEFT_SHOULDER, LEFT_ELBOW],
        [LEFT_ELBOW, LEFT_WRIST],
        [RIGHT_SHOULDER, RIGHT_ELBOW],
        [RIGHT_ELBOW, RIGHT_WRIST],
        [LEFT_HIP, LEFT_KNEE],
        [LEFT_KNEE, LEFT_ANKLE],
        [RIGHT_HIP, RIGHT_KNEE],
        [RIGHT_KNEE, RIGHT_ANKLE]
    ]
    
    def __init__(
        self, 
        fall_threshold: float = 0.7,  # 调整阈值
        angle_threshold_high: float = 65,
        angle_threshold_mid: float = 40,
        height_ratio_high: float = 0.25,
        height_ratio_mid: float = 0.45,
        history_length: int = 8,  # 增加历史记录长度
        motion_threshold: float = 0.15  # 新增：运动变化阈值
    ):
        """初始化跌倒检测器"""
        self.fall_threshold = fall_threshold
        self.angle_threshold_high = angle_threshold_high
        self.angle_threshold_mid = angle_threshold_mid
        self.height_ratio_high = height_ratio_high
        self.height_ratio_mid = height_ratio_mid
        self.history_length = history_length
        self.motion_threshold = motion_threshold
        
        # 每个检测对象的历史记录，增加位置和速度信息
        self.history = {}
        
    def detect(self, keypoints: np.ndarray, object_id: int = 0) -> Tuple[bool, float, Dict]:
        """检测是否跌倒"""
        # 确保keypoints是numpy数组
        if not isinstance(keypoints, np.ndarray):
            keypoints = np.array(keypoints)
            
        # 计算跌倒分数
        score, details = self.calculate_fall_score(keypoints)
        
        # 初始化历史记录
        if object_id not in self.history:
            self.history[object_id] = deque(maxlen=self.history_length)
        
        # 提取关键位置用于运动分析
        shoulder_center = self._get_center_point(
            keypoints[self.LEFT_SHOULDER], keypoints[self.RIGHT_SHOULDER]
        )
        
        # 记录包含位置信息的历史
        self.history[object_id].append({
            'score': score,
            'position': (shoulder_center[0], shoulder_center[1]),  # 肩部中心点
            'timestamp': datetime.now().timestamp()
        })
        
        # 使用历史数据计算运动变化
        motion_score = self._calculate_motion_score(object_id)
        details['motion_score'] = motion_score
        
        # 综合评分（加入运动分数）
        combined_score = (score * 0.7) + (motion_score * 0.3)
        details['combined_score'] = combined_score
        
        # 使用历史平均值判断
        avg_score = sum(h['score'] for h in self.history[object_id]) / len(self.history[object_id])
        is_fall = avg_score > self.fall_threshold
        
        details['avg_score'] = avg_score
        details['history_length'] = len(self.history[object_id])
        
        logger.debug(f"对象 {object_id}: 分数={score:.3f}, 平均={avg_score:.3f}, 跌倒={is_fall}")
        
        # 确保所有值都是Python原生类型，避免JSON序列化问题
        return is_fall, float(combined_score), self._convert_to_python_types(details)
    
    def calculate_fall_score(self, keypoints: np.ndarray) -> Tuple[float, Dict]:
        """计算跌倒分数"""
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
            left_knee = keypoints[self.LEFT_KNEE]
            right_knee = keypoints[self.RIGHT_KNEE]
            left_ankle = keypoints[self.LEFT_ANKLE]
            right_ankle = keypoints[self.RIGHT_ANKLE]
        except IndexError:
            return 0.0, {'error': 'Invalid keypoints'}
        
        # 检查关键点置信度（更严格的检查）
        min_confidence = 0.4
        critical_points = [left_shoulder, right_shoulder, left_hip, right_hip]
        if not all(kp[2] > min_confidence for kp in critical_points):
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
            left_shoulder, right_shoulder, left_hip, right_hip,
            left_knee, right_knee
        )
        details['posture_score'] = posture_score
        
        # 4. 新增：计算身体比例分数（躯干与腿部比例）
        body_ratio_score, body_ratio = self._calculate_body_ratio(
            left_shoulder, right_shoulder, left_hip, right_hip,
            left_ankle, right_ankle
        )
        details['body_ratio'] = body_ratio
        details['body_ratio_score'] = body_ratio_score
        
        # 综合评分
        fall_score = angle_score + height_score + posture_score + body_ratio_score
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
        """计算身体角度（躯干与垂直方向的夹角）"""
        # 计算肩部和髋部中心点
        shoulder_center = self._get_center_point(left_shoulder, right_shoulder)
        hip_center = self._get_center_point(left_hip, right_hip)
        
        # 计算躯干向量
        dx = hip_center[0] - shoulder_center[0]
        dy = hip_center[1] - shoulder_center[1]
        
        # 计算与垂直方向的夹角
        if dy != 0:
            angle = abs(math.atan(dx / dy) * 180 / math.pi)
        else:
            angle = 90.0
        
        # 角度评分（更精细的分级）
        if angle > self.angle_threshold_high:
            score = 0.35
        elif angle > self.angle_threshold_mid:
            score = 0.15
        else:
            score = 0.0
        
        return score, float(angle)
    
    def _calculate_height_ratio(
        self, 
        nose: np.ndarray,
        left_ankle: np.ndarray, 
        right_ankle: np.ndarray
    ) -> Tuple[float, float]:
        """计算头部高度比例"""
        # 计算脚踝平均位置
        ankle_y = (left_ankle[1] + right_ankle[1]) / 2
        
        # 处理无效情况
        if ankle_y <= 0 or nose[1] <= 0:
            return 0.0, 1.0
        
        # 计算高度比例（头部位置 / 脚踝位置）
        height_ratio = (ankle_y - nose[1]) / ankle_y
        
        # 高度评分（更精细的分级）
        if height_ratio < self.height_ratio_high:
            score = 0.35
        elif height_ratio < self.height_ratio_mid:
            score = 0.15
        else:
            score = 0.0
        
        return score, float(height_ratio)
    
    def _calculate_posture_score(
        self,
        left_shoulder: np.ndarray,
        right_shoulder: np.ndarray,
        left_hip: np.ndarray,
        right_hip: np.ndarray,
        left_knee: np.ndarray,
        right_knee: np.ndarray
    ) -> float:
        """计算姿态异常分数"""
        shoulder_center = self._get_center_point(left_shoulder, right_shoulder)
        hip_center = self._get_center_point(left_hip, right_hip)
        knee_center = self._get_center_point(left_knee, right_knee)
        
        score = 0.0
        
        # 如果肩部低于髋部（人体倒置或弯曲严重）
        if shoulder_center[1] > hip_center[1]:
            score += 0.15
        
        # 如果髋部低于膝盖（可能处于蹲坐或跌倒状态）
        if hip_center[1] > knee_center[1] * 0.85:
            score += 0.15
            
        return float(score)
    
    def _calculate_body_ratio(
        self,
        left_shoulder: np.ndarray,
        right_shoulder: np.ndarray,
        left_hip: np.ndarray,
        right_hip: np.ndarray,
        left_ankle: np.ndarray,
        right_ankle: np.ndarray
    ) -> Tuple[float, float]:
        """计算躯干与腿部的比例"""
        shoulder_center = self._get_center_point(left_shoulder, right_shoulder)
        hip_center = self._get_center_point(left_hip, right_hip)
        ankle_center = self._get_center_point(left_ankle, right_ankle)
        
        # 计算躯干长度（肩到髋）
        torso_length = math.hypot(
            shoulder_center[0] - hip_center[0],
            shoulder_center[1] - hip_center[1]
        )
        
        # 计算腿部长度（髋到脚踝）
        leg_length = math.hypot(
            hip_center[0] - ankle_center[0],
            hip_center[1] - ankle_center[1]
        )
        
        # 避免除零错误
        if leg_length == 0:
            return 0.0, 0.0
            
        # 躯干与腿部的比例
        ratio = torso_length / leg_length
        
        # 跌倒时该比例通常会变大
        if ratio > 0.8:
            return 0.2, float(ratio)
        elif ratio > 0.6:
            return 0.1, float(ratio)
        else:
            return 0.0, float(ratio)
    
    def _calculate_motion_score(self, object_id: int) -> float:
        """计算运动变化分数（检测突然的位置变化）"""
        if object_id not in self.history or len(self.history[object_id]) < 3:
            return 0.0
            
        # 取最近的3个历史记录
        recent = list(self.history[object_id])[-3:]
        
        # 计算移动距离
        total_distance = 0
        time_diff = 0
        
        for i in range(1, len(recent)):
            x1, y1 = recent[i-1]['position']
            x2, y2 = recent[i]['position']
            total_distance += math.hypot(x2 - x1, y2 - y1)
            time_diff += recent[i]['timestamp'] - recent[i-1]['timestamp']
        
        # 计算平均速度
        if time_diff > 0:
            avg_speed = total_distance / time_diff
        else:
            avg_speed = 0
        
        # 速度突然变化可能表明跌倒
        if avg_speed > self.motion_threshold:
            return min(avg_speed / (self.motion_threshold * 3), 1.0)
        return 0.0
    
    def _get_center_point(self, point1: np.ndarray, point2: np.ndarray) -> Tuple[float, float]:
        """计算两个点的中心点"""
        return (
            float((point1[0] + point2[0]) / 2),
            float((point1[1] + point2[1]) / 2)
        )
    
    def _convert_to_python_types(self, data):
        """将numpy类型转换为Python原生类型，避免JSON序列化问题"""
        if isinstance(data, dict):
            return {k: self._convert_to_python_types(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_python_types(item) for item in data]
        elif isinstance(data, (np.float32, np.float64)):
            return float(data)
        elif isinstance(data, (np.int32, np.int64)):
            return int(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data
    
    def reset_history(self, object_id: int = None):
        """重置历史记录"""
        if object_id is None:
            self.history.clear()
            logger.info("已重置所有对象的历史记录")
        elif object_id in self.history:
            del self.history[object_id]
            logger.info(f"已重置对象 {object_id} 的历史记录")
    
    def get_config(self) -> Dict:
        """获取配置信息"""
        return {
            'fall_threshold': float(self.fall_threshold),
            'angle_threshold_high': float(self.angle_threshold_high),
            'angle_threshold_mid': float(self.angle_threshold_mid),
            'height_ratio_high': float(self.height_ratio_high),
            'height_ratio_mid': float(self.height_ratio_mid),
            'history_length': int(self.history_length),
            'motion_threshold': float(self.motion_threshold)
        }