from ultralytics import YOLO
import cv2
import numpy as np

def get_centroid(polygon):
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
    except ZeroDivisionError as e:
        print(e)
        centroid_x, centroid_y = 0, 0

    # except Exception as e:
    #     print(e)
    #     centroid_x, centroid_y = 0, 0

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


class find_load_center():
    def __init__(self):
        self.model = YOLO("../../data/bestyolov8n.pt")
        # self.model = YOLO("../../data/bestyolov8m.pt")
        self.image = None
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)

        self.roi_rect_start = (0, self.img_center_y - 100)
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

    def get_road_center(self, image):
        self.seg_center_middle_list = []
        self.seg_center_border_list = []
        self.seg_center_inter_list = []

        self.image = image.copy()
        
        ROI = self.image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]]
        self.zeros_image[self.roi_rect_start[1]:self.roi_rect_end[1], self.roi_rect_start[0]:self.roi_rect_end[0]] = ROI
        
        self.result = self.model.predict(source = self.zeros_image, conf=0.4, verbose=False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        try: 
            for mask, box in zip(self.segmentation, self.classes):
                # border line
                if box.cls.item()==0:
                    xy = mask.xy[0].astype("int")
                    if check_right_lane(xy):
                        centroid = np.mean(xy, axis=0).astype(int)
                        cv2.putText(self.image, text="test", org=(centroid[0], centroid[1]), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,255,255), thickness=2)
                        cv2.polylines(self.image,[xy],isClosed=True,color=(255,255,255),thickness=3)
                        self.seg_center_border = get_centroid(xy)
                        self.seg_center_border_list.append(self.seg_center_border)

                # intersection
                if box.cls.item()==1: 
                    xy = mask.xy[0].astype("int") 
                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,0,255),thickness=3)
                    self.seg_center_inter = get_centroid(xy)
                    self.seg_center_inter_list.append(self.seg_center_inter)

                # middle_line
                if box.cls.item()==2:
                    xy = mask.xy[0].astype("int")
                    if check_left_lane(xy):
                        cv2.polylines(self.image,[xy],isClosed=True,color=(0,255,255),thickness=3)
                        self.seg_center_middle = get_centroid(xy)
                        self.seg_center_middle_list.append(self.seg_center_middle)

        except TypeError as e:
            print("for mask, box in zip(self.segmentation,self.classes) : ", e)
            pass
        
        # middle line, intersection
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

        road_center = (int((self.line_center[0] + self.seg_center_border[0])/2), int(self.img_center_y*1.5))

        cv2.rectangle(self.image, self.roi_rect_start, self.roi_rect_end, color = (255, 0, 0), thickness = 8)
        cv2.line(self.image, (self.line_center[0], road_center[1]), (self.seg_center_border[0], road_center[1]), color = (0, 255, 0), thickness=2)
        cv2.circle(self.image, road_center, radius = 3, color = (0, 0, 255), thickness = -1)
        cv2.circle(self.image, (self.img_center_x, road_center[1]), radius = 5, color = (255, 255, 255), thickness = -1)
        
        self.error = road_center[0]-(self.img_center_x)

        print(self.status, self.line_center, road_center, self.error)
        # print(self.line_center)
        return self.image, self.error
