import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt
import os.path as path
import pickle

def lazy_calibration(func):
    # 함수 호출 시 마다 캐시 파일 확인
    # 캐시 파일이 존재하면 결과를 읽어오고, 존재하지 않으면 함수를 호출하여 결과 계산 후 캐시 파일에 저장
    # 이후에 같은 입력이 들어오면 함수의 결과를 다시 계산하는 대신 캐시 파일에서 결과를 불러옴
    calibration_cache = 'camera_cal/calibration_data.pickle'

    def wrapper(*args, **kwargs):
        if path.exists(calibration_cache):
            print('Loading cached camera calibration...', end=' ')
            with open(calibration_cache, 'rb') as dump_file:
                calibration = pickle.load(dump_file)
        else:
            print('Computing camera calibration...', end=' ')
            calibration = func(*args, **kwargs)
            with open(calibration_cache, 'wb') as dump_file:
                pickle.dump(calibration, dump_file)
        print('Done.')
        return calibration

    return wrapper

# 'calibrate_camera' 함수에 '@lazy_calibration' 데코레이터 적용
# calib_images_dir : calibration을 위한 chessboard frame을 가지고 있는 경로
# verbose : 'True'이면 chessboard corner를 표시
@lazy_calibration
def calibrate_camera(calib_images_dir, verbose=False):

    assert path.exists(calib_images_dir), '"{}" must exist and contain calibration images.'.format(calib_images_dir)

    
    objp = np.zeros((6 * 9, 3), np.float32)
    objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

    # objpoinats : 실제 환경에서의 3D points 
    # imgpoints :  이미지 상의 2D points
    objpoints = []  
    imgpoints = []  

    images = glob.glob(path.join(calib_images_dir, 'calibration*.jpg'))

    # chessboard corners 찾기
    for filename in images:

        img = cv2.imread(filename)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        pattern_found, corners = cv2.findChessboardCorners(gray, (9, 6), None)

        if pattern_found is True:
            objpoints.append(objp)
            imgpoints.append(corners)

            # verbose = True이면 chessboard corners를 그리고 표시
            if verbose:
                img = cv2.drawChessboardCorners(img, (9, 6), corners, pattern_found)
                cv2.imshow('img',img)
                cv2.waitKey(500)

    if verbose:
        cv2.destroyAllWindows()

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    # ret : 카메라 보정 성공 여부(flag)
    # mtx : 카메라 행렬(카메라 내부 파라미터 정의 3X3 행렬)
    # dist : 왜곡 계수
    # rvecs : 회전벡터(각 이미지에 대한 회전)
    # tvecs : 변환벡터(각 이미지에 대한 변환)
    return ret, mtx, dist, rvecs, tvecs

# 카메라 행렬과 왜곡 계수를 이용한 왜곡 현상 완화 
# frame : 입력 프레임(왜곡 완화 적용할 프레임)
# mtx : 카메라 matrix(카메라 내부 파라미터 포함)
# dist : 왜곡 계수(카메라 렌즈 왜곡 보정)
def undistort(frame, mtx, dist, verbose=False):

    frame_undistorted = cv2.undistort(frame, mtx, dist, newCameraMatrix=mtx)

    if verbose:
        fig, ax = plt.subplots(nrows=1, ncols=2)
        ax[0].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ax[1].imshow(cv2.cvtColor(frame_undistorted, cv2.COLOR_BGR2RGB))
        plt.show()

    return frame_undistorted


if __name__ == '__main__':

    ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='camera_cal', verbose=True)

    img = cv2.imread('test_images/test2.jpg')

    img_undistorted = undistort(img, mtx, dist, verbose=True)

    # cv2.imwrite('img/test_calibration_before.jpg', img)
    # cv2.imwrite('img/test_calibration_after.jpg', img_undistorted)