from ultralytics import YOLO

model = YOLO('D:/小发明/YOLOV8-/fall_detection/train_20251012_133752/weights/best.pt') # 也可以换成last.pt
results = model.predict(source='D:/Fall down_img/test/A-143-_png.rf.3a1c2fdbe13d21b805d4b0629241e261.jpg', save=True)  # 对单张图片推理，source也可以是视频文件路径、摄像头等