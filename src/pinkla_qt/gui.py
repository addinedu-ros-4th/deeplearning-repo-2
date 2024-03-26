from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *

import sys, os
import cv2, imutils
import time
import datetime
import numpy as np
import rclpy
import psutil

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir + "/..")
print(f'current_dir : {current_dir}')
from pinkla_qt.comm_module import *

ui_path = "./gui.ui"
from_class = uic.loadUiType(ui_path)[0]

HOST = '192.168.0.23'
CAM_PORT = 8485

PINK_HOST = '192.168.0.100'
PINK_PORT = 8090

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
    update = pyqtSignal(QPixmap)

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running = True

        self.cam_server = SERVER()
        self.conn = None
        self.source, self.pixmap = None, None

    def run(self):
        while self.conn is None:
            QThread.msleep(10)
        self.cam_server.conn = self.conn

        while self.running == True:
            self.source = self.cam_server.show_video()
            if self.source is not None:
                image = cv2.cvtColor(self.source, cv2.COLOR_BGR2RGB) 
                h,w,c = image.shape
                qformat_type = QImage.Format_RGB888
                qimage = QImage(image.data, w, h, w*c, qformat_type)
                self.pixmap = QPixmap.fromImage(qimage)
                self.update.emit(self.pixmap)
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
        self.cmd = [0, 5, 0, 0, 0, 0]
        self.s = s

    def run(self):
        while self.running:
            try:
                data_str = ','.join(map(str, self.cmd))
                self.s.sendall(data_str.encode())

                self.update.emit(True)
                QThread.msleep(20)
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
        

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('pinkla.b')
        self.ui_init()
        self.socket_module()
        self.camera_module()
        self.source = None
        self.show_logo()

    def ui_init(self):
        self.btn_record.hide()
        self.btn_camera.hide()
        self.btn_pinkla_socket.clicked.connect(self.click_pinkla_socket)
        self.btn_cam_socket.clicked.connect(self.click_cam_socket)
        
        self.btn_camera.clicked.connect(self.click_camera)
        self.btn_record.clicked.connect(self.click_record)

        self.btn_for.clicked.connect(self.click_forward)
        self.btn_st.clicked.connect(self.click_stop)


        self.pixmap = QPixmap(self.label_pixmap.width(), self.label_pixmap.height())
        self.pixmap.fill(Qt.white)
        self.label_pixmap.setAlignment(Qt.AlignCenter)
        self.label_pixmap.setPixmap(self.pixmap)

        self.conn, self.addr = None, None
        self.pinkla_conn, self.pinkla_addr = None, None

    def click_forward(self):
        self.sender.cmd = [0,8,0,0,0,0]
    def click_stop(self):
        self.sender.cmd = [0,5,0,0,0,0]

    def socket_module(self):
        self.isCamSocketOpened = False
        self.isPinkSocketOpened = False

        self.cam_socket = Socket(HOST, CAM_PORT)
        self.cam_socket.daemon = True
        self.cam_socket.update.connect(self.check_connect_cam)

        self.pinkla_socket = Socket_Pinkla(PINK_HOST, PINK_PORT)
        self.pinkla_socket.daemon = True
        self.pinkla_socket.update.connect(self.check_connect_pink)

    def camera_module(self):
        self.isCameraOn = False
        self.isRecOn = False
        self.camera_server = SERVER(HOST, CAM_PORT)
        self.camera_th = Camera_Th(self)
        self.camera_th.daemon = True
        self.camera_th.update.connect(self.update_image)
        self.camera_th.update.connect(self.update_record)

    def control(self, flag):
        if not flag:
            print("server's disconnect ")
            self.btn_pinkla_socket.setText('PINKLA\nCONNECT')
            self.sender.s.close()
            self.sender.running = False
            self.isPinkSocketOpened = False

    def check_connect_pink(self, conn):
        if conn:
            self.isPinkSocketOpened = True
            self.pinkla_conn = conn
            self.pinkla_socket.running = False
            QMessageBox.information(self, "PINKLA Connection Status", "PINKLA Connected!")
            self.btn_pinkla_socket.setText('PINKLA\nDISCONNECT')
            print(self.pinkla_conn)

            self.sender = Control_Pinkla(self.pinkla_socket.s)
            self.sender.daemon = True
            self.sender.update.connect(self.control)

            self.sender.running = True
            self.sender.start()

        else:
            QMessageBox.warning(self, "PINKLA Connection Status", "PINKLA Disconnected!")
            self.btn_pinkla_socket.setText('PINKLA\nCONNECT')
            self.isPinkSocketOpened = False
            try:
                self.sender.running = False
                self.sender.stop()
                del self.sender
            except Exception as e:
                pass

    def check_connect_cam(self, conn):
        if conn:
            self.conn = conn
            self.cam_socket.running = False
            QMessageBox.information(self, "CAMERA Connection Status", "CAMERA Connected!")
            print(self.conn)
            self.isCamSocketOpened = True
        else:
            QMessageBox.warning(self, "CAMERA Connection Status", "CAMERA Disconnected!")
            self.isCamSocketOpened = False

    def click_cam_socket(self):
        self.isCameraOn = False
        self.isRecOn = False
        if not self.isCamSocketOpened:
            self.btn_cam_socket.setText('CAMERA\nDISCONNECT')
            self.btn_camera.setText('CAMERA\nOPEN')
            self.btn_camera.show()
            self.btn_record.hide()
            self.cam_socket_connection()
        else:
            self.btn_cam_socket.setText('CAMERA\nCONNECT')
            self.btn_camera.hide()
            self.btn_record.hide()
            self.cam_socket_connection()

    def click_pinkla_socket(self):
        if not self.isPinkSocketOpened:
            self.isPinkSocketOpened = True
            self.btn_pinkla_socket.setText('PINKLA\nSTOP CONNECTING')
            self.pinkla_socket.running = True
            self.pinkla_socket.start()
        else:
            self.isPinkSocketOpened = False
            self.btn_pinkla_socket.setText('PINKLA\nCONNECT')
            self.pinkla_socket.running = False
            self.pinkla_socket.stop()

    def cam_socket_connection(self):
        if not self.isCamSocketOpened:
            self.cam_socket.running = True
            self.cam_socket.start()
        else:
            try:
                self.cam_socket.running = False
                self.cam_socket.stop()
                self.show_logo()
            except Exception as e:
                # print(e)
                pass

    def click_camera(self):
        if self.isCameraOn == False:
            self.btn_camera.setText('CAMERA\nCLOSE')
            self.btn_record.show()
            self.camera_connection()
            self.isRecOn = False
        else:
            self.btn_camera.setText('CAMERA\nOPEN')
            self.btn_record.hide()
            self.camera_connection()
            self.isRecOn = False

    def camera_connection(self):
        if not self.isCameraOn:
            self.isCameraOn = True
            self.camera_th.conn = self.conn
            self.camera_th.running = True 
            self.camera_th.start()
        else:
            self.isCameraOn = False
            self.camera_th.running = False
            self.camera_th.stop()

    def update_image(self, pixmap): 
        try:
            self.pixmap = pixmap.scaled(self.label_pixmap.width(), self.label_pixmap.height())
            self.label_pixmap.setPixmap(self.pixmap)
            self.label_pixmap.setAlignment(Qt.AlignCenter)
        except Exception as e:
            # print(e)
            self.show_logo()
            pass

    def click_record(self):
        if not self.isRecOn:
            self.isRecOn = True
            self.camera_server.record_start(width=640, height=480, fps=30)
            print(self.camera_server.writer)
            self.btn_record.setText('RECORD\nSTOP')

        else:
            self.isRecOn = False
            self.camera_server.record_stop()
            self.btn_record.setText('RECORD\nSTART')

    def update_record(self, pixmap):
        try:
            if self.camera_server is not None:
                image = pixmap.toImage()
                width, height = image.width(), image.height()
                ptr = image.bits()
                ptr.setsize(image.byteCount())
                arr = np.array(ptr).reshape(height, width, 4)
                rgb_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
                if self.camera_server.writer is not None:
                    self.camera_server.writer.write(rgb_image)
        except Exception as e:
            # print(e)
            pass
    
    def show_logo(self):
        self.logo_img = cv2.imread("./design/pinkla_logo.png")
        self.logo_img = cv2.cvtColor(self.logo_img, cv2.COLOR_BGR2RGB)
        h,w,c = self.logo_img.shape 
        qimage = QImage(self.logo_img.data, w, h, w*c, QImage.Format_RGB888)
        self.pixmap = self.pixmap.fromImage(qimage)
        self.pixmap = self.pixmap.scaled(self.label_pixmap.width(), self.label_pixmap.height())
        self.label_pixmap.setPixmap(self.pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec_())
