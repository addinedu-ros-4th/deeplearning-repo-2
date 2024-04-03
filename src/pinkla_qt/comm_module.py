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

cmtx2 = np.array([[470.86256773,0.,322.79554974],
                  [0.,470.89842857,236.76274254],
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
            # self.conn.close()
            # self.s.close()
            # del self.s
            pass
        except Exception as e:
            pass

    def undistorted_frame(self, frame):
        cam = ""
        cmtx = None
        dist = None
        if self.port == 8485:
            cmtx = cmtx1
            dist = dist1
            cam = "Lane"
        else:
            cmtx = cmtx2
            dist = dist2
            cam = "Object"

        if not self.show:
            self.show =True
            print(f"Connected {cam} Camera.")
            print(cmtx)
            print(dist)

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
            # return frame
        except Exception as e:
            # print(e)
            return None

    def record_start(self, width=640, height=480, fps=30):
        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f'../../data/{current_time}.avi'
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        except Exception as e:
            print(e)
            return None

    def record_stop(self):
        try:
            self.writer.release()
        except Exception as e:
            # print(e)
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
            # del self.conn
            # del self.server.s
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

class Yolo_Th(QThread):
    update = pyqtSignal(np.ndarray, list)

    def __init__(self):
        super().__init__()
        self.running = True
        self.source = None
        self.image = None
        self.generator = find_road_center()
        
    def run(self):
        while self.running == True:
            value = [0.,0.,0.,0.]
            if self.source is not None:
                self.image, value = self.generator.get_road_center(self.source)

                self.update.emit(self.image, value)
            QThread.msleep(8)

    def stop(self):
        self.running = False
        del self.source
        del self.image
        # del self.generator

class Camera_Th(QThread):
    # update = pyqtSignal(QPixmap, int)
    update = pyqtSignal(QPixmap, list)

    def __init__(self, sec=0, parent=None, port=0000):
        super().__init__()
        self.main = parent
        self.running = True
        self.cam_server = SERVER(port=port)
        self.conn = None
        self.source, self.image, self.pixmap = None, None, None

        self.generator = find_road_center()
        self.yolo_lane = False
        self.yolo = None
        self.test_img, self.test_value = None, None

    def run(self):
        while self.conn is None:
            QThread.msleep(10)
        self.cam_server.conn = self.conn

        while self.running == True:
            self.source = self.cam_server.show_video()
            if self.source is not None:
                self.value = [0.,0.,0.,0.]

                if self.yolo is not None:
                    self.yolo.source = self.source.copy()

                if not self.yolo_lane:
                    self.image = self.source.copy()
                else:
                    # self.image, value = self.generator.get_road_center(self.source.copy())

                    if self.test_img is not None and self.test_value is not None:
                        # image = cv2.cvtColor(self.test_img, cv2.COLOR_BGR2RGB)
                        self.image = self.test_img
                        self.value = self.test_value

                image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                try:
                    h,w,c = image.shape
                    qformat_type = QImage.Format_RGB888
                    qimage = QImage(image.data, w, h, w*c, qformat_type)
                    self.pixmap = QPixmap.fromImage(qimage)
                    self.update.emit(self.pixmap, self.value)

                except Exception as e:
                    print(e)
                    pass
            QThread.msleep(8)

    def get_lane_info(self, image, value):
        self.test_img = image
        self.test_value = value

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


class Cal_Cmd():
    def __init__(self):
        self.lx = 0.0
        self.ly = 0.0
        self.az = 0.0
        self.r = 0.025
        # self.b = 0.11
        self.b = 0.08

        self.w1, self.w2, self.w3, self.w4 = 0.0, 0.0, 0.0, 0.0

    def cal(self):
        # cal
        
        self.w1 = (1/self.r) * (self.lx-self.ly-self.b*self.az)
        self.w2 = (1/self.r) * (self.lx+self.ly-self.b*self.az)
        self.w3 = (1/self.r) * (self.lx-self.ly+self.b*self.az)
        self.w4 = (1/self.r) * (self.lx+self.ly+self.b*self.az)

        # value = [self.w1, self.w2, self.w3, self.w4]
        value = [self.w4, self.w3, self.w2, self.w1]

        # after 3 sec -> zero

        return value

    def moveTo(self, delta):
        angle = math.atan2(delta, 418)

        self.lx = 2.2
        self.ly = 0.0
        self.az = angle * -30.0

        self.w1 = (1/self.r) * (self.lx-self.ly-self.b*self.az)
        self.w2 = (1/self.r) * (self.lx+self.ly-self.b*self.az)
        self.w3 = (1/self.r) * (self.lx-self.ly+self.b*self.az)
        self.w4 = (1/self.r) * (self.lx+self.ly+self.b*self.az)
        value = [self.w4, self.w3, self.w2, self.w1]
        # print(angle, value)
        # print(angle)

        return value
        
    def moveTo2(self, value):
        return value

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
            # print(value)

        try:
            self.sender.cmd = [1, 100, 5, int(value[0]), int(value[1]), int(value[2]), int(value[3])]
        except Exception as e:
            # print(e)
            pass


def center_ui(object):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - object.width()) // 2
        y = (screen_geometry.height() - object.height()) // 2
        object.move(x, y)
