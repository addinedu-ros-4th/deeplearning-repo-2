from ultralytics import YOLO
import cv2
import numpy as np

# from pinkla_qt.comm_module import cmtx1, dist1

class find_object():
    def __init__(self):
        self.model = YOLO('../../data/best_yolos_object.pt')
        self.names = self.model.model.names
    # 실제 객체들의 너비값을 저장(지정된 객체만 검출 됨 / 단위 : inch)
        self.known_widths = {
            'car' : 4,
            'crosswalk' : 6.496,
            'green_light' : 1.969, # 1.378
            'human' : 1.969,
            'only_right_turn' : 2.36,
            'only_straight' : 2.36,
            'red_light' : 1.969,
            'start_line' : 7.087,
            'stop_line' : 4.331,
            'yellow_light' : 1.969
            }
        # self.KNOWN_DISTANCE = 11.81  # 객체와의 거리(초기에 검출되는 객체에 한해 입력 요구 / 단위 : inch)
        # KNOWN_WIDTH = 6.7  # 실제 객체의 너비

        self.focalLength = 478.87

    def get_bounding_boxes(self, results):
        # yolo 모델의 예측 결과에서 객체 boundary box와 클래스 명을 반환
        self.object_boxes = [] # 객체 bounding box를 저장할 리스트
        self.classes = [] # 클래스 명을 저장할 리스트
        self.confidences = []

        for result in results:
            bounding_boxes = result.boxes

            for box in bounding_boxes:
                x1, y1, x2, y2 = box.xyxy[0] # 바운딩 박스의 좌표 정보 추출
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cls = int(box.cls[0]) # 바운딩 박스에 대한 클래스 정보 추출
                conf = float(box.conf[0])
                self.object_boxes.append([x1, y1, x2, y2])
                self.classes.append(cls)
                self.confidences.append(conf)

        return self.object_boxes, self.classes, self.confidences

    def distance_to_camera(self, knownWidth, focalLength, perWidth):

        # 카메라와 객체 사이의 거리 계산
        # focalLength : 카메라의 초점 거리(초기 계산 이후 상수로 사용)
        # perWidth : 화면 상 객체의 너비(픽셀 값)

        self.distance = (knownWidth * focalLength) / perWidth
        return self.distance

    def calculate_depth(self, image):
        
        mtx = np.array([[479.02325822, 0., 300.28563966],
                        [0., 478.72152516, 232.33223961],
                        [0., 0., 1.]])
        dist = np.array([[-0.01884809, 0.00845537, -0.00234588, -0.00259763, -0.06820042]])

        self.image = image.copy()

        self.calibrated_image = cv2.undistort(self.image, mtx, dist, newCameraMatrix=mtx)

        # vid_stride : 연속된 프레임 사이 간격
        # 최대 감지 객체 개수 제한
        # verbose=False : 터미널 출력 제한
        results = self.model.predict(self.calibrated_image, conf=0.6, vid_stride=30, max_det = 10, verbose=False)
        # results = model.predict(source=image, conf=0.5)[0]

        # 첫 번째 프레임에서 객체가 감지된 경우
        if results[0].boxes is not None:
            object_boxes, cls_indices, confidences = self.get_bounding_boxes(results)

            for object_box, cls_index, confidence in zip(object_boxes, cls_indices, confidences):
                class_name = self.names[cls_index]

                if class_name in self.known_widths:
                    known_width = self.known_widths[class_name]
                    perwidth = object_box[2] - object_box[0] # (x2 - x1)
                    # 객체와 카메라 사이의 거리 계산
                    distance = self.distance_to_camera(known_width, self.focalLength, perwidth)
                    # 바운딩 박스와 거리 정보 영상에 표시
                    cv2.rectangle(self.calibrated_image, (object_box[0], object_box[1]), (object_box[2], object_box[3]), (255,0,255), 2)
                    cv2.putText(self.calibrated_image, f"{(distance*2.5126):.2f}cm, Conf: {confidence:.2f}", (object_box[0], object_box[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    # 클래스명 출력
                    cv2.putText(self.calibrated_image, class_name, (object_box[0], object_box[1] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)

        return self.calibrated_image
            
