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
    except Exception as e:
        centroid_x, centroid_y = 0, 0

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
        self.alpha = 0.3
        self.error = 0
        
 
    def get_load_center(self, image):
        self.seg_center1_list = []
        self.seg_center2_list = []
        self.image = image
        
        roi_rect_start = (0, int(self.img_center_y))
        roi_rect_end = (self.img_center_x * 2, int(self.img_center_y * 1.75))
        
        ROI = self.image[roi_rect_start[1]:roi_rect_end[1], roi_rect_start[0]:roi_rect_end[0]]
        
        
        self.result = self.model.predict(source = ROI, conf=0.5, verbose=False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        try: 
            for mask, box in zip(self.segmentation,self.classes):
                if box.cls.item()==2:
                    
                    xy = mask.xy[0].astype("int") 
                    cv2.polylines(ROI,[xy],isClosed=True,color=(255,0,0),thickness=2)
                    self.seg_center1 = get_centroid(xy)
                    self.seg_center1_list.append(self.seg_center1)

                if box.cls.item()==0:
                    
                    xy = mask.xy[0].astype("int")
                    if check_right_lane(xy):
                        cv2.polylines(ROI,[xy],isClosed=True,color=(0,0,255),thickness=2)
                        self.seg_center2 = get_centroid(xy)
                        self.seg_center2_list.append(self.seg_center2)
                
                if box.cls.item()==1:
                    
                    xy = mask.xy[0].astype("int") 
                    cv2.polylines(ROI,[xy],isClosed=True,color=(0,255,0),thickness=2)

        except TypeError:
            pass
        
        
        if len(self.seg_center1_list) > 1:
            self.line_center = get_centroid(self.seg_center1_list)
        else:
            self.line_center = self.seg_center1
            
        
        load_center = (int((self.line_center[0] + self.seg_center2[0])/2), int(self.img_center_y*1.5))        
        
        overlay = self.image.copy()
        cv2.rectangle(self.image, roi_rect_start, roi_rect_end, color = (255, 0, 0), thickness = 2)
        
        self.error = load_center[0]-(self.img_center_x)

        print(self.error)
                
        cv2.line(self.image, (self.line_center[0], int(self.img_center_y*1.5)), (self.seg_center2[0], int(self.img_center_y*1.5)), color = (0, 255, 0), thickness=2)
        cv2.circle(self.image, load_center, radius = 3, color = (0, 0, 255), thickness = -1)
        cv2.circle(self.image, (self.img_center_x, int(self.img_center_y*1.5)), radius = 5, color = (255, 255, 255), thickness = -1)
        
        overlay = cv2.addWeighted(overlay, self.alpha, self.image, 1-self.alpha, 0)

        
        return overlay, self.error
