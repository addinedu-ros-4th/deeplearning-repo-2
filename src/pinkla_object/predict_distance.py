from ultralytics import YOLO
import cv2
import numpy as np

# from pinkla_qt.comm_module import cmtx1, dist1

class Find_Object():
    def __init__(self):
        self.model = YOLO('../../data/bestobjectv8n.pt')
        self.names = self.model.model.names
    # 실제 객체들의 너비값을 저장(지정된 객체만 검출 됨 / 단위 : inch)
        self.known_widths = {
            'car' : 3.543,
            'crosswalk' : 6.496,
            'green_light' : 1.654, # 1.378
            'human' : 2.165,
            'only_right_turn' : 2.165,
            'only_straight' : 2.165,
            'red_light' : 1.654,
            'start_line' : 7.48,
            'stop_line' : 4.724,
            'yellow_light' : 1.654
        }

        self.colors = {
            'car': (0, 111, 0), 
            'crosswalk': (140, 140, 140), 
            'green_light': (29, 219, 22),
            'human': (255, 228, 0), 
            'only_right_turn': (0, 216, 255),
            'only_straight': (95, 0, 255),
            'red_light': (241, 95, 95), 
            'start_line': (0, 165, 255),
            'stop_line': (255, 94, 0), 
            'yellow_light': (250, 237, 125)
        }

        self.focalLength = (470.86256773 + 470.89842857) / 2.0

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
                conf = float(box.conf[0]) # 바운딩 박스에 대한 confidence 점수 추출
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
        self.image = image.copy()
        object_boxes, cls_indices, confidences = [], [], []

        results = self.model.predict(self.image, conf=0.6, vid_stride=30, max_det = 5, verbose=False)

        obj_result = []
        obj_info = []

        # 첫 번째 프레임에서 객체가 감지된 경우
        if results[0].boxes is not None:
            object_boxes, cls_indices, confidences = self.get_bounding_boxes(results)

            for object_box, cls_index, confidence in zip(object_boxes, cls_indices, confidences):
                class_name = self.names[cls_index]
                if class_name in self.known_widths:
                    known_width = self.known_widths[class_name]
                    color = self.colors[class_name]

                    perwidth = object_box[2] - object_box[0] # (x2 - x1)
                    # 객체와 카메라 사이의 거리 계산
                    distance = self.distance_to_camera(known_width, self.focalLength, perwidth)
                    distance = distance*2.278
                    # 바운딩 박스와 거리 정보 영상에 표시

                    obj_info = [class_name, object_box, distance, confidence, color]

                    obj_result.append(obj_info)
                
                    # cv2.rectangle(self.image, (object_box[0], object_box[1]), (object_box[2], object_box[3]), color, 2)
                    # cv2.putText(self.image, f"{(distance):.2f}cm", (object_box[0], object_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 0, 0), 2)
                    # cv2.putText(self.image, f"Conf: {confidence:.2f}", (object_box[0], object_box[3] + 20), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 0), 2)
                    
                    # # 클래스명 출력
                    # cv2.putText(self.image, class_name, (object_box[0], object_box[1] - 30), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 2)

        return obj_result
