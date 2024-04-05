import cv2
from time import time
from ultralytics import YOLO

# best.pt(trained model) path
model = YOLO('yolov8n-seg.pt')

## ./src/lane-seg-yolov8/yolov8n-seg.pt
## ./src/lane-seg-yolov8/yolov8m-seg.pt

# inference video path
video_path = 0
cap = cv2.VideoCapture(video_path)

fps = 0
frame_count = 0
start_time = time()

while cap.isOpened():
    ret, frame = cap.read()

    if ret:
        # Run YOLOv8 inference on the frame (only class 0, 1, 3)
        results = model.predict(frame, classes=[0,1,3], conf=0.5)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # check fps
        frame_count += 1
        if frame_count >= 10:
            end_time = time()
            fps = frame_count / (end_time - start_time)
            frame_count = 0
            start_time = time()

        # show fps 
        cv2.putText(annotated_frame, f"FPS: {round(fps, 2)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("YOLOv8 Inference", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()


