import numpy as np
import cv2
import glob
import collections
import matplotlib.pyplot as plt
from calibration_utils import calibrate_camera, undistort
from binarization_utils import binarize
from perspective_utils import birdeye
from globals import ym_per_pix, xm_per_pix

# 차선 모델링 클래스
class Line:

    def __init__(self, buffer_len=10):

        # 마지막 iteration에서 차선이 검출되었는지 여부(flag)
        self.detected = False

        # 마지막 iteration에서의 다항식 계수(픽셀, 미터 단위)
        self.last_fit_pixel = None
        self.last_fit_meter = None

        # 마지막 N iteration에서의 다항식 계수(픽셀, 미터 단위)
        self.recent_fits_pixel = collections.deque(maxlen=buffer_len)
        self.recent_fits_meter = collections.deque(maxlen=2 * buffer_len)

        # 차선의 곡률 반지름
        self.radius_of_curvature = None

        # 감지된 차선의 모든 픽셀 좌표
        self.all_x = []
        self.all_y = []

    def update_values(self, x_values, y_values):
        self.all_x = x_values
        self.all_y = y_values

    def print_values(self):
        print("X values:", self.all_x)
        print("Y values:", self.all_y)

    # 새로운 픽셀/미터 단위 계수 -> 라인 재설정
    # detected : 차선이 감지되었는지 여부
    # clear_buffer : True이;면 line 객체 상태를 reset
    def update_line(self, new_fit_pixel, new_fit_meter, detected, clear_buffer=False):
        
        self.detected = detected

        if clear_buffer:
            self.recent_fits_pixel = []
            self.recent_fits_meter = []

        self.last_fit_pixel = new_fit_pixel
        self.last_fit_meter = new_fit_meter

        self.recent_fits_pixel.append(self.last_fit_pixel)
        self.recent_fits_meter.append(self.last_fit_meter)

    # mask image에 차선 그리기
    def draw(self, mask, color=(255, 0, 0), line_width=50, average=False):

        # h, w, c : mask image의 높이, 너비, 채널 수
        h, w, c = mask.shape

        plot_y = np.linspace(0, h - 1, h)

        # 차선을 정의하기 위한 계수
        # average : True이면 차선의 평균에 의해 결정, False 이면 가장 최근에 감지된 차선에 의해 결정
        coeffs = self.average_fit if average else self.last_fit_pixel

        # 차선의 중심 계산
        line_center = coeffs[0] * plot_y ** 2 + coeffs[1] * plot_y + coeffs[2]

        # 차선 경계 정의(양옆으로 line width의 절반 만큼)
        line_left_side = line_center - line_width // 2
        line_right_side = line_center + line_width // 2

        # cv2.fillPoly()에 적용 가능한 형식으로 recast
        pts_left = np.array(list(zip(line_left_side, plot_y)))
        pts_right = np.array(np.flipud(list(zip(line_right_side, plot_y))))
        pts = np.vstack([pts_left, pts_right])

        # mask image 정의된 차선의 영역을 채우고, 이미지 반환
        return cv2.fillPoly(mask, [np.int32(pts)], color)

    @property
    # 최근 N번의 다항식 계수의 평균으로 선의 평균적인 형태 파악
    def average_fit(self):
        return np.mean(self.recent_fits_pixel, axis=0)

    @property
    # 평균 다항식 계수를 이용하여 선의 곡률 계산
    # 곡률은 y좌표에 대해 곡률 반지름을 나타냄
    def curvature(self):
        y_eval = 0
        coeffs = self.average_fit
        return ((1 + (2 * coeffs[0] * y_eval + coeffs[1]) ** 2) ** 1.5) / np.absolute(2 * coeffs[0])

    @property
    def curvature_pixel(self):
        y_eval = 0
        coeffs = np.mean(self.recent_fits_pixel, axis=0)
        return ((1 + (2 * coeffs[0] * y_eval + coeffs[1]) ** 2) ** 1.5) / np.absolute(2 * coeffs[0])

# sliding window 차선 검출
# binary image에서 라인 검출을 위한 다항식 계수 추출
# birdeye_binary: input bird's eye view binary image
# line_lt: 이전에 감지된 왼쪽 차선
# line_rt: 이전에 감지된 오른쪽 차선
# n_windows: sliding window의 개수(default : 9)
def get_fits_by_sliding_windows(birdeye_binary, line_lt, line_rt, n_windows=9, verbose=False):

    height, width = birdeye_binary.shape

    # BEV 이미지의 하단 절반에서 픽셀 값에 대한 히스토그램 계산 -> 차선의 초기위치 추정
    histogram = np.sum(birdeye_binary[height//2:-30, :], axis=0)

    # output image 생성
    out_img = np.dstack((birdeye_binary, birdeye_binary, birdeye_binary)) * 255

    # 히스토그램에서 왼쪽, 오른쪽 차선의 시작점 찾기
    midpoint = len(histogram) // 2
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    # sliding window 높이 계산
    window_height = int(height / n_windows)

    nonzero = birdeye_binary.nonzero()
    nonzero_y = np.array(nonzero[0])
    nonzero_x = np.array(nonzero[1])

    # 현재 sliding window의 왼쪽 및 오른쪽 차선의 x좌표를 시작위치로 초기화
    # 초기에는 차선을 찾을 위치가 이미지 하단에 있다고 예측하고,
    # 이 위치를 기준으로 sliding window를 이동하면서 차선을 찾아감
    leftx_current = leftx_base
    rightx_current = rightx_base

    margin = 100  # sliding window의 너비(현재 위치에서 얼마나 멀리 차선을 탐색할지)
    minpix = 50   # 윈도우를 재설정할 최소 픽셀 수(각 윈도우에서 찾은 픽셀 수가 기준보다 작으면 다음 위도우 위치 조정 X)

    # 왼쪽 차선과 오른쪽 차선에 해당하는 픽셀들의 인덱스 리스트
    left_lane_inds = []
    right_lane_inds = []


    for window in range(n_windows):
        # 슬라이딩 윈도우 경계 지정
        win_y_low = height - (window + 1) * window_height
        win_y_high = height - window * window_height
        win_xleft_low = leftx_current - margin
        win_xleft_high = leftx_current + margin
        win_xright_low = rightx_current - margin
        win_xright_high = rightx_current + margin

        # 윈도우 시각화
        cv2.rectangle(out_img, (win_xleft_low, win_y_low), (win_xleft_high, win_y_high), (0, 255, 0), 2)
        cv2.rectangle(out_img, (win_xright_low, win_y_low), (win_xright_high, win_y_high), (0, 255, 0), 2)

        # 윈도우 내의 차선에 해당하는 픽셀(nonzero) 식별
        good_left_inds = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_xleft_low)
                          & (nonzero_x < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_xright_low)
                           & (nonzero_x < win_xright_high)).nonzero()[0]

        # 차선 인덱스 업데이트
        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)

        # 윈도우 내 픽셀 수 > minpix이면 다음 윈도우 위치 조정
        if len(good_left_inds) > minpix:
            leftx_current = int(np.mean(nonzero_x[good_left_inds]))
        elif len(good_left_inds) < minpix:
            left_fit_pixel = line_lt.last_fit_pixel
            left_fit_meter = line_lt.last_fit_meter
            detected = False

        if len(good_right_inds) > minpix:
            rightx_current = int(np.mean(nonzero_x[good_right_inds]))
        elif len(good_right_inds) < minpix:
            right_fit_pixel = line_rt.last_fit_pixel
            right_fit_meter = line_rt.last_fit_meter
            detected = False

    # 차선 인덱스 업데이트
    left_lane_inds = np.concatenate(left_lane_inds)
    right_lane_inds = np.concatenate(right_lane_inds)

    # 왼쪽 / 오른쪽 차선을 나타내는 객체(line_lt / line_rt)에 검출된 모든 차선 픽셀을 설정
    line_lt.all_x, line_lt.all_y = nonzero_x[left_lane_inds], nonzero_y[left_lane_inds]
    line_rt.all_x, line_rt.all_y = nonzero_x[right_lane_inds], nonzero_y[right_lane_inds]

    detected = True

    # 왼쪽 / 오른쪽 차선에 해당하는 픽셀이 검출되지 않은 경우
    if not list(line_lt.all_x) or not list(line_lt.all_y):
        left_fit_pixel = line_lt.last_fit_pixel
        left_fit_meter = line_lt.last_fit_meter
        detected = False
    else:
        left_fit_pixel = np.polyfit(line_lt.all_y, line_lt.all_x, 2)
        left_fit_meter = np.polyfit(line_lt.all_y * ym_per_pix, line_lt.all_x * xm_per_pix, 2)

    if not list(line_rt.all_x) or not list(line_rt.all_y):
        right_fit_pixel = line_rt.last_fit_pixel
        right_fit_meter = line_rt.last_fit_meter
        detected = False
    else:
        right_fit_pixel = np.polyfit(line_rt.all_y, line_rt.all_x, 2)
        right_fit_meter = np.polyfit(line_rt.all_y * ym_per_pix, line_rt.all_x * xm_per_pix, 2)

    line_lt.update_line(left_fit_pixel, left_fit_meter, detected=detected)
    line_rt.update_line(right_fit_pixel, right_fit_meter, detected=detected)

    # 적합한 다항식을 이용하여 차선의 x, y 좌표 생성
    ploty = np.linspace(0, height - 1, height)
    left_fitx = left_fit_pixel[0] * ploty ** 2 + left_fit_pixel[1] * ploty + left_fit_pixel[2]
    right_fitx = right_fit_pixel[0] * ploty ** 2 + right_fit_pixel[1] * ploty + right_fit_pixel[2]

    out_img[nonzero_y[left_lane_inds], nonzero_x[left_lane_inds]] = [255, 0, 0]
    out_img[nonzero_y[right_lane_inds], nonzero_x[right_lane_inds]] = [0, 0, 255]

    if verbose:
        f, ax = plt.subplots(1, 2)
        f.set_facecolor('white')
        ax[0].imshow(birdeye_binary, cmap='gray')
        ax[1].imshow(out_img)
        ax[1].plot(left_fitx, ploty, color='yellow')
        ax[1].plot(right_fitx, ploty, color='yellow')
        ax[1].set_xlim(0, 640)
        ax[1].set_ylim(480, 0)
        # plt.imshow(out_img)

        plt.show()

    return line_lt, line_rt, out_img

# 이전에 감지된 차선 정보를 사용 -> 현재 프레임에서 차선을 감지(속도 향상)
# 양쪽 차선 사이 주행 영역을 표시
def get_fits_by_previous_fits(birdeye_binary, line_lt, line_rt, verbose=False):

    height, width = birdeye_binary.shape

    left_fit_pixel = line_lt.last_fit_pixel
    right_fit_pixel = line_rt.last_fit_pixel

    nonzero = birdeye_binary.nonzero()
    nonzero_y = np.array(nonzero[0])
    nonzero_x = np.array(nonzero[1])
    margin = 100
    left_lane_inds = (
    (nonzero_x > (left_fit_pixel[0] * (nonzero_y ** 2) + left_fit_pixel[1] * nonzero_y + left_fit_pixel[2] - margin)) & (
    nonzero_x < (left_fit_pixel[0] * (nonzero_y ** 2) + left_fit_pixel[1] * nonzero_y + left_fit_pixel[2] + margin)))
    right_lane_inds = (
    (nonzero_x > (right_fit_pixel[0] * (nonzero_y ** 2) + right_fit_pixel[1] * nonzero_y + right_fit_pixel[2] - margin)) & (
    nonzero_x < (right_fit_pixel[0] * (nonzero_y ** 2) + right_fit_pixel[1] * nonzero_y + right_fit_pixel[2] + margin)))

    line_lt.all_x, line_lt.all_y = nonzero_x[left_lane_inds], nonzero_y[left_lane_inds]
    line_rt.all_x, line_rt.all_y = nonzero_x[right_lane_inds], nonzero_y[right_lane_inds]

    detected = True

    if not list(line_lt.all_x) or not list(line_lt.all_y):
        left_fit_pixel = line_lt.last_fit_pixel
        left_fit_meter = line_lt.last_fit_meter
        detected = False
    else:
        left_fit_pixel = np.polyfit(line_lt.all_y, line_lt.all_x, 2)
        left_fit_meter = np.polyfit(line_lt.all_y * ym_per_pix, line_lt.all_x * xm_per_pix, 2)

    if not list(line_rt.all_x) or not list(line_rt.all_y):
        right_fit_pixel = line_rt.last_fit_pixel
        right_fit_meter = line_rt.last_fit_meter
        detected = False
    else:
        right_fit_pixel = np.polyfit(line_rt.all_y, line_rt.all_x, 2)
        right_fit_meter = np.polyfit(line_rt.all_y * ym_per_pix, line_rt.all_x * xm_per_pix, 2)

    line_lt.update_line(left_fit_pixel, left_fit_meter, detected=detected)
    line_rt.update_line(right_fit_pixel, right_fit_meter, detected=detected)

    ploty = np.linspace(0, height - 1, height)
    left_fitx = left_fit_pixel[0] * ploty ** 2 + left_fit_pixel[1] * ploty + left_fit_pixel[2]
    right_fitx = right_fit_pixel[0] * ploty ** 2 + right_fit_pixel[1] * ploty + right_fit_pixel[2]

    # img_fit : 검정 배경, 흰색 차선 픽셀 표시
    img_fit = np.dstack((birdeye_binary, birdeye_binary, birdeye_binary)) * 255
    window_img = np.zeros_like(img_fit)
    img_fit[nonzero_y[left_lane_inds], nonzero_x[left_lane_inds]] = [255, 0, 0]
    img_fit[nonzero_y[right_lane_inds], nonzero_x[right_lane_inds]] = [0, 0, 255]

    # search window 영역을 polygon으로 형성
    left_line_window1 = np.array([np.transpose(np.vstack([left_fitx - margin, ploty]))])
    left_line_window2 = np.array([np.flipud(np.transpose(np.vstack([left_fitx + margin, ploty])))])
    left_line_pts = np.hstack((left_line_window1, left_line_window2))
    right_line_window1 = np.array([np.transpose(np.vstack([right_fitx - margin, ploty]))])
    right_line_window2 = np.array([np.flipud(np.transpose(np.vstack([right_fitx + margin, ploty])))])
    right_line_pts = np.hstack((right_line_window1, right_line_window2))

    # 왼쪽 차선과 오른쪽 차선 사이를 초록색 경로로 표시
    cv2.fillPoly(window_img, [left_line_pts.astype(int)], (0, 255, 0))
    cv2.fillPoly(window_img, [right_line_pts.astype(int)], (0, 255, 0)) 
    result = cv2.addWeighted(img_fit, 1, window_img, 0.3, 0)

    if verbose:
        plt.imshow(result)
        plt.plot(left_fitx, ploty, color='yellow')
        plt.plot(right_fitx, ploty, color='yellow')
        plt.xlim(0, 1280)
        plt.ylim(720, 0)

        plt.show()

    return line_lt, line_rt, img_fit

# 주행 가능 경로와 양쪽 차선을 입력된 프레임에 그려줌
# keep_state: True이면, line state 유지
def draw_back_onto_the_road(img_undistorted, Minv, line_lt, line_rt, keep_state):
    
    height, width, _ = img_undistorted.shape

    left_fit = line_lt.average_fit if keep_state else line_lt.last_fit_pixel
    right_fit = line_rt.average_fit if keep_state else line_rt.last_fit_pixel

    # 다각형 꼭짓점 생성
    ploty = np.linspace(0, height - 1, height)
    left_fitx = left_fit[0] * ploty ** 2 + left_fit[1] * ploty + left_fit[2]
    right_fitx = right_fit[0] * ploty ** 2 + right_fit[1] * ploty + right_fit[2]

    # 경로를 녹색으로 표시
    road_warp = np.zeros_like(img_undistorted, dtype=np.uint8)
    pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
    pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
    pts = np.hstack((pts_left, pts_right))
    cv2.fillPoly(road_warp, [np.int32(pts)], (0, 255, 0))

    # 다각형 영역을 원본 이미지 공간으로 변환
    road_dewarped = cv2.warpPerspective(road_warp, Minv, (width, height))  
    blend_onto_road = cv2.addWeighted(img_undistorted, 1., road_dewarped, 0.3, 0)

    line_warp = np.zeros_like(img_undistorted)
    line_warp = line_lt.draw(line_warp, color=(255, 0, 0), average=keep_state)
    line_warp = line_rt.draw(line_warp, color=(0, 0, 255), average=keep_state)
    line_dewarped = cv2.warpPerspective(line_warp, Minv, (width, height))

    lines_mask = blend_onto_road.copy()
    idx = np.any([line_dewarped != 0][0], axis=2)
    lines_mask[idx] = line_dewarped[idx]

    blend_onto_road = cv2.addWeighted(src1=lines_mask, alpha=0.8, src2=blend_onto_road, beta=0.5, gamma=0.)

    return blend_onto_road


if __name__ == '__main__':

    line_lt, line_rt = Line(buffer_len=10), Line(buffer_len=10)

    ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='camera_cal')

    for test_img in glob.glob('test_images/frame707.jpg'):

        img = cv2.imread(test_img)

        img_undistorted = undistort(img, mtx, dist, verbose=False)

        img_binary = binarize(img_undistorted, verbose=False)

        img_birdeye, M, Minv = birdeye(img_binary, verbose=False)

        line_lt, line_rt, img_out = get_fits_by_sliding_windows(img_birdeye, line_lt, line_rt, n_windows=7, verbose=True)
