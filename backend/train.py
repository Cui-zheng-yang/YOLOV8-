from ultralytics import YOLO
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("train_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # 创建模型实例 - 使用 YOLOv8 模型
        # 可选: yolo8n.pt (nano), yolo8s.pt (small), yolo8m.pt (medium), yolo8l.pt (large), yolo8x.pt (extra large)
        # 注意：如果本地没有模型文件，Ultralytics 会自动下载
        model = YOLO('yolov8n.pt')
        
        # 定义训练参数
        data_config = 'd:\\小发明\\YOLOV8-\\fall_training_data\\Fall-Detected\\Falldown_set.yaml'
        epochs = 300
        batch_size = 16  # 根据GPU内存调整
        img_size = 640   # 输入图像大小
        workers = 4      # 数据加载工作进程数
        device = 0       # 使用GPU训练，-1表示CPU
        patience = 50    # 早停耐心值
        project = 'fall_detection'
        name = f'train_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # 开始训练
        logger.info(f"开始训练YOLOv8模型，使用配置文件: {data_config}")
        results = model.train(
            data=data_config,
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            workers=workers,
            device=device,
            patience=patience,
            project=project,
            name=name,
            pretrained=True,
            cache=True,        # 缓存数据以加速训练
            save=True,         # 保存检查点
            save_period=10,    # 每10个epoch保存一次
            verbose=True,
            plots=True         # 生成训练曲线图
        )
        
        logger.info("模型训练完成！")
        logger.info(f"训练结果保存在: {os.path.join(project, name)}")
        
        # 评估模型性能
        logger.info("评估模型性能...")
        metrics = model.val()
        logger.info(f"模型性能: {metrics}")
        
        # 可选：导出模型为其他格式
        # model.export(format='onnx')
        
    except Exception as e:
        logger.error(f"训练过程中发生错误: {str(e)}")
        raise