import cv2
import os
import matplotlib.pyplot as plt
from calibration_utils import calibrate_camera, undistort
from binarization_utils import binarize
from perspective_utils import birdeye
from line_utils import get_fits_by_sliding_windows, draw_back_onto_the_road, Line, get_fits_by_previous_fits
from moviepy.editor import VideoFileClip
import numpy as np
from globals import xm_per_pix, time_window

# processed_frames : 처리된 프레임 개수(영상의 경우)
processed_frames = 0                    
line_lt = Line(buffer_len=time_window) 
line_rt = Line(buffer_len=time_window)  

# blend_on_road : 주행 가능한 영역과 차선이 그려진 이미지
# img_fit : BEV에 검출된 차선이 강조된 이미지
# line_lt: 검출된 왼쪽 차선
# line_rt: 검출된 오른쪽 차선
def prepare_out_blend_frame(blend_on_road, img_binary, img_birdeye, img_fit, line_lt, line_rt, offset_pix):

    h, w = blend_on_road.shape[:2]

    # 이미지 상단에 썸네일 생성 
    thumb_ratio = 0.2
    thumb_h, thumb_w = int(thumb_ratio * h), int(thumb_ratio * w)

    off_x, off_y = 20, 15

    mask = blend_on_road.copy()
    mask = cv2.rectangle(mask, pt1=(0, 0), pt2=(w, thumb_h+2*off_y), color=(0, 0, 0), thickness=cv2.FILLED)
    blend_on_road = cv2.addWeighted(src1=mask, alpha=0.2, src2=blend_on_road, beta=0.8, gamma=0)

    thumb_binary = cv2.resize(img_binary, dsize=(thumb_w, thumb_h))
    thumb_binary = np.dstack([thumb_binary, thumb_binary, thumb_binary]) * 255
    blend_on_road[off_y:thumb_h+off_y, off_x:off_x+thumb_w, :] = thumb_binary

    thumb_birdeye = cv2.resize(img_birdeye, dsize=(thumb_w, thumb_h))
    thumb_birdeye = np.dstack([thumb_birdeye, thumb_birdeye, thumb_birdeye]) * 255
    blend_on_road[off_y:thumb_h+off_y, 2*off_x+thumb_w:2*(off_x+thumb_w), :] = thumb_birdeye

    thumb_img_fit = cv2.resize(img_fit, dsize=(thumb_w, thumb_h))
    blend_on_road[off_y:thumb_h+off_y, 3*off_x+2*thumb_w:3*(off_x+thumb_w), :] = thumb_img_fit

    mean_curvature_pixel = np.mean([line_lt.curvature_pixel, line_rt.curvature_pixel])
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(blend_on_road, 'Cr : {:.0f}px'.format(mean_curvature_pixel), (500, 30), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(blend_on_road, 'Xe : {:.02f}px'.format(offset_pix), (500, 80), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    return blend_on_road

# 산출된 차선의 중심으로부터의 offset
def compute_offset_from_center(line_lt, line_rt, frame_width):

    if line_lt.detected and line_rt.detected:
        line_lt_bottom = np.mean(line_lt.all_x[line_lt.all_y > 0.95 * line_lt.all_y.max()])
        line_rt_bottom = np.mean(line_rt.all_x[line_rt.all_y > 0.95 * line_rt.all_y.max()])
        lane_width = line_rt_bottom - line_lt_bottom
        midpoint = frame_width / 2
        offset_pix = abs((line_lt_bottom + lane_width / 2) - midpoint)
        # offset_meter = xm_per_pix * offset_pix
    else:
        offset_pix = 0

    return offset_pix

# 카메라 중점과 검출된 차선의 중점을 표시
def draw_lane_center(blend_on_road, line_lt, line_rt):

    h, w = blend_on_road.shape[:2]

    if line_lt.detected and line_rt.detected:
        line_lt_bottom = np.mean(line_lt.all_x[line_lt.all_y > 0.95 * line_lt.all_y.max()])
        line_rt_bottom = np.mean(line_rt.all_x[line_rt.all_y > 0.95 * line_rt.all_y.max()])
        lane_center = int((line_lt_bottom + line_rt_bottom) / 2)
        cv2.circle(blend_on_road, (lane_center, h - 100), 8, (0, 255, 255), -1) # 인식한 주행가능 영역 중점
        cv2.circle(blend_on_road, (int(w / 2), h - 100), 8, (255, 0, 0), -1) # 카메라 중점

    return blend_on_road


def process_pipeline(frame, keep_state=True):

    global line_lt, line_rt, processed_frames


    img_undistorted = undistort(frame, mtx, dist, verbose=False)

    img_binary = binarize(img_undistorted, verbose=False)

    img_birdeye, M, Minv = birdeye(img_binary, verbose=False)

    # 2차 다항식 곡선 적용
    if processed_frames > 0 and keep_state and line_lt.detected and line_rt.detected:
        line_lt, line_rt, img_fit = get_fits_by_previous_fits(img_birdeye, line_lt, line_rt, verbose=False)
    else:
        line_lt, line_rt, img_fit = get_fits_by_sliding_windows(img_birdeye, line_lt, line_rt, n_windows=9, verbose=False)

    offset_pix = compute_offset_from_center(line_lt, line_rt, frame_width=frame.shape[1])

    blend_on_road = draw_back_onto_the_road(img_undistorted, Minv, line_lt, line_rt, keep_state)

    blend_on_road = draw_lane_center(blend_on_road, line_lt, line_rt)

    blend_output = prepare_out_blend_frame(blend_on_road, img_binary, img_birdeye, img_fit, line_lt, line_rt, offset_pix)

    # font = cv2.FONT_HERSHEY_SIMPLEX
    # cv2.putText(blend_output, 'Xe : {:.02f}px'.format(offset_pix), (blend_output.shape[1] - 150, 30), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    processed_frames += 1

    return blend_output


if __name__ == '__main__':

    # ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='camera_cal')
    # ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='video')

    # # mode = 'images'
    # mode = 'video'

    # if mode == 'video':

    #     selector = 'mobility4'
    #     clip = VideoFileClip('{}_video.mp4'.format(selector)).fl_image(process_pipeline)
    #     clip.write_videofile('output_video/out_{}_{}.mp4'.format(selector, time_window), audio=False)

    # else:

    #     test_img_dir = 'test_images'
    #     for test_img in os.listdir(test_img_dir):

    #         frame = cv2.imread(os.path.join(test_img_dir, test_img))

    #         blend = process_pipeline(frame, keep_state=False)

    #         cv2.imwrite('output_images/{}'.format(test_img), blend)

    #         plt.imshow(cv2.cvtColor(blend, code=cv2.COLOR_BGR2RGB))
    #         plt.show()

    # # 웹캠 실시간 영상 처리 확인
    # ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='video')
    # cap = cv2.VideoCapture(0)

    # while True:
    #     ret, frame = cap.read()
    #     blend = process_pipeline(frame, keep_state=False)
    #     cv2.imshow('Lane Detection', blend)
    #     line_lt.print_values()
    #     line_rt.print_values()
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break

    # cap.release()
    # cv2.destroyAllWindows()

    ret, mtx, dist, rvecs, tvecs = calibrate_camera(calib_images_dir='video')

    video_path = 'mobility4_video.mp4'

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        blend = process_pipeline(frame, keep_state=False)
        cv2.imshow('Lane Detection', blend)
        line_lt.print_values()
        line_rt.print_values()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()