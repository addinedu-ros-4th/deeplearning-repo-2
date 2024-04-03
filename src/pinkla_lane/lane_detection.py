from ultralytics import YOLO
import cv2
import numpy as np
import math 


class LowPassFilter(object):
    def __init__(self, cut_off_freqency, ts):
    	# cut_off_freqency: 차단 주파수
        # ts: 주기
        
        self.ts = ts
        self.cut_off_freqency = cut_off_freqency
        self.tau = self.get_tau()

        self.prev_data = 0.
        
    def get_tau(self):
        return 1 / (2 * np.pi * self.cut_off_freqency)

    def filter(self, data):
        val = (self.ts * data + self.tau * self.prev_data) / (self.tau + self.ts)
        self.prev_data = val
        return val 


class Centroid():
    def __init__(self):
        self.temp_x, self.temp_y = 0, 0
        self.centroid_x, self.centroid_y = 0, 0

    def get_centroid(self, polygon):
        area = 0
        self.centroid_x = 0
        self.centroid_y = 0
        n = len(polygon)

        try:
            for i in range(n):
                j = (i + 1) % n
                factor = polygon[i][0] * polygon[j][1] - polygon[j][0] * polygon[i][1]
                area += factor
                self.centroid_x += (polygon[i][0] + polygon[j][0]) * factor
                self.centroid_y += (polygon[i][1] + polygon[j][1]) * factor
            area /= 2.0
            if area != 0:
                self.centroid_x /= (6 * area)
                self.centroid_y /= (6 * area)
                self.temp_x, self.temp_y = self.centroid_x, self.centroid_y
            else:
                raise ZeroDivisionError("Polygon area is zero")
            return [int(self.centroid_x), int(self.centroid_y)]
            
        except ZeroDivisionError as e:
            self.centroid_x, self.centroid_y = self.temp_x, self.temp_y
            return [int(self.centroid_x), int(self.centroid_y)]
        except Exception as e:
            print("get_centroid Exc Error : ", e)
            return [0, 0]

def check_right_lane(arr):
    x_values = arr[:, 0]
    indices = []
    indices = np.where(x_values > 200)[0]
    
    if len(indices) == 0:
        result = False
    else:
        result = True
    return result

def check_left_lane(arr):
    x_values = arr[:, 0]
    indices = []
    indices = np.where(x_values < 200)[0]
    
    if len(indices) == 0:
        result = False
    else:
        result = True
    return result


lpf_x = LowPassFilter(5.0, 1)
lpf_y = LowPassFilter(5.0, 1)
lpf_dx = LowPassFilter(0.1, 0.5)
lpf_dy = LowPassFilter(0.1, 0.5)


class find_road_center():
    def __init__(self):
        self.model = YOLO("../../data/bestyolov8n.pt")
        # self.model = YOLO("../../data/bestyolov8m.pt")
        self.image = None
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)

        self.roi_rect_start = (0, self.img_center_y - 100)
        self.roi_rect_end = (self.img_center_x * 2, int(self.img_center_y * 2))

        self.seg_center_middle = (0,0)
        self.seg_center_border = (0,0)
        self.seg_center_inter = (0,0)
        
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []

        self.line_center = (0, 0)

        self.alpha = 0.3

        self.zeros_image = np.zeros((480, 640, 3)).astype(np.uint8)
        self.zeros_image[:, :] = [0, 0, 255]
        self.value = [0.,0.,0.,0.]

        self.temp_border = None

        self.get_border_cen = Centroid()
        self.get_middle_cen = Centroid()
        self.get_inter_cen = Centroid()

        self.cnt_stop = 0
        self.w4, self.w3, self.w2, self.w1 = 0,0,0,0

    def get_road_center(self, image):
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []

        self.image = image.copy()
        ROI = self.image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]]
        self.zeros_image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]] = ROI
        self.result = self.model.predict(source = self.zeros_image, conf=0.5, verbose=False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        try:
            for mask, box in zip(self.segmentation, self.classes):
                # border_line
                if box.cls.item() == 0:
                    xy = mask.xy[0].astype("int")
                    if check_right_lane(xy):
                        self.seg_center_border = self.get_border_cen.get_centroid(xy)
                        self.seg_center_border_list.append(self.seg_center_border)

                        cv2.polylines(self.image,[xy],isClosed=True,color=(255,255,255),thickness=3)
                        cv2.circle(self.image, (int(self.seg_center_border[0]), int(self.seg_center_border[1])), radius=10, color=(255,255,255),thickness=-1)
                        cv2.putText(self.image, text="border", org=(self.seg_center_border[0]-20, self.seg_center_border[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,255,255), thickness=2)
                        
                        if self.seg_center_border[0] >= 300:
                            self.temp_border = self.seg_center_border
                else:
                    # self.seg_center_border = (640, 240)
                    self.seg_center_border = self.temp_border
                    pass

                # intersection
                if box.cls.item() == 1: 
                    xy = mask.xy[0].astype("int") 
                    self.seg_center_inter = self.get_inter_cen.get_centroid(xy)
                    self.seg_center_inter_list.append(self.seg_center_inter)
                    
                    cv2.polylines(self.image,[xy],isClosed=True,color=(64,64,64),thickness=3)
                    cv2.circle(self.image, (int(self.seg_center_inter[0]), int(self.seg_center_inter[1])), radius=10, color=(64,64,64),thickness=-1)
                    cv2.putText(self.image, text="intersection", org=(self.seg_center_inter[0]-20, self.seg_center_inter[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(64,64,64), thickness=2)

                # middle_line
                if box.cls.item() == 2:
                    xy = mask.xy[0].astype("int")
                    self.seg_center_middle = self.get_middle_cen.get_centroid(xy)
                    self.seg_center_middle_list.append(self.seg_center_middle)

                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,255,255),thickness=3)
                    cv2.circle(self.image, (int(self.seg_center_middle[0]), int(self.seg_center_middle[1])), radius=10, color=(0,255,255),thickness=-1)
                    cv2.putText(self.image, text="middle", org=(int(self.seg_center_middle[0])-20, int(self.seg_center_middle[1])-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,255,255), thickness=2)

        except TypeError as e:
            # print("for mask, box in zip(self.segmentation,self.classes) : ", e)
            pass
    

        # 인터섹션 2개 검출 시, 왼쪽/오른쪽 선택
        if len(self.seg_center_inter_list) > 1:
            # 평균 사용
            # x = int((self.seg_center1_list[0][0] + self.seg_center1_list[-1][0])/2)
            # y = int((self.seg_center1_list[0][1] + self.seg_center1_list[-1][1])/2)
            # self.seg_center_inter = (x,y)

            # 두 x 좌표의 차이가 10이하 일 때, 아래 또는 평균 사용
            delta = self.seg_center_inter_list[0][0] - self.seg_center_inter_list[-1][0]
            if abs(delta) <= 10:
                avg_x = int((self.seg_center_inter_list[0][0] + self.seg_center_inter_list[-1][0])/2)
                avg_y = int((self.seg_center_inter_list[0][1] + self.seg_center_inter_list[-1][1])/2)
                self.seg_center_inter = (avg_x, avg_y)
            else:
            # 둘 중 더 오른쪽에 있는 놈 사용
                if self.seg_center_inter_list[0][0] > self.seg_center_inter_list[-1][0]:
                    self.seg_center_inter = self.seg_center_inter_list[0]
                else:
                    self.seg_center_inter = self.seg_center_inter_list[-1]
        else:
            pass


        # (미들, 인터) 2개 동시 검출 시 우선순위를 구분하자면 : 미들 > 인터섹션
        # (미들, 인터) 두개 동시 검출 시 => 평균값 사용
        if len(self.seg_center_middle_list) > 0 and len(self.seg_center_inter_list) > 0:
            line_center_x = int((self.seg_center_middle[0] + self.seg_center_inter[0])/2)
            line_center_y = int((self.seg_center_middle[1] + self.seg_center_inter[1])/2)
            
        # 미들 검출 X => 인터 섹션을 왼쪽 차선으로
        elif len(self.seg_center_middle_list) == 0:
            line_center_x = self.seg_center_inter[0]
            line_center_y = self.seg_center_inter[1]
            
        # 미들 검출 O => 미들 라인을 왼쪽 차선으로
        else:
            line_center_x = self.seg_center_middle[0]
            line_center_y = self.seg_center_middle[1]


        # middle 라인 2개 이상 검출 시, 우선 순위 : 오른쪽 > 왼쪽
        if len(self.seg_center_border_list) > 1:
            if self.seg_center_border_list[0][0] > self.seg_center_border_list[-1][0]:
                self.seg_center_border = self.seg_center_border_list[0]
            else:
                self.seg_center_border = self.seg_center_border_list[-1]


        # 최종 선정 된 기준 선 정보를 임시 저장하고, 값이 튀는 것을 방지해야 함


        # thk test
        vx,vy,vz = 0.,0.,0.
        try:
            hor_ang = math.radians(1)
            ver_ang = math.radians(-18)
            cam_h = 0.08
            cam_shift = 0.06
            hor_pixel_per_deg = 640 / math.degrees(hor_ang)
            ver_pixel_per_deg = 640 / math.degrees(ver_ang)

            # 우측 차선 주행 중, 갑자기 왼쪽 border_line만 검출 시 -> 우측으로 rotation 필요. 오른쪽 border_line 이전 값 적용
            if self.seg_center_border[0] < 300:
                self.seg_center_border = self.temp_border

            x = lpf_x.filter(line_center_x)
            y = lpf_y.filter(line_center_y)

            cen_x = (x + self.seg_center_border[0]) / 2
            cen_y = (y + self.seg_center_border[1]) / 2

            # target_pos - robot_pos
            delta_x_t = self.img_center_x - cen_x
            delta_y_t = (self.roi_rect_end[1]) - cen_y

            delta_x = lpf_dx.filter(delta_x_t)
            delta_y = lpf_dy.filter(delta_y_t)

            target_pos = np.array([int(cen_x), int(cen_y)])
            robot_pos = np.array([self.img_center_x, int(self.roi_rect_end[1])])
            # robot_pos = np.array([self.img_center_x, int(self.roi_rect_end[1] - 50)])
            
            # distance = np.linalg.norm(robot_pos - target_pos)
            distance = np.sqrt(delta_x**2 + delta_y**2)
            angle = np.arctan2(delta_x, delta_y)

            # hor_dist = delta_x / hor_pixel_per_deg
            hor_dist = delta_x / 10 * -1
            ver_dist = (delta_y / ver_pixel_per_deg)  + (cam_shift * 100 * -1)
            dist = math.sqrt(hor_dist**2 + ver_dist**2 + cam_h **2)


            # max_lin_x = 1.8
            # max_lin_y = 1.8
            # max_distance = 100
            # vx = max_lin_x * (distance / max_distance)
            # vz = angle * 50.0

            max_distance = 10

            max_lin_x = abs(ver_dist / max_distance) * 3.2
            max_lin_y = abs(hor_dist / max_distance / 1.54) * 2.7
            
            vx = (ver_dist / (abs(ver_dist) + abs(hor_dist)) * max_lin_x) * -1
            vy = (hor_dist / (abs(ver_dist) + abs(hor_dist)) * max_lin_y) * -1
            vz = angle * 11.1
            # print(max_lin_x, max_lin_y, vx, vy, vz)


            test_x = robot_pos[0] - distance * np.sin(angle)
            test_y = robot_pos[1] - distance * np.cos(angle)


            self.w1 = (1/0.025) * (vx-vy-0.11*vz)
            self.w2 = (1/0.025) * (vx+vy-0.11*vz)
            self.w3 = (1/0.025) * (vx-vy+0.11*vz)
            self.w4 = (1/0.025) * (vx+vy+0.11*vz)

            
        except Exception as e:
            print(e)
            pass

        # print(distance, dist, hor_dist, ver_dist)

        if len(self.seg_center_border_list) == 0 and len(self.seg_center_inter_list) == 0 and len(self.seg_center_middle_list) == 0:
            print("stoping")
            self.cnt_stop += 1
            if self.cnt_stop > 20:
                self.value = [0., 0., 0., 0.]
        else:
            self.value = [self.w4, self.w3, self.w2, self.w1]
            self.cnt_stop = 0

        # print(len(self.seg_center_border_list),len(self.seg_center_inter_list),len(self.seg_center_middle_list), self.cnt_stop)
        cv2.putText(self.image, text=f"{self.value[0]:.2f}, {self.value[1]:.2f}, {self.value[2]:.2f}, {self.value[3]:.2f}", org=(50, 40), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
        try:
            cv2.rectangle(self.image, self.roi_rect_start, self.roi_rect_end, color = (255, 0, 0), thickness = 8)

            cv2.line(self.image, (int(x)+5, int(y)), (int(self.seg_center_border[0])-5, int(self.seg_center_border[1])), color=(128,128,128), thickness=5 )

            cv2.putText(self.image, text=f"linear_y: {vy:.2f}, linear_x: {vx:.2f}, angular_z: {vz:.2f}", org=(50, 70), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(self.image, text=f"delta_x: {hor_dist:.2f}, delta_y: {ver_dist:.2f}, angle: {angle:.2f}", org=(50, 100), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(self.image, text=f"distance: {distance:.2f}", org=(50, 130), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)

            cv2.putText(self.image, text="target", org=(int(cen_x-20), int(cen_y-20)), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2)

            cv2.circle(self.image, (int(cen_x), int(cen_y)), radius=10, color=(0,0,255), thickness=-1)
            cv2.arrowedLine(self.image, (self.img_center_x, int(self.roi_rect_end[1])+5), (int(cen_x), int(cen_y)), color=(50,50,50), thickness=5, tipLength=0.2)
            cv2.circle(self.image, (self.img_center_x, int(self.roi_rect_end[1])), radius = 10, color = (255, 255, 255), thickness = -1)
        except Exception as e:
            print(e)
            pass        

        return self.image, self.value


