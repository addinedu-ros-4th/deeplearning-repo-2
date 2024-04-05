import numpy as np
import cv2
import matplotlib.pyplot as plt
from calibration_utils import calibrate_camera, undistort
from segmented_binarization import binarize
from ultralytics import YOLO
from extract_pixels import extract_pixels


# 프레임에 원근 변환을 적용하여 새로운 시점의 이미지(BEV)를 생성
def birdeye(img, verbose=False):

    h, w = img.shape[:2]

    # 원근 변환 시 사용할 점(우측하단, 좌측하단, 좌측상단, 우측상단 좌표) 지정
    src = np.float32([[w, h],    # br
                      [0, h],    # bl
                    #   [w*5/18, h*1/3], 
                    #   [w*13/18, h*1/3]])
                      [w*1/3, h*1/3], 
                      [w*2/3, h*1/3]])
    
    
    # 변환된 이미지의 네 모서리 좌표
    dst = np.float32([[w, h],       # br
                      [0, h],       # bl
                      [0, 0],       # tl
                      [w, 0]])      # tr

    # M : src -> dst 변환 행렬
    # Minv : dst -> src 변환 행렬
    M = cv2.getPerspectiveTransform(src, dst)
    Minv = cv2.getPerspectiveTransform(dst, src)

    # 이미지 원근 변환
    warped = cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR)
    # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB) 

    if verbose:
        f, axarray = plt.subplots(1, 2)
        f.set_facecolor('white')
        axarray[0].set_title('Before perspective transform')
        axarray[0].imshow(img, cmap='gray')
        for point in src:
            axarray[0].plot(*point, '.')
        axarray[1].set_title('After perspective transform')
        axarray[1].imshow(warped, cmap='gray')
        for point in dst:
            axarray[1].plot(*point, '.')
        for axis in axarray:
            axis.set_axis_off()
        plt.show()

    return warped, M, Minv


if __name__ == '__main__':

    # ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='camera_cal')
    mtx = np.array([[470.86256773,0.,322.79554974],
                  [0.,470.89842857,236.76274254],
                  [0.,0.,1.]])
    dist = np.array([[0.00727918, -0.09059939, -0.00224102, -0.00040328, 0.06114216]])

    model = YOLO("best2.pt")

    video_path = "mobility6_video.avi"
    # video_path = "mobility4_video.mp4"

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

        img_undistorted = undistort(image, mtx, dist, verbose=False)

        border_line_pix, middle_line_pix, filled_image = extract_pixels(img_undistorted, segmentation, classes)

        # cv2.imshow("Video", filled_image)


        segmented_binarized = binarize(filled_image)


        # cv2.imshow("Video", segmented_binarized)

        segmented_birdeye, M, Minv = birdeye(cv2.cvtColor(segmented_binarized, cv2.COLOR_BGR2RGB))

        cv2.imshow("Video", segmented_birdeye)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


