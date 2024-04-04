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
        self.model = YOLO("../../data/0402_seg_n_best.pt")
        self.image = None
        self.seg_center0 = (0, 0)
        self.seg_center1 = (0, 0)
        self.seg_center2 = (0, 0)
        self.img_center_x = int(640/2)
        self.img_center_y = int(480/2)
        self.alpha = 0.3
        self.error = 0
        
        self.coordinate = []
        
 
    def get_road_center(self, image):
        self.seg_center0_list = []
        self.seg_center1_list = []
        self.seg_center2_list = []
        self.coordinate = []
        self.image = image
        
        roi_rect_start = (0, int(self.img_center_y-130))
        roi_rect_end = (self.img_center_x * 2, int(self.img_center_y * 1.75))
        roi_rect_center_y = int((roi_rect_start[1]+roi_rect_end[1])/2)
        
        ROI = self.image[roi_rect_start[1]:roi_rect_end[1], roi_rect_start[0]:roi_rect_end[0]]
        
        
        self.result = self.model.predict(source = ROI, conf=0.5, verbose = False)[0]
        self.classes = self.result.boxes
        self.segmentation = self.result.masks
        
        try: 
            for mask, box in zip(self.segmentation,self.classes):
                if box.cls.item()==0:
                    
                    xy = mask.xy[0].astype("int")
                    if check_right_lane(xy):
                        cv2.polylines(ROI,[xy],isClosed=True,color=(0,0,255),thickness=2)
                        
                        self.seg_center0 = get_centroid(xy)
                        self.seg_center0_list.append(self.seg_center1)
                    
                elif box.cls.item()==1:
                    xy = mask.xy[0].astype("int") 
                    cv2.polylines(ROI,[xy],isClosed=True,color=(255,0,0),thickness=2)
                    self.seg_center1 = get_centroid(xy)
                    self.seg_center1_list.append(self.seg_center1)
                    
                    
                    
                elif box.cls.item()==2:
                    xy = mask.xy[0].astype("int") 
                    # if check_left_lane(xy):
                    cv2.polylines(ROI,[xy],isClosed=True,color=(0,255,255),thickness=2)
                    self.seg_center2 = get_centroid(xy)
                    self.seg_center2_list.append(self.seg_center2)
                        
                
                else:
                    pass
                
                
                self.coordinate.append(self.seg_center0)
                self.coordinate.append(self.seg_center1)
                self.coordinate.append(self.seg_center2)
        
        except TypeError:
            print("error")
    
            
        # print(self.seg_center0_list, self.seg_center1_list, self.seg_center2_list)
        
        
        
        if len(self.seg_center1_list) > 1:
            # x = int((self.seg_center1_list[0][0] + self.seg_center1_list[-1][0])/2)
            # y = int((self.seg_center1_list[0][1] + self.seg_center1_list[-1][1])/2)
            # self.seg_center1 = (x,y)
            
            if self.seg_center1_list[0][0]>self.seg_center1_list[-1][0]:
                self.seg_center1 = self.seg_center1_list[0]
            else:
                self.seg_center1 = self.seg_center1_list[-1]
            
        else:
            pass
                
        if len(self.seg_center1_list) > 0 and len(self.seg_center2_list) > 0:
            # line_center = (640-self.seg_center0[0], roi_rect_center_y+100)
            # load_center = int(self.seg_center1[0]*2/3)
            line_center = int((self.seg_center2[0] + self.seg_center1[0]))
            load_center = int((line_center + self.seg_center0[0])/2.5)
            # if self.seg_center1[0] > self.seg_center2[0] and self.seg_center1[0]-self.seg_center2[0] > 50:
                
            #     load_center = int((self.seg_center2[0] + 2*self.seg_center1[0])/3.5)
            # else:
            #     load_center =  int((self.seg_center1[0] + self.seg_center0[0])/2) 
            
            
        elif len(self.seg_center2_list) == 0:
            # line_center = self.seg_center1
            load_center = int((self.seg_center1[0] + self.seg_center0[0])/2) 
              
        else:
            # line_center = self.seg_center2
            load_center = int((self.seg_center2[0] + self.seg_center0[0])/2)  
            
        self.error = load_center-(self.img_center_x)
        
        if abs(self.error) > 100:
            error = 100
        else:
            error = abs(self.error)
        
        linear_x= int(roi_rect_center_y-50 + error)
        
        overlay = self.image.copy()
        cv2.rectangle(self.image, roi_rect_start, roi_rect_end, color = (255, 0, 0), thickness = 2)
        
        
                
        cv2.line(self.image, (0, linear_x), (640, linear_x), color = (0, 255, 0), thickness=2)
        cv2.line(self.image, (load_center, roi_rect_start[1]), (load_center, roi_rect_end[1]), color = (0, 255, 0), thickness=2)
        cv2.circle(self.image, (load_center, linear_x), radius = 5, color = (0, 0, 255), thickness = -1)
        
        print(self.img_center_x, roi_rect_center_y)
        cv2.line(self.image, (0, roi_rect_center_y), (640, roi_rect_center_y), color = (255, 255, 255), thickness=2) 
        cv2.line(self.image, (self.img_center_x, roi_rect_start[1]), (self.img_center_x, roi_rect_end[1]), color = (255, 255, 255), thickness=2) 
        cv2.circle(self.image, (self.img_center_x, roi_rect_center_y), radius = 5, color = (0, 0, 0), thickness = -1)
        
        
        cv2.putText(self.image, str(self.error), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
               
        overlay = cv2.addWeighted(overlay, self.alpha, self.image, 1-self.alpha, 0)
        self.coordinate.append([(load_center, linear_x)])

        
        return overlay, self.error, self.coordinate
