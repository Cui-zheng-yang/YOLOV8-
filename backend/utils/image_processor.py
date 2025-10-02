import base64
import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图像处理工具类"""
    
    @staticmethod
    def base64_to_image(base64_string: str) -> Optional[np.ndarray]:
        """
        Base64字符串转换为图像
        
        Args:
            base64_string: Base64编码的图像字符串
            
        Returns:
            numpy图像数组，失败返回None
        """
        try:
            # 移除data URL前缀
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # 解码base64
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # 解码图像
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("图像解码失败")
                return None
            
            logger.debug(f"成功解码图像，尺寸: {image.shape}")
            return image
            
        except Exception as e:
            logger.error(f"Base64转图像失败: {str(e)}")
            return None
    
    @staticmethod
    def image_to_base64(
        image: np.ndarray, 
        format: str = '.jpg',
        quality: int = 85
    ) -> Optional[str]:
        """
        图像转换为Base64字符串
        
        Args:
            image: numpy图像数组
            format: 图像格式 ('.jpg' 或 '.png')
            quality: JPEG质量 (1-100)
            
        Returns:
            Base64编码的图像字符串，失败返回None
        """
        try:
            # 编码参数
            if format == '.jpg':
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            else:
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            
            # 编码图像
            success, buffer = cv2.imencode(format, image, encode_params)
            
            if not success:
                logger.error("图像编码失败")
                return None
            
            # 转换为base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 添加data URL前缀
            mime_type = 'image/jpeg' if format == '.jpg' else 'image/png'
            result = f'data:{mime_type};base64,{image_base64}'
            
            logger.debug(f"成功编码图像，大小: {len(result)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"图像转Base64失败: {str(e)}")
            return None
    
    @staticmethod
    def resize_image(
        image: np.ndarray, 
        max_size: Tuple[int, int] = (1920, 1080)
    ) -> np.ndarray:
        """
        调整图像大小（保持宽高比）
        
        Args:
            image: 输入图像
            max_size: 最大尺寸 (width, height)
            
        Returns:
            调整后的图像
        """
        height, width = image.shape[:2]
        max_width, max_height = max_size
        
        # 计算缩放比例
        scale = min(max_width / width, max_height / height, 1.0)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"图像已调整: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    @staticmethod
    def validate_image(image: np.ndarray) -> bool:
        """
        验证图像是否有效
        
        Args:
            image: 图像数组
            
        Returns:
            是否有效
        """
        if image is None:
            return False
        
        if not isinstance(image, np.ndarray):
            return False
        
        if image.size == 0:
            return False
        
        if len(image.shape) < 2:
            return False
        
        return True
    
    @staticmethod
    def add_watermark(
        image: np.ndarray, 
        text: str = "Fall Detection System",
        position: str = "bottom_right"
    ) -> np.ndarray:
        """
        添加水印
        
        Args:
            image: 输入图像
            text: 水印文本
            position: 位置 ('bottom_right', 'bottom_left', 'top_right', 'top_left')
            
        Returns:
            添加水印后的图像
        """
        result = image.copy()
        height, width = result.shape[:2]
        
        # 字体设置
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        color = (255, 255, 255)
        bg_color = (0, 0, 0)
        
        # 获取文本尺寸
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 计算位置
        padding = 10
        if position == "bottom_right":
            x = width - text_width - padding
            y = height - padding
        elif position == "bottom_left":
            x = padding
            y = height - padding
        elif position == "top_right":
            x = width - text_width - padding
            y = text_height + padding
        else:  # top_left
            x = padding
            y = text_height + padding
        
        # 绘制背景
        cv2.rectangle(
            result,
            (x - 5, y - text_height - 5),
            (x + text_width + 5, y + 5),
            bg_color,
            -1
        )
        
        # 绘制文本
        cv2.putText(result, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        
        return result