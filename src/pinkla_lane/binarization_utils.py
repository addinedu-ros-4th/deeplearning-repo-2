import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt


# 노란선 구분하기 위한 임계값 설정
yellow_HSV_th_min = np.array([0, 70, 70])
yellow_HSV_th_max = np.array([50, 255, 255])

# 입력 프레임 -> HSV 변환 이후, 최소/최대 임계값을 사용하여 binarize
def thresh_frame_in_HSV(frame, min_values, max_values, verbose=False):

    HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    min_th_ok = np.all(HSV > min_values, axis=2)
    max_th_ok = np.all(HSV < max_values, axis=2)

    out = np.logical_and(min_th_ok, max_th_ok)

    if verbose:
        plt.imshow(out, cmap='gray')
        plt.show()

    return out

# sobel 필터 사용 엣지 검출
def thresh_frame_sobel(frame, kernel_size):
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 이미지의 수평 및 수직 방향 경계 검출
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=kernel_size)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=kernel_size)

    # 경계 강도 계산 및 정규화
    sobel_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    sobel_mag = np.uint8(sobel_mag / np.max(sobel_mag) * 255)

    # 경계강도가 임계값(50)보다 큰 경우 1, 아닌 경우 0으로 binarize
    _, sobel_mag = cv2.threshold(sobel_mag, 50, 1, cv2.THRESH_BINARY)

    return sobel_mag.astype(bool)

# equalize histogram
def get_binary_from_equalized_grayscale(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    eq_global = cv2.equalizeHist(gray)

    # 임계값이 250 이상인 픽셀을 255, 아닌 경우를 0으로 binarize
    _, th = cv2.threshold(eq_global, thresh=250, maxval=255, type=cv2.THRESH_BINARY)

    return th

def create_yellow_mask(img):
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    
    # 노란색 영역을 추출하기 위한 마스크 생성
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    return yellow_mask

def create_green_mask(img):

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    # 연두색 영역을 추출하기 위한 마스크 생성
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    return green_mask

prev_lines = None

# 차선을 강조한 binary 이미지로 변환
def binarize(img, verbose=False):

    h, w = img.shape[:2]
    binary = np.zeros(shape=(h, w), dtype=np.uint8)

    # 노란 선 강조
    yellow_mask = create_yellow_mask(img)
    binary = np.logical_or(binary, yellow_mask)

    # 흰색 선 강조
    eq_white_mask = get_binary_from_equalized_grayscale(img)
    binary = np.logical_or(binary, eq_white_mask)

    # yellow_mask에 의해 연두색 지역이 같이 강조 되어 나타남.
    # 연두색 지역을 제외하기 위한 마스크 생성(binary 이미지에서 연두색 지역을 제외)
    green_mask = create_green_mask(img)
    binary[green_mask] = 0

    # Sobel binary mask (thresholded gradients)
    sobel_mask = thresh_frame_sobel(img, kernel_size=9)
    binary = np.logical_or(binary, sobel_mask)

    # 모폴로지 연산을 적용하여 binary 이미지로 변환
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(binary.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

    # # 현재 프레임에서 라인을 감지하고 추적
    # detected_lines = detect_lines(img)
    
    # # 라인이 감지되지 않는 경우에는 이전 프레임에서 추적한 정보를 사용하여 라인 예측
    # if detected_lines is None:
    #     predicted_lines = predict_lines(prev_lines)
    #     if predicted_lines is not None:
    #         detected_lines = predicted_lines
    
    # # 현재 프레임에서 추적한 라인 정보를 이전 프레임 변수에 저장
    # prev_lines = detected_lines

    if verbose:
        f, ax = plt.subplots(2, 3)
        f.set_facecolor('white')
        ax[0, 0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax[0, 0].set_title('input_frame')
        ax[0, 0].set_axis_off()
        ax[0, 0].set_facecolor('red')
        ax[0, 1].imshow(eq_white_mask, cmap='gray')
        ax[0, 1].set_title('white mask')
        ax[0, 1].set_axis_off()

        ax[0, 2].imshow(yellow_mask, cmap='gray')
        ax[0, 2].set_title('yellow mask')
        ax[0, 2].set_axis_off()

        ax[1, 0].imshow(sobel_mask, cmap='gray')
        ax[1, 0].set_title('sobel mask')
        ax[1, 0].set_axis_off()

        ax[1, 1].imshow(binary, cmap='gray')
        ax[1, 1].set_title('before closure')
        ax[1, 1].set_axis_off()

        ax[1, 2].imshow(closing, cmap='gray')
        ax[1, 2].set_title('after closure')
        ax[1, 2].set_axis_off()
        # ax[1, 2].imshow(green_mask, cmap='gray')
        # ax[1, 2].set_title('green_mask')
        # ax[1, 2].set_axis_off()
        plt.show()

    return closing

# def detect_lines(img):
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 50, 150)
#     lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=50)
    
#     if lines is not None:
#         detected_lines = []
#         for line in lines:
#             x1, y1, x2, y2 = line[0]
#             detected_lines.append(((x1, y1), (x2, y2)))
#         return detected_lines
#     else:
#         return None

# def predict_lines(prev_lines):
#     if prev_lines is not None:
#         predicted_lines = []
#         for line in prev_lines:
#             # 이전 라인의 경향성을 유지하며 다음 프레임 예측
#             # 이전 라인의 기울기를 유지, 이전 라인의 끝점을 기준으로 새로운 라인을 생성
#             x1, y1 = line[0]
#             x2, y2 = line[1]
#             dx = x2 - x1
#             dy = y2 - y1
#             new_x1 = max(0, x1 - dx)
#             new_y1 = max(0, y1 - dy)
#             new_x2 = min(img.shape[1], x2 + dx)
#             new_y2 = min(img.shape[0], y2 + dy)
#             predicted_lines.append(((new_x1, new_y1), (new_x2, new_y2)))
#         return predicted_lines
#     else:
#         return None

if __name__ == '__main__':

    test_images = glob.glob('test_images/20240321_211649.jpg')
    for test_image in test_images:
        img = cv2.imread(test_image)
        binarize(img=img, verbose=True)
