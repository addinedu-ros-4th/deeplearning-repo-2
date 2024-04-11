from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *

import cv2, imutils
import socket
import numpy as np
import serial

import time
# import datetime
from datetime import datetime
import psutil
import math

from pinkla_lane.lane_detection import *

cmtx1 = np.array([[474.9308089, 0., 313.10372736],
                  [0., 474.24684641, 254.94399015],
                  [0.,0.,1.]])
dist1 = np.array([[0.0268074362, -0.178310961, -0.000144841081, -0.00103575477, 0.183767484]])

cmtx2 = np.array([[470.86256773, 0., 322.79554974],
                  [0., 470.89842857, 236.76274254],
                  [0.,0.,1.]])
dist2 = np.array([[0.00727918, -0.09059939, -0.00224102, -0.00040328, 0.06114216]])

class SERVER():
    def __init__(self, host='0.0.0.0', port=0000):
        self.s = None
        self.host = host
        self.port = port
        self.conn, self.addr = None, None
        self.writer = None
        self.show = False

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.host, self.port))
            self.s.listen(10)
        except Exception as e:
            print(e)
            pass

    def disconnect(self):
        try:
            pass
        except Exception as e:
            pass

    def undistorted_frame(self, frame):
        cmtx = None
        dist = None
        if self.port == 8485:
            cmtx = cmtx1
            dist = dist1
        else:
            cmtx = cmtx2
            dist = dist2

        undist = cv2.undistort(frame, cmtx, dist)
        return undist

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf
    
    def show_video(self):
        try:
            length = self.recvall(self.conn, 16)
            stringData = self.recvall(self.conn, int(length))
            data = np.fromstring(stringData, dtype = 'uint8')
            frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
            undist = self.undistorted_frame(frame)
            return undist
        except Exception as e:
            return None

    def record_start(self, width=640, height=480, fps=30):
        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f'../../data/{current_time}.avi'
            fourcc = cv2.VideoWriter_fourcc(*'VXID')
            self.writer = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        except Exception as e:
            print(e)
            return None

    def record_stop(self):
        try:
            self.writer.release()
        except Exception as e:
            pass


class CLIENT():
    def __init__(self, host='0.0.0.0', port=0000):
        self.s = None
        self.host = host
        self.port = port
        self.conn, self.addr = None, None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            print(e)


class Socket(QThread):
    update = pyqtSignal(object)

    def __init__(self, host, port):
        super().__init__()
        self.running = True
        self.host = host
        self.port = port
        self.conn, self.addr = None, None
        self.server = SERVER(self.host, self.port)

    def run(self):
        self.server.connect()
        self.server.s.settimeout(0.1)
        while self.running:
            try:
                self.conn, self.addr = self.server.s.accept()
                if self.conn:
                    self.update.emit(self.conn)
                    self.running = False
            except socket.timeout:
                pass
            except Exception as e:
                pass
    
    def disconnect(self):
        try:
            self.conn.close()
            self.server.s.close()
            self.update.emit(False)
            QThread.msleep(100)
        except Exception as e:
            pass

    def stop(self):
        print("stop connection.")
        self.running = False
        try:
            self.disconnect()
        except Exception as e:
            pass

class Camera_Th(QThread):
    update = pyqtSignal(np.ndarray, list)

    def __init__(self, sec=0, parent=None, port=0000):
        super().__init__()
        self.main = parent
        self.running = True
        self.cam_server = SERVER(port=port)
        self.conn = None
        self.source, self.image, self.pixmap = None, None, None

        self.generator = find_road_center()
        self.yolo_lane = False
        self.seg_result = [None]

    def run(self):
        while self.conn is None:
            QThread.msleep(10)
        self.cam_server.conn = self.conn

        while self.running == True:
            self.source = self.cam_server.show_video()
            if self.source is not None:
                if not self.yolo_lane:
                    self.image = self.source.copy()
                else:
                    self.image, self.seg_result = self.generator.get_road_center(self.source.copy())
                try:
                    image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                    self.update.emit(image, self.seg_result)
                except Exception as e:
                    pass
            QThread.msleep(8)

    def cv2_draw_tool(self):
        try:
            pass
        except Exception as e:
            print(e)
            pass

    def stop(self):
        self.running = False


class Socket_Pinkla(QThread):
    update = pyqtSignal(object)
    def __init__(self, host, port):
        super().__init__()
        self.running = True
        self.host = host
        self.port = port
        self.conn, self.addr = None, None
        self.client = CLIENT(self.host, self.port)
        self.s = None

    def run(self):
        self.client.connect()
        connected = False
        self.s = self.client.s
        while self.running:
            try:
                self.s.connect((self.host, self.port))
                connected = True
                if connected:
                    self.running = False
                    self.update.emit(self.s)
            except ConnectionRefusedError:
                print("Waiting for server...")
                connected = False
                QThread.msleep(1000)
                pass
            except Exception as e:
                connected = False
                print(e)
                pass
    
    def disconnect(self):
        try:
            self.s.close()
            self.update.emit(False)
            del self.s
            QThread.msleep(100)
        except Exception as e:
            pass

    def stop(self):
        print("stop connection.")
        self.running = False
        try:
            self.disconnect()
        except Exception as e:
            pass


class Control_Pinkla(QThread):
    update = pyqtSignal(bool)

    def __init__(self, s=None):
        super().__init__()
        self.running = True
        self.cmd = [0, 100, 5, 0, 0, 0, 0]
        self.s = s

    def run(self):
        while self.running:
            try:
                data_str = ','.join(map(str, self.cmd))
                self.s.sendall(data_str.encode())

                self.update.emit(True)
                QThread.msleep(30)
            except Exception as e :
                print(e)
                self.s.close()
                self.update.emit(False)
                self.running = False
                pass

    def stop(self):
        self.running = False
        try:
            self.s.close()
        except Exception as e:
            pass

class LowPassFilter(object):
    def __init__(self, cut_off_freqency, ts):
        self.ts = ts
        self.cut_off_freqency = cut_off_freqency
        self.tau = self.get_tau()

        self.prev_data = 0.
        
    def get_tau(self):
        return 1 / (2 * np.pi * self.cut_off_freqency)

    def filter(self, data):
        val = (self.ts * data + self.tau * self.prev_data) / (self.tau + self.ts)
        self.prev_data = val
        return val

class Cal_Cmd():
    def __init__(self):
        self.lx = 0.0
        self.ly = 0.0
        self.az = 0.0
        self.r = 0.01
        self.b = 0.05

        self.img_width = 640
        self.img_height = 480

        self.angle = 0.0
        self.cen_x, self.cen_y = 0., 0.
        self.x, self.y = 0., 0.
        self.seg_center_border = (0,0)

        self.max_distance = 10

        self.w1, self.w2, self.w3, self.w4 = 0.0, 0.0, 0.0, 0.0

        self.lpf_x = LowPassFilter(5.0, 1)
        self.lpf_y = LowPassFilter(5.0, 1)
        self.lpf_dx = LowPassFilter(0.1, 0.5)
        self.lpf_dy = LowPassFilter(0.1, 0.5)

    def cal(self):
        self.w1 = (1/self.r) * (self.lx-self.ly-self.b*self.az)
        self.w2 = (1/self.r) * (self.lx+self.ly-self.b*self.az)
        self.w3 = (1/self.r) * (self.lx-self.ly+self.b*self.az)
        self.w4 = (1/self.r) * (self.lx+self.ly+self.b*self.az)
        value = [self.w4, self.w3, self.w2, self.w1]
        return value

    def move_to_lane_center(self, seg_result):
        line_center_x = seg_result[0]
        line_center_y = seg_result[1]
        self.seg_center_border = seg_result[2]
        cnt_stop = seg_result[3]

        self.x = self.lpf_x.filter(line_center_x)
        self.y = self.lpf_y.filter(line_center_y)

        self.cen_x = (self.x + self.seg_center_border[0]) / 2
        self.cen_y = (self.y + self.seg_center_border[1]) / 2

        delta_x_t = (self.img_width/2) - self.cen_x
        delta_y_t = (self.img_height) - self.cen_y

        delta_x = self.lpf_dx.filter(delta_x_t)
        delta_y = self.lpf_dy.filter(delta_y_t)
        self.angle = np.arctan2(delta_x, delta_y)

        self.dist = math.sqrt(delta_x**2 + delta_y**2)


        mx = abs(delta_y/ self.max_distance) 
        my = abs(delta_x / self.max_distance)
            
        vx = (delta_x * mx) * -1
        vy = (delta_y * my) * -1
        vz = self.angle

        self.r = 0.025
        self.b = 0.11

        if cnt_stop > 20:
            self.lx = 0.
            self.ly = 0.
            self.az = 0.
            self.dist = 0.
        else:
            self.lx = vx
            self.ly = vy
            self.az = vz

        velo = self.cal()
        return velo

    def print_vels(self, linear_x_velocity, linear_y_velocity, angular_velocity):
        print('linear x velocity {0:.3} | linear y velocity {1:.3} | angular velocity {2:.3}'.format(
            linear_x_velocity, linear_y_velocity, angular_velocity))


class KeyboardTeleopController():
    def __init__(self, cal_cmd, sender):
        self.LIN_VEL_STEP_SIZE = 0.2
        self.ANG_VEL_STEP_SIZE = 2.5
        self.cal_cmd = cal_cmd
        self.sender = sender

    def press_key_control(self, event):
        
        shift_flag = False

        if event.key() == Qt.Key_W:
            self.cal_cmd.ly = 0.0

            if self.cal_cmd.az != 0.0:
                self.cal_cmd.ax = 0.0

            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = 2.0
            elif self.cal_cmd.lx >= 3.0:
                self.cal_cmd.lx = 3.0
            else:
                self.cal_cmd.lx += self.LIN_VEL_STEP_SIZE

        elif event.key() == Qt.Key_X:
            self.cal_cmd.ly = 0.0

            if self.cal_cmd.az != 0.0:
                self.cal_cmd.ax = 0.0

            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = -2.0
            elif self.cal_cmd.lx <= -3.0:
                self.cal_cmd.lx = -3.0
            else:
                self.cal_cmd.lx -= self.LIN_VEL_STEP_SIZE

        elif event.key() == Qt.Key_A:
            if event.modifiers() & Qt.ShiftModifier:
                self.cal_cmd.lx = 0.0
                self.cal_cmd.ly = -2.4
                self.cal_cmd.az = 0.0
            else:
                self.cal_cmd.ly = 0.0
                if self.cal_cmd.az < 0.0:
                    self.cal_cmd.az = 0.0
                if self.cal_cmd.az >= 50.0:
                    self.cal_cmd.az = 50.0
                else:
                    self.cal_cmd.az += self.ANG_VEL_STEP_SIZE

        elif event.key() == Qt.Key_D:
            if event.modifiers() & Qt.ShiftModifier:
                self.cal_cmd.lx = 0.0
                self.cal_cmd.ly = 2.4
                self.cal_cmd.az = 0.0
            else:
                self.cal_cmd.ly = 0.0
                if self.cal_cmd.az > 0.0:
                    self.cal_cmd.az = 0.0
                if self.cal_cmd.az <= -50.0:
                    self.cal_cmd.az = -50.0
                else:
                    self.cal_cmd.az -= self.ANG_VEL_STEP_SIZE

        elif event.key() == Qt.Key_S:
            self.cal_cmd.lx = 0.0
            self.cal_cmd.ly = 0.0
            self.cal_cmd.az = 0.0
        elif event.key() == Qt.Key_Q:
            self.cal_cmd.lx = 2.4
            self.cal_cmd.ly = -2.4
            self.cal_cmd.az = 0.0
        elif event.key() == Qt.Key_E:
            self.cal_cmd.lx = 2.4
            self.cal_cmd.ly = 2.4
            self.cal_cmd.az = 0.0
        elif event.key() == Qt.Key_Z:
            self.cal_cmd.lx = -2.4
            self.cal_cmd.ly = -2.4
            self.cal_cmd.az = 0.0
        elif event.key() == Qt.Key_C:
            self.cal_cmd.lx = -2.4
            self.cal_cmd.ly = 2.4
            self.cal_cmd.az = 0.0

        else:
            if event.key() == Qt.Key_Shift:
                shift_flag = True
            else:
                self.cal_cmd.lx = 0.0
                self.cal_cmd.ly = 0.0
                self.cal_cmd.az = 0.0

        if not shift_flag:
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.ly, self.cal_cmd.az)
            value = self.cal_cmd.cal()
