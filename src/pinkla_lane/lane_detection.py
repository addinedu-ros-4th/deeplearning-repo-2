from ultralytics import YOLO
import cv2
import numpy as np
temp_x, temp_y = 0,0

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

lpf_x = LowPassFilter(5.0, 5)
lpf_y = LowPassFilter(5.0, 5)
lpf_e = LowPassFilter(1.0, 0.5)
lpf_t0 = LowPassFilter(5.0, 0.5)
lpf_t1 = LowPassFilter(5.0, 0.5)

lpf_x1 = LowPassFilter(5.0, 5)
lpf_y1 = LowPassFilter(5.0, 5)


def get_centroid(polygon):
    global temp_x, temp_y
    # centroid_x, centroid_y = 0, 0
    # centroid = np.mean(polygon, axis=0).astype(int)

    # centroid_x = centroid[0]
    # centroid_y = centroid[1]

    area = 0
    centroid_x = 0
    centroid_y = 0
    try:
        for i in range(len(polygon)):
            j = (i + 1) % len(polygon)
            factor = polygon[i][0] * polygon[j][1] - polygon[j][0] * polygon[i][1]
            area += factor
            centroid_x += (polygon[i][0] + polygon[j][0]) * factor
            centroid_y += (polygon[i][1] + polygon[j][1]) * factor
        
        area /= 2.0

        centroid_x /= (6 * area)
        centroid_y /= (6 * area)

        centroid_x = lpf_x1.filter(centroid_x)
        centroid_y = lpf_y1.filter(centroid_y)


        temp_x = centroid_x
        temp_y = centroid_y
    except ZeroDivisionError as e:
        # print(e)
        # centroid_x, centroid_y = 0, 0
        centroid_x, centroid_y = temp_x, temp_y

    return [int(centroid_x), int(centroid_y)]

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

def get_points(polygon):
    # total_length = 0
    # cumulative_lengths = []

    # for i in range(len(polygon)):
    #     x1, y1 = polygon[i]
    #     x2, y2 = polygon[(i + 1) % len(polygon)]  # 다음 점
    #     length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    #     total_length += length
    #     cumulative_lengths.append(total_length)

    # # one_third_length = total_length - 120
    # # one_third_length = total_length / 3 + total_length / 2
    # one_third_length = total_length * 1/3
        

    # for i in range(len(cumulative_lengths)):
    #     if cumulative_lengths[i] >= one_third_length:
    #         x1, y1 = polygon[i]
    #         x2, y2 = polygon[(i + 1) % len(polygon)]
    #         ratio = (one_third_length - cumulative_lengths[i-1]) / (cumulative_lengths[i] - cumulative_lengths[i-1])
    #         x_one_third = x1 + ratio * (x2 - x1)
    #         y_one_third = y1 + ratio * (y2 - y1)
    #         break

    # x = x_one_third - 20
    # y = y_one_third

    centroid = np.mean(polygon, axis=0).astype(int)

    x = centroid[0]
    y = centroid[1]

    x = lpf_x.filter(x)
    y = lpf_y.filter(y)
    return x, y


class find_load_center():
    def __init__(self):
        self.model = YOLO("../../data/bestyolov8n.pt")
        # self.model = YOLO("../../data/bestyolov8m.pt")
        self.image = None
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)

        self.roi_rect_start = (0, self.img_center_y - 80)
        self.roi_rect_end = (self.img_center_x * 2, int(self.img_center_y * 1.99))
        # roi_rect_center_y = (int(self.roi_rect_start[1]+self.roi_rect_end[1])/2)
        # roi_upside = [(0, 0), (self.img_center_x*2, int(self.img_center_y)-130)]
        # roi_downside = ((0, int(self.img_center_y * 1.75)), (self.img_center_x*2, self.img_center_y*2))

        self.seg_center_middle = (0,0)
        self.seg_center_border = (0,0)
        self.seg_center_inter = (0,0)
        
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []

        self.line_center = (0, 0)

        self.alpha = 0.3
        self.error = 0

        self.status = ""

        self.zeros_image = np.zeros((480, 640, 3)).astype(np.uint8)
        self.zeros_image[:, :] = [0, 0, 255]
        self.value = [0.,0.,0.,0.]

        self.temp = None

    def get_road_center(self, image):
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []

        self.border_list = []
        self.middle_list = []
        self.inter_list = []

        self.image = image.copy()
        ROI = self.image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]]
        self.zeros_image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]] = ROI
        self.result = self.model.predict(source = self.zeros_image, conf=0.5, verbose=False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        try: 
            for mask, box in zip(self.segmentation, self.classes):
                # border_line
                if box.cls.item()==0:
                    xy = mask.xy[0].astype("int")
                    test1 = get_points(xy)
                    cv2.circle(self.image, (int(test1[0]), int(test1[1])), radius=10, color=(255,255,255),thickness=-1)

                    if check_right_lane(xy):
                        self.border_list.append(test1)
                        centroid = np.mean(xy, axis=0).astype(int)
                        cv2.putText(self.image, text="border", org=(centroid[0]-20, centroid[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,255,255), thickness=2)
                        cv2.polylines(self.image,[xy],isClosed=True,color=(255,255,255),thickness=3)
                        self.seg_center_border = get_centroid(xy)
                        self.seg_center_border_list.append(self.seg_center_border)
                        self.temp = self.seg_center_border
                else:
                    self.seg_center_border = (640, 240)
                    pass


                # intersection
                if box.cls.item()==1: 
                    xy = mask.xy[0].astype("int") 
                    centroid = np.mean(xy, axis=0).astype(int)
                    cv2.putText(self.image, text="intersection", org=(centroid[0]-20, centroid[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2)

                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,0,255),thickness=3)
                    self.seg_center_inter = get_centroid(xy)
                    self.seg_center_inter_list.append(self.seg_center_inter)

                    test1 = get_points(xy)
                    cv2.circle(self.image, (int(test1[0]), int(test1[1])), radius=10, color=(0,0,255),thickness=-1)
                    if check_right_lane(xy):
                        self.inter_list.append(test1)

                # middle_line
                if box.cls.item()==2:
                    xy = mask.xy[0].astype("int")
                    centroid = np.mean(xy, axis=0).astype(int)
                    cv2.putText(self.image, text="middle", org=(centroid[0]-20, centroid[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,255,255), thickness=2)

                    test1 = get_points(xy)
                    cv2.circle(self.image, (int(test1[0]), int(test1[1])), radius=10, color=(0,255,255),thickness=-1)
                    # if check_left_lane(xy):
                    self.middle_list.append(test1)
                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,255,255),thickness=3)
                    self.seg_center_middle = get_centroid(xy)
                    self.seg_center_middle_list.append(self.seg_center_middle)

        except TypeError as e:
            # print("for mask, box in zip(self.segmentation,self.classes) : ", e)
            pass
    

        # 인터섹션 2개 검출 시, 왼쪽/오른쪽 선택
        if len(self.seg_center_inter_list) > 1:
            # x = int((self.seg_center1_list[0][0] + self.seg_center1_list[-1][0])/2)
            # y = int((self.seg_center1_list[0][1] + self.seg_center1_list[-1][1])/2)
            # self.seg_center1 = (x,y)
            
            if self.seg_center_inter_list[0][0]>self.seg_center_inter_list[-1][0]:
                self.seg_center_inter = self.seg_center_inter_list[0]
            else:
                self.seg_center_inter = self.seg_center_inter_list[-1]
            
        else:
            pass

        # 하드코딩이고, 2개 동시 검출시 우선순위 따지는 부분 (미들>인터섹션>)
        # 두개 동시 검출 시 (미들, 인터) => 평균값 사용
        if len(self.seg_center_middle_list) > 0 and len(self.seg_center_inter_list) > 0:
            # line_center = (640-self.seg_center0[0], roi_rect_center_y+100)
            # load_center = int(self.seg_center1[0]*2/3)
            line_center = int((self.seg_center_middle[0] + self.seg_center_inter[0])/2)
            # road_center = int((line_center + self.seg_center_border[0])/2.5)

            # if self.seg_center1[0] > self.seg_center2[0] and self.seg_center1[0]-self.seg_center2[0] > 50:
                
            #     road_center = int((self.seg_center2[0] + 2*self.seg_center1[0])/3.5)
            # else:
            #     road_center =  int((self.seg_center1[0] + self.seg_center0[0])/2) 
            
        # 미들 검출 X => 인터 섹션을 왼쪽 차선
        elif len(self.seg_center_middle_list) == 0:
            line_center = self.seg_center_inter[0]
            # road_center = int((self.seg_center_inter[0] + self.seg_center_border[0])/2) 
            
        # 미들 검출 O => 미들 라인을 왼쪽 차선
        else:
            line_center = self.seg_center_middle[0]
            # road_center = int((self.seg_center_middle[0] + self.seg_center_border[0])/2) 
        



        # middle line, intersection 우선 순위
        if len(self.seg_center_middle_list) > 0:
            self.status = "using middle_line"
            self.line_center = self.seg_center_middle_list[0]
        else:
            if len(self.seg_center_inter_list) > 0:
                self.status = "using intersection"
                self.line_center = self.seg_center_inter_list[0]
            else:
                self.status = "None"
                self.line_center = self.seg_center_border
                self.border_list.append(self.line_center)


        # if len(self.middle_list) > 0:
        #     self.test = self.middle_list[0]
        # else:
        #     if len(self.inter_list) > 0:
        #         self.test = self.inter_list[0]
        #     else:
        #         if len(self.border_list) > 0:
        #             self.test = (self.border_list[0][0]/2, self.border_list[0][1])

        try:
            # print(self.test, self.border_list)
            # x = lpf_t0.filter(self.test[0])
            # y = lpf_t1.filter(self.test[1])
            x = lpf_t0.filter(line_center)
            y = lpf_t1.filter(self.line_center[1])

            # cv2.line(self.image, (int(self.test[0]), int(self.test[1])), (int(self.border_list[0][0]), int(self.border_list[0][1])), color=(128,128,128), thickness=5 )
            cv2.line(self.image, (int(x), int(y)), (int(self.border_list[0][0]), int(self.border_list[0][1])), color=(64,64,64), thickness=5 )

            cen_x = (x + self.border_list[0][0]) / 2
            cen_y = (y + self.border_list[0][1]) / 2
            cv2.circle(self.image, (int(cen_x), int(cen_y)), radius=10, color=(0,0,255), thickness=-1)

            # target_pos - robot_pos
            # delta_x = cen_x - self.img_center_x
            # delta_y = cen_y - (self.roi_rect_end[1] - 50)

            delta_x = self.img_center_x - cen_x
            delta_y = (self.roi_rect_end[1] - 50) - cen_y

            # distance = np.sqrt(delta_x**2 + delta_y**2) * 0.1
            angle = np.arctan2(delta_x, delta_y)

            target_pos = np.array([int(cen_x), int(cen_y)])
            # robot_pos = np.array([self.img_center_x, int(self.roi_rect_end[1] - 50)])
            robot_pos = np.array([self.img_center_x - 20, int(self.roi_rect_end[1] + 70)])
            
            distance = np.linalg.norm(robot_pos - target_pos)

            max_lin_x_vel = 1.8
            max_lin_y_vel = 1.8
            
            max_distance = 100
            vx = max_lin_x_vel * (distance / max_distance)
            vz = angle * 50.0

            test_x = robot_pos[0] - distance * np.sin(angle)
            test_y = robot_pos[1] - distance * np.cos(angle)

            cv2.arrowedLine(self.image, (int(robot_pos[0]), int(robot_pos[1])), (int(test_x), int(test_y)), color=(255,0,0), thickness=5, tipLength=0.2)

            self.w1 = (1/0.025) * (vx-0.08*vz) # = 40 * vx - 3.2 * vz
            self.w2 = (1/0.025) * (vx-0.08*vz)
            self.w3 = (1/0.025) * (vx+0.08*vz)
            self.w4 = (1/0.025) * (vx+0.08*vz)


            # if distance < 70 and self.status =="None":
            #     self.value = [0., 0., 0., 0.]
            # else:
            #     self.value = [self.w4, self.w3, self.w2, self.w1]

            self.value = [self.w4, self.w3, self.w2, self.w1]
            

            cv2.putText(self.image, text=f"{self.value[0]:.2f}, {self.value[1]:.2f}, {self.value[2]:.2f}, {self.value[3]:.2f}", org=(50, 40), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(self.image, text=f"{vx:.2f}, {vz:.2f}", org=(50, 70), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(self.image, text=f"{delta_x:.2f}, {delta_y:.2f}", org=(50, 100), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(self.image, text=f"distance: {distance:.2f}, angle: {angle:.2f}", org=(50, 130), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)


        except Exception as e:
            print(e)
            pass

        # road_center = (int((self.line_center[0] + self.seg_center_border[0])/2), int(self.roi_rect_end[1]/1.5)+100)

        cv2.rectangle(self.image, self.roi_rect_start, self.roi_rect_end, color = (255, 0, 0), thickness = 8)
        # cv2.line(self.image, (self.line_center[0], road_center[1]), (self.seg_center_border[0], road_center[1]), color = (0, 255, 0), thickness=2)
        # cv2.circle(self.image, road_center, radius = 3, color = (0, 0, 255), thickness = -1)
        # cv2.circle(self.image, (self.img_center_x, int(self.roi_rect_end[1]/1.5)), radius = 5, color = (255, 255, 255), thickness = -1)
        cv2.circle(self.image, (self.img_center_x, int(self.roi_rect_end[1] - 50)), radius = 5, color = (255, 255, 255), thickness = -1)

        
        # self.error = road_center[0]-(self.img_center_x)

        # error = lpf_e.filter(self.error)

        # print(self.status, self.line_center, road_center, self.error, error)
        # print(self.line_center)
        # return self.image, self.error
        # return self.image, error

        return self.image, self.value


