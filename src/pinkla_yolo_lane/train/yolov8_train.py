from ultralytics import YOLO
import os

# choose 
model = YOLO(model='yolov8m-seg.yaml')
data_directory = 'roboflow_dataset.yaml'
model.train(batch=8, data=data_directory, epochs=200, imgsz = 640)
