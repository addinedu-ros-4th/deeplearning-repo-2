from ultralytics import YOLO
import cv2
import numpy as np
import glob
from calibration_utils import calibrate_camera, undistort
import time

model = YOLO("best.pt")



# def extract_pixels(image, box_cords):
#     x, y, w, h = box_cords
#     return image[y:y+h, x:x+w]

def extract_pixels(image, segmentation, classes):
    
    filled_image = np.copy(image)

    border_line_pix = []
    middle_line_pix = []

    # border_line_pix.clear()
    # middle_line_pix.clear()

    for mask,box in zip(segmentation,classes):
        
        xy = mask.xy[0].astype("int") 

        if box.cls.item()==3:
            middle_line_pix.append(xy)
            cv2.fillPoly(filled_image,[xy],color=(0,255,255))

        elif box.cls.item()==0:
            border_line_pix.append(xy)
            cv2.fillPoly(filled_image,[xy],color=(255,255,255))

    return border_line_pix, middle_line_pix, filled_image

# def draw_from_pixels(image, lines_pix, color):

#     filled_image = np.copy(image)

#     for pix in lines_pix:
#         polygon_pts = np.array(pix, dtype=np.int32)

#         cv2.fillPoly(filled_image, [polygon_pts], color)

#     return filled_image

if __name__ == '__main__':

    video_path = "mobility4_video.mp4"
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Video is unavailable :", video_path)
        exit(0) 

    while (cap.isOpened()):
        ret, image = cap.read()
    
        if not ret:
            break

        result = model.predict(source = image, conf=0.5)[0]
        classes = result.boxes
        segmentation = result.masks

        border_line_pix, middle_line_pix, filled_image = extract_pixels(image, segmentation, classes)

        # filled_image = draw_from_pixels(image, middle_line_pix, (0, 255, 255)) 
        # filled_image = draw_from_pixels(filled_image, border_line_pix, (255, 255, 255))  

        # print("border_line_pix :", border_line_pix[-1])
        # print("middle_line_pix :", middle_line_pix[-1])
        # print(border_line_pix)



        # mask = np.zeros_like(image)
        # mask2 = np.zeros_like(image)

        # for pix in border_line_pix:
        #     polygon_pts = np.array(pix, dtype=np.int32)
        #     cv2.fillPoly(mask, [polygon_pts], (0, 0, 255))

        # if len(middle_line_pix) > 0:
        #     all_middle_pts = np.concatenate(middle_line_pix, axis=0)
        #     polygon_pts2 = np.array([all_middle_pts], dtype=np.int32)
        #     cv2.fillPoly(mask2, polygon_pts2, (0, 255, 0))



        # mask = cv2.bitwise_or(mask, mask2)
        # image = cv2.addWeighted(image, 1, mask, 0.5, 0)



        # polygon_area = cv2.bitwise_and(image, mask)
        # polygon_area2 = cv2.bitwise_and(image, mask2)

        # image = cv2.addWeighted(image, 1, polygon_area, 0.5, 0)
        # image = cv2.addWeighted(image, 1, polygon_area2, 0.5, 0)

        cv2.imshow("Video", filled_image)
        time.sleep(0.01)

        # border_line_pix.clear()
        # middle_line_pix.clear()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()