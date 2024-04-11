from ultralytics import YOLO
import cv2
import numpy as np
import math 

class Centroid():
    def __init__(self):
        self.centroid_x, self.centroid_y = 0, 0

    def get_centroid(self, polygon):
        area = 0
        self.centroid_x = 0
        self.centroid_y = 0
        n = len(polygon)

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


class find_road_center():
    def __init__(self):
        self.model = YOLO("../../data/bestyolov8n.pt")
        self.image = None
        self.seg_center0 = (0, 0)
        self.seg_center1 = (0, 0)
        self.seg_center2 = (0, 0)
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)
        self.roi_rect_start = (0, self.img_center_y - 100)
        self.roi_rect_end = (self.img_center_x * 2, int(self.img_center_y * 2))

        self.line_center = (0,0)
        self.seg_center_middle = (0,0)
        self.seg_center_border = (0,0)
        self.seg_center_inter = (0,0)
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []
        self.coordinate = []
        self.temp_border = None

        self.get_border_cen = Centroid()
        self.get_middle_cen = Centroid()
        self.get_inter_cen = Centroid()

        self.cnt_stop = 0

    def get_road_center(self, image):
        self.seg_center_middle_list.clear()
        self.seg_center_border_list.clear()
        self.seg_center_inter_list.clear()
        self.coordinate.clear()
        line_center_x, line_center_y = 0, 0

        self.image = image.copy()
        ROI = self.image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]]
        
        self.result = self.model.predict(source = ROI, conf=0.5, verbose=False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        for mask, box in zip(self.segmentation, self.classes):
            try:
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
                    self.seg_center_border = self.temp_border
            except Exception as e:
                print("border_line : ",e)
                pass

            try:
                if box.cls.item() == 1: 
                    xy = mask.xy[0].astype("int") 
                    self.seg_center_inter = self.get_inter_cen.get_centroid(xy)
                    self.seg_center_inter_list.append(self.seg_center_inter)
                    cv2.polylines(self.image,[xy],isClosed=True,color=(64,64,64),thickness=3)
                    cv2.circle(self.image, (int(self.seg_center_inter[0]), int(self.seg_center_inter[1])), radius=10, color=(64,64,64),thickness=-1)
                    cv2.putText(self.image, text="intersection", org=(self.seg_center_inter[0]-20, self.seg_center_inter[1]-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(64,64,64), thickness=2)
            except Exception as e:
                print("intersection : ",e)
                pass

            try:
                if box.cls.item() == 2:
                    xy = mask.xy[0].astype("int")
                    self.seg_center_middle = self.get_middle_cen.get_centroid(xy)
                    self.seg_center_middle_list.append(self.seg_center_middle)
                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,255,255),thickness=3)
                    cv2.circle(self.image, (int(self.seg_center_middle[0]), int(self.seg_center_middle[1])), radius=10, color=(0,255,255),thickness=-1)
                    cv2.putText(self.image, text="middle", org=(int(self.seg_center_middle[0])-20, int(self.seg_center_middle[1])-20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,255,255), thickness=2)
            except Exception as e:
                print("middle_line : ",e)
                pass


        self.coordinate.append(self.seg_center_border)
        self.coordinate.append(self.seg_center_inter)
        self.coordinate.append(self.seg_center_middle)
        
    

        if len(self.seg_center_inter_list) > 1:
            delta = self.seg_center_inter_list[0][0] - self.seg_center_inter_list[-1][0]
            if abs(delta) <= 10:
                avg_x = int((self.seg_center_inter_list[0][0] + self.seg_center_inter_list[-1][0])/2)
                avg_y = int((self.seg_center_inter_list[0][1] + self.seg_center_inter_list[-1][1])/2)
                self.seg_center_inter = (avg_x, avg_y)
            else:
                if self.seg_center_inter_list[0][0] > self.seg_center_inter_list[-1][0]:
                    self.seg_center_inter = self.seg_center_inter_list[0]
                else:
                    self.seg_center_inter = self.seg_center_inter_list[-1]
        else:
            pass


        if len(self.seg_center_middle_list) > 0 and len(self.seg_center_inter_list) > 0:
            line_center_x = int((self.seg_center_middle[0] + self.seg_center_inter[0])/2)
            line_center_y = int((self.seg_center_middle[1] + self.seg_center_inter[1])/2)
            
        elif len(self.seg_center_middle_list) == 0:
            line_center_x = self.seg_center_inter[0]
            line_center_y = self.seg_center_inter[1]
            
        else:
            line_center_x = self.seg_center_middle[0]
            line_center_y = self.seg_center_middle[1]


        if len(self.seg_center_border_list) > 1:
            if self.seg_center_border_list[0][0] > self.seg_center_border_list[-1][0]:
                self.seg_center_border = self.seg_center_border_list[0]
            else:
                self.seg_center_border = self.seg_center_border_list[-1]



        if self.seg_center_border[0] < 300:
            self.seg_center_border = self.temp_border

        if len(self.seg_center_border_list) == 0 and len(self.seg_center_inter_list) == 0 and len(self.seg_center_middle_list) == 0:
            self.cnt_stop += 1
        else:
            self.cnt_stop = 0
        
        
        
        seg_result = [line_center_x, line_center_y, self.seg_center_border, self.cnt_stop, self.coordinate]
        return self.image, seg_result