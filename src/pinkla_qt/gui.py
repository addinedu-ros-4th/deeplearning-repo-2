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

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir + "/..")
print(f'current_dir : {current_dir}')
from pinkla_camera.server.cam_module import *
# from th_socket import *

ui_path = "./gui.ui"
from_class = uic.loadUiType(ui_path)[0]

HOST = '192.168.0.23'
PORT = 8485

class Socket(QThread):
    update = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = True
        self.host = HOST
        self.port = PORT
        self.conn, self.addr = None, None
        self.cam_server = CAM_SERVER(self.host, self.port)

    def run(self):
        self.cam_server.connect()
        self.cam_server.s.settimeout(0.1)
        while self.running:
            try:
                # print("waiting connection...")
                self.conn, self.addr = self.cam_server.s.accept()
                # print(conn)
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
            self.update.emit(False)
            del self.conn
            del self.cam_server.s
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
    update = pyqtSignal()

    def __init__(self, sec=0, parent=None):
        super().__init__()
        self.main = parent
        self.running = True

        self.cam_server = CAM_SERVER()
        self.conn = None

    def run(self):
        print("camera start")
        while self.running == True:
            self.update.emit() 
            QThread.msleep(10)
        
    def stop(self):
        print("camera stop")
        self.running = False


class Control_pinkla(QThread):
    update = pyqtSignal(str)

    def __init__(self):
        super().__init__()



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
        self.btn_camera.clicked.connect(self.click_camera)
        self.btn_raspi.clicked.connect(self.click_raspi)

        self.pixmap = QPixmap(self.label_pixmap.width(), self.label_pixmap.height())
        self.pixmap.fill(Qt.white)
        self.label_pixmap.setAlignment(Qt.AlignCenter)
        self.label_pixmap.setPixmap(self.pixmap)

        self.conn, self.addr = None, None

    # socket on -> camera on/off -> record on/off
    # socket off -> camera off, record off
        
    def socket_module(self):
        self.isSocketOpened = False

        self.socket = Socket()
        self.socket.daemon = True
        self.socket.update.connect(self.check_connect)
        
    def camera_module(self):
        self.isCameraOn = False

        self.camera_server = CAM_SERVER(HOST, PORT)
        self.camera_th = Camera_Th(self)
        self.camera_th.daemon = True
        self.camera_th.update.connect(self.update_image)


    def check_connect(self, conn):
        if conn:
            self.conn = conn
            self.socket.running = False
            QMessageBox.information(self, "Connection Status", "Connected!")
            print(self.conn)
            self.isSocketOpened = True
        else:
            QMessageBox.warning(self, "Connection Status", "Disconnected!")
            self.isSocketOpened = False

    def click_raspi(self):
        self.isCameraOn = False
        if not self.isSocketOpened:
            self.btn_raspi.setText('RasPi5\nDISCONNECT')
            self.btn_camera.setText('CAMERA\nOPEN')
            self.btn_camera.show()
            self.btn_record.hide()
            self.pi_socket_connection()
        else:
            self.btn_raspi.setText('RasPi5\nCONNECT')
            self.btn_camera.hide()
            self.btn_record.hide()
            self.pi_socket_connection()
    
    def pi_socket_connection(self):
        if not self.isSocketOpened:
            self.socket.running = True
            self.socket.start()
        else:
            try:
                self.socket.running = False
                self.socket.stop()
            except Exception as e:
                print(e)
                pass

    def click_camera(self):
        if self.isCameraOn == False:
            self.btn_camera.setText('CAMERA\nCLOSE')
            self.btn_record.show()
            # self.record.stop()
            self.camera_connection()
        else:
            self.btn_camera.setText('CAMERA\nOPEN')
            self.btn_record.hide()
            # self.record.stop()

            self.camera_connection()
            self.show_logo()

    def camera_connection(self):
        if not self.isCameraOn:
            self.isCameraOn = True
            self.camera_th.running = True 
            self.camera_th.start()
        else:
            self.isCameraOn = False
            self.camera_th.running = False
            self.camera_th.stop()

    def update_image(self): 
        try:
            if self.conn and self.isCameraOn:
                self.camera_server.conn = self.conn
                self.source = self.camera_server.show_video()
                if self.source is not None:
                    image = cv2.cvtColor(self.source, cv2.COLOR_BGR2RGB) # ui 출력용 데이터
                    h,w,c = image.shape
                    qformat_type = QImage.Format_RGB888
                    qimage = QImage(image.data, w, h, w*c, qformat_type)

                    self.pixmap = self.pixmap.fromImage(qimage)
                    self.pixmap = self.pixmap.scaled(self.label_pixmap.width(), self.label_pixmap.height())

                    self.label_pixmap.setPixmap(self.pixmap)
                else:
                    # self.show_logo()
                    pass

        except Exception as e:
            print(e)
            self.show_logo()
            pass


    def record(self):
        pass

    def show_logo(self):
        self.logo_img = cv2.imread("./design/pinkla_logo.png")
        self.logo_img = cv2.cvtColor(self.logo_img, cv2.COLOR_BGR2RGB)
        h,w,c = self.logo_img.shape 
        qimage = QImage(self.logo_img.data, w, h, w*c, QImage.Format_RGB888)
        self.pixmap = self.pixmap.fromImage(qimage)
        # self.pixmap = self.pixmap.scaled(self.label_pixmap.width(), self.label_pixmap.height())
        self.label_pixmap.setPixmap(self.pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec_())
