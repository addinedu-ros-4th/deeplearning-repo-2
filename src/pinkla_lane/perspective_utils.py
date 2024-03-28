import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt
from calibration_utils import calibrate_camera, undistort
from binarization_utils import binarize

# 프레임에 원근 변환을 적용하여 새로운 시점의 이미지(BEV)를 생성
def birdeye(img, verbose=False):

    h, w = img.shape[:2]

    # 원근 변환 시 사용할 점(우측하단, 좌측하단, 좌측상단, 우측상단 좌표) 지정
    src = np.float32([[w, h],    # br
                      [0, h],    # bl
                    #   [w/20, h/3],   # tl
                    #   [w*19/20, h/3]])  # tr
                      [0, h*1/3],   # tl video 4
                      [w, h*1/3]])  # tr video 4
    
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

    ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='camera_cal')

    for test_img in glob.glob('test_images/frame707.jpg'):
    # for test_img in glob.glob('test_images/test1.jpg'):

        img = cv2.imread(test_img)

        img_undistorted = undistort(img, mtx, dist, verbose=False)

        img_binary = binarize(img, verbose=False)

        img_birdeye, M, Minv = birdeye(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), verbose=True)


