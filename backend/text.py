from ultralytics import YOLO

model = YOLO('D:/小发明/YOLOV8-/fall_detection/train_20251012_133752/weights/best.pt') # 也可以换成last.pt
results = model.predict(source='D:/lianz/Videos/屏幕录制/屏幕录制 2025-10-15 163901.mp4', save=True)  # 对单张图片推理，source也可以是视频文件路径、摄像头等
