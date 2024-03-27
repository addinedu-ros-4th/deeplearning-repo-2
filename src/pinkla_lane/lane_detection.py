from ultralytics import YOLO
import cv2
import numpy as np


def get_centroid(polygon):
    area = 0
    centroid_x = 0
    centroid_y = 0
    
    for i in range(len(polygon)):
        j = (i + 1) % len(polygon)
        factor = polygon[i][0] * polygon[j][1] - polygon[j][0] * polygon[i][1]
        area += factor
        centroid_x += (polygon[i][0] + polygon[j][0]) * factor
        centroid_y += (polygon[i][1] + polygon[j][1]) * factor
    
    area /= 2.0
    
    centroid_x /= (6 * area)
    centroid_y /= (6 * area)
    
    return int(centroid_x), int(centroid_y)

def check_right_lane(arr):
    x_values = arr[:, 0]
    indices = []
    indices = np.where(x_values > 200)[0]
    
    if len(indices) == 0:
        result = False
    else:
        result = True
        
    return result


class find_load_center():
    def __init__(self):
        self.model = YOLO("../../data/bestyolov8m.pt")
        self.image = None
        self.seg_center1 = (0,0)
        self.seg_center2 = (0,0)
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)
        self.seg_center1_list = []
        self.seg_center2_list = []
        
 
    def get_load_center(self, image):
        self.seg_center1_list = []
        self.seg_center2_list = []
        self.image = image
        self.result = self.model.predict(source = self.image, conf=0.5)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        for mask, box in zip(self.segmentation,self.classes):
            if box.cls.item()==3:
                
                xy = mask.xy[0].astype("int") 
                cv2.polylines(self.image,[xy],isClosed=True,color=(255,0,0),thickness=2)
                self.seg_center1 = get_centroid(xy)
                self.seg_center1_list.append(self.seg_center1)

            elif box.cls.item()==0:
                
                xy = mask.xy[0].astype("int")
                if check_right_lane(xy):
                    cv2.polylines(self.image,[xy],isClosed=True,color=(0,0,255),thickness=2)
                    self.seg_center2 = get_centroid(xy)
                    self.seg_center2_list.append(self.seg_center2)
            else:
                pass
        
        
        if len(self.seg_center1_list) > 2:
            line_center = get_centroid(self.seg_center1_list)
        else:
            line_center = self.seg_center1
            
        
        load_center = (int((line_center[0] + self.seg_center2[0])/2), self.img_center_y)
        
        error = load_center[0]-(self.img_center_x)
        
        print(self.seg_center1, self.seg_center2)
        
        cv2.line(self.image, (self.seg_center1[0], self.img_center_y), (self.seg_center2[0], self.img_center_y), color = (0, 255, 0), thickness=2)
        cv2.circle(self.image, load_center, radius = 3, color = (0, 0, 255), thickness = -1)
        cv2.circle(self.image, (self.img_center_x, self.img_center_y), radius = 5, color = (255, 255, 255), thickness = -1)
        
        return self.image, error
