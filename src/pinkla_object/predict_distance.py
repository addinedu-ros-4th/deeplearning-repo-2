from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO('best.pt')
names = model.model.names

def get_bounding_boxes(results):
    object_boxes = [] 
    classes = [] 

    for result in results:
        bounding_boxes = result.boxes
        for box in bounding_boxes:
            x1, y1, x2, y2 = box.xyxy[0] 
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cls = int(box.cls[0]) 
            object_boxes.append([x1, y1, x2, y2])
            classes.append(cls)
    return object_boxes, classes


def distance_to_camera(knownWidth, focalLength, perWidth):
    distance = (knownWidth * focalLength) / perWidth
    return distance

known_widths = {
    'minions' : 1.97,
    'tank' : 3.54
}

if __name__ == '__main__':
    
    mtx = np.array([[479.02325822, 0., 300.28563966],
                    [0., 478.72152516, 232.33223961],
                    [0., 0., 1.]])
    dist = np.array([[-0.01884809, 0.00845537, -0.00234588, -0.00259763, -0.06820042]])

    video_path = 0  # 웹캠 사용
    cap = cv2.VideoCapture(video_path)
    focalLength = None
 
    KNOWN_DISTANCE = 11.81

    if not cap.isOpened():
        print("Video is unavailable :", video_path)
        exit(0) 

    while cap.isOpened():
        ret, image = cap.read()
    
        if not ret:
            break
        
        calibrated_image = cv2.undistort(image, mtx, dist, newCameraMatrix=mtx)

        results = model.predict(calibrated_image, conf=0.4, vid_stride=30, max_det = 3, verbose=False)

        if results[0].boxes is not None:

            object_boxes, cls_indices = get_bounding_boxes(results)

            for object_box, cls_index in zip(object_boxes, cls_indices):

                class_name = names[cls_index]

                if class_name in known_widths:
                    known_width = known_widths[class_name]
                    
                    perwidth = object_box[2] - object_box[0] # (x2 - x1)

                    if focalLength is None:
                        focalLength = (perwidth * KNOWN_DISTANCE) / known_width

                    distance = distance_to_camera(known_width, focalLength, perwidth)
                    cv2.rectangle(calibrated_image, (object_box[0], object_box[1]), (object_box[2], object_box[3]), (255,0,255), 2)
                    cv2.putText(calibrated_image, f"{(distance*2.48):.2f}cm", (object_box[0], object_box[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    cv2.putText(calibrated_image, class_name, (object_box[0], object_box[1] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)

        cv2.imshow("object detection", calibrated_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()