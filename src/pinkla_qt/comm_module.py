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


class Camera_Th(QThread):
    update = pyqtSignal(QPixmap, int, list)

    def __init__(self, sec=0, parent=None, port=0000):
        super().__init__()
        self.main = parent
        self.running = True
        self.generator = find_load_center()
        self.cam_server = SERVER(port=port)
        self.conn = None
        self.source, self.image, self.pixmap = None, None, None
        self.yolo_lane = False
        self.error = 0
        self.coordinate = []

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
                    self.image, self.error, self.coordinate = self.generator.get_road_center(self.source.copy())

                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                h,w,c = self.image.shape
                qformat_type = QImage.Format_RGB888
                qimage = QImage(self.image.data, w, h, w*c, qformat_type)
                self.pixmap = QPixmap.fromImage(qimage)
                self.update.emit(self.pixmap, self.error, self.coordinate)
            QThread.msleep(8)

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

    def moveTo(self, error):
        angle = math.atan2(error, 360)

        self.lx = 2.2
        self.ly = 0.0
        self.az = angle * -40.0

        self.w1 = (1/self.r) * (self.lx-self.ly-self.b*self.az)
        self.w2 = (1/self.r) * (self.lx+self.ly-self.b*self.az)
        self.w3 = (1/self.r) * (self.lx-self.ly+self.b*self.az)
        self.w4 = (1/self.r) * (self.lx+self.ly+self.b*self.az)
        value = [self.w4, self.w3, self.w2, self.w1]
        print(angle, value)

        return value
        
        
    def print_vels(self, linear_velocity, angular_velocity):
        print('currently:\tlinear velocity {0}\t angular velocity {1} '.format(
            linear_velocity,
            angular_velocity))

def center_ui(object):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - object.width()) // 2
        y = (screen_geometry.height() - object.height()) // 2
        object.move(x, y)
