from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO('best.pt')
names = model.model.names

def get_bounding_boxes(results):

    #yolo 모델의 예측 결과에서 객체 boundary box와 클래스 명을 반환

    object_boxes = [] # 객체 bounding box를 저장할 리스트
    classes = [] # 클래스 명을 저장할 리스트

    for result in results:

        bounding_boxes = result.boxes

        for box in bounding_boxes:

            x1, y1, x2, y2 = box.xyxy[0] # 바운딩 박스의 좌표 정보 추출

            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            cls = int(box.cls[0]) # 바운딩 박스에 대한 클래스 정보 추출

            object_boxes.append([x1, y1, x2, y2])

            classes.append(cls)

    return object_boxes, classes


def distance_to_camera(knownWidth, focalLength, perWidth):

    # 카메라와 객체 사이의 거리 계산
    # focalLength : 카메라의 초점 거리(초기 계산 이후 상수로 사용)
    # perWidth : 화면 상 객체의 너비(픽셀 값)

    distance = (knownWidth * focalLength) / perWidth
    return distance

# 실제 객체들의 너비값을 저장(지정된 객체만 검출 됨 / 단위 : inch)
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
 
    KNOWN_DISTANCE = 11.81  # 객체와의 거리(초기에 검출되는 객체에 한해 입력 요구 / 단위 : inch)
    # KNOWN_WIDTH = 6.7  # 실제 객체의 너비

    if not cap.isOpened():
        print("Video is unavailable :", video_path)
        exit(0) 

    while cap.isOpened():
        ret, image = cap.read()
    
        if not ret:
            break
        
        calibrated_image = cv2.undistort(image, mtx, dist, newCameraMatrix=mtx)

        # vid_stride : 연속된 프레임 사이 간격
        # 최대 감지 객체 개수 제한
        # verbose=False : 터미널 출력 제한
        results = model.predict(calibrated_image, conf=0.4, vid_stride=30, max_det = 3, verbose=False)
        # results = model.predict(source=image, conf=0.5)[0]

        # 첫 번째 프레임에서 객체가 감지된 경우
        if results[0].boxes is not None:

            object_boxes, cls_indices = get_bounding_boxes(results)

            for object_box, cls_index in zip(object_boxes, cls_indices):

                class_name = names[cls_index]

                if class_name in known_widths:
                    known_width = known_widths[class_name]
                    
                    perwidth = object_box[2] - object_box[0] # (x2 - x1)

                    # 초점 거리 계산 (초기 프레임에서만 계산)
                    if focalLength is None:
                        focalLength = (perwidth * KNOWN_DISTANCE) / known_width

                    # 객체와 카메라 사이의 거리 계산
                    distance = distance_to_camera(known_width, focalLength, perwidth)

                    # 바운딩 박스와 거리 정보 영상에 표시
                    cv2.rectangle(calibrated_image, (object_box[0], object_box[1]), (object_box[2], object_box[3]), (255,0,255), 2)
                    cv2.putText(calibrated_image, f"{(distance*2.48):.2f}cm", (object_box[0], object_box[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    
                    # 클래스명 출력
                    cv2.putText(calibrated_image, class_name, (object_box[0], object_box[1] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)

        cv2.imshow("object detection", calibrated_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


    # 하나의 객체에 한해서만 검출(초기버전)
    # video_path = 0  # 웹캠 사용
    # cap = cv2.VideoCapture(video_path)
    # focalLength = None

    # # 초기 입력 요구
    # KNOWN_DISTANCE = 17.7165  # 객체와의 거리
    # KNOWN_WIDTH = 6.7  # 실제 객체의 폭


    # if not cap.isOpened():
    #     print("Video is unavailable :", video_path)
    #     exit(0) 

    # while cap.isOpened():
    #     ret, image = cap.read()

    #     if not ret:
    #         break

    #     # results = model.predict(source=image, conf=0.5)[0]
    #     results = model.predict(image, conf=0.4, vid_stride=30, max_det = 1)

    #     if results[0].boxes is not None:

    #         object_boxes, cls = get_bounding_boxes(results)

    #         for object_box in object_boxes:

    #             perwidth = object_box[2] - object_box[0]
                
    #             # 초점 거리 계산 (초기 프레임에서만 계산)
    #             if focalLength is None:
                
    #                 focalLength = (perwidth * KNOWN_DISTANCE) / KNOWN_WIDTH

    #             # 객체와 카메라 사이의 거리 계산
    #             distance = distance_to_camera(KNOWN_WIDTH, focalLength, perwidth)

    #             # 바운딩 박스와 거리 정보 영상에 표시
    #             cv2.rectangle(image, (object_box[0], object_box[1]), (object_box[2], object_box[3]), (255,0,255), 1)
    #             cv2.putText(image, f"{(distance*24/9):.2f}cm", (object_box[0], object_box[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    #             class_name = names[cls_index]
    #             cv2.putText(image, class_name, [object_box[0], object_box[1]], cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 1)

    #     cv2.imshow("object detection", image)
        
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break

    # cap.release()
    # cv2.destroyAllWindows()