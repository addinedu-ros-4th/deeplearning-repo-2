import sys, os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir + "/..")
# print(f'current_dir : {current_dir}')
from pinkla_qt.comm_module import *
# from pinkla_database.pinkla_db import *

ui_path = "./gui.ui"
from_class = uic.loadUiType(ui_path)[0]

HOST = '192.168.0.197'
CAM_PORT = 8485
CAM_PORT2 = 8584

PINK_HOST = '192.168.0.100'
PINK_PORT = 8090

class WindowClass(QMainWindow, from_class):
    def __init__(self, server_ip="192.168.0.197", client_ip="192.168.0.100", port1="8485", port2="8584", port3="8090"):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Pinkla.b')
        center_ui(self)

        self.server_ip = server_ip
        self.client_ip = client_ip
        self.cam_port1 = int(port1)
        self.cam_port2 = int(port2)
        self.serial_port3 = int(port3)
        
        self.conn, self.addr = [None], [None]
        self.conn2, self.addr2 = [None], [None]
        self.pinkla_conn, self.pinkla_addr = None, None
        self.source = None

        self.flag_init()
        self.ui_init()
        self.socket_module_init()
        self.camera_module_init()
        self.btn_init()

        self.show_logo(self.label_pixmap, self.pixmap)
        self.show_logo(self.label_pixmap_2, self.pixmap2)

        self.cal_cmd = Cal_Cmd()
        
        # self.mysql_info = ["localhost", "joe", "0000", "pinkla_base"]
        
        # self.db = pinkla_mysql()
        
        # self.db.init_db(self.mysql_info)

    def flag_init(self):
        self.isCamSocketOpened, self.isCamSocketOpened2 = [False], [False]
        self.isCameraOn, self.isCameraOn2 = [False], [False]
        self.isRecOn, self.isRecOn2 = [False], [False]
        self.isPinkSocketOpened = False
        self.isLaneDetectionOn = False

    def ui_init(self):
        self.setFocusPolicy(Qt.StrongFocus)

        self.btn_record.hide()
        self.btn_camera.hide()
        self.btn_record_2.hide()
        self.btn_camera_2.hide()
        
        self.pixmap = QPixmap(self.label_pixmap.width(), self.label_pixmap.height())
        self.pixmap.fill(Qt.white)
        self.pixmap2 = QPixmap(self.label_pixmap_2.width(), self.label_pixmap_2.height())
        self.pixmap2.fill(Qt.white)

        self.label_pixmap.setAlignment(Qt.AlignCenter)
        self.label_pixmap.setPixmap(self.pixmap)
        self.label_pixmap_2.setAlignment(Qt.AlignCenter)
        self.label_pixmap_2.setPixmap(self.pixmap2)

    def socket_module_init(self):
        self.cam_socket = Socket(self.server_ip, self.cam_port1)
        self.cam_socket.daemon = True
        self.cam_socket.update.connect(lambda conn: self.check_connect_cam(conn, 
                                                                           self.conn, 
                                                                           self.cam_socket, 
                                                                           self.isCamSocketOpened))

        self.cam_socket2 = Socket(self.server_ip, self.cam_port2)
        self.cam_socket2.daemon = True
        self.cam_socket2.update.connect(lambda conn: self.check_connect_cam(conn, 
                                                                           self.conn2, 
                                                                           self.cam_socket2, 
                                                                           self.isCamSocketOpened2))


        self.pinkla_socket = Socket_Pinkla(self.client_ip, self.serial_port3)
        self.pinkla_socket.daemon = True
        self.pinkla_socket.update.connect(self.check_connect_pink)

    def camera_module_init(self):
        self.camera_server = SERVER(self.server_ip, self.cam_port1)
        self.camera_th = Camera_Th(self, port=self.cam_port1)
        self.camera_th.daemon = True
        self.camera_th.update.connect(lambda pixmap : self.update_image(pixmap,
                                                                        self.label_pixmap,
                                                                        self.pixmap))
        self.camera_th.update.connect(lambda pixmap : self.update_record(pixmap,
                                                                        self.camera_server))

        self.camera_server2 = SERVER(self.server_ip, self.cam_port2)
        self.camera_th2 = Camera_Th(self, port=self.cam_port2)
        self.camera_th2.daemon = True
        self.camera_th2.update.connect(lambda pixmap : self.update_image(pixmap,
                                                                        self.label_pixmap_2,
                                                                        self.pixmap2))
        self.camera_th2.update.connect(lambda pixmap : self.update_record(pixmap,
                                                                        self.camera_server2))

    def btn_init(self):
        self.btn_cam_socket.clicked.connect(lambda: self.click_cam_socket(self.isCamSocketOpened, self.isCameraOn, self.isRecOn,
                                                                          self.cam_socket,
                                                                          self.btn_cam_socket,
                                                                          self.btn_camera,
                                                                          self.btn_record,
                                                                          self.label_pixmap,
                                                                          self.pixmap,
                                                                          self.camera_th))
        self.btn_camera.clicked.connect(lambda: self.click_camera(self.isCameraOn, self.isRecOn,
                                                                  self.btn_camera,
                                                                  self.btn_record,
                                                                  self.camera_th,
                                                                  self.conn))
        self.btn_record.clicked.connect(lambda: self.click_record(self.isRecOn, self.camera_server, self.btn_record))


        self.btn_cam_socket_2.clicked.connect(lambda: self.click_cam_socket(self.isCamSocketOpened2, self.isCameraOn2, self.isRecOn2,
                                                                          self.cam_socket2,
                                                                          self.btn_cam_socket_2,
                                                                          self.btn_camera_2,
                                                                          self.btn_record_2,
                                                                          self.label_pixmap_2,
                                                                          self.pixmap2,
                                                                          self.camera_th2))
        self.btn_camera_2.clicked.connect(lambda: self.click_camera(self.isCameraOn2, self.isRecOn2,
                                                                  self.btn_camera_2,
                                                                  self.btn_record_2,
                                                                  self.camera_th2,
                                                                  self.conn2))
        self.btn_record_2.clicked.connect(lambda: self.click_record(self.isRecOn2, self.camera_server2, self.btn_record_2))


        self.btn_pinkla_socket.clicked.connect(self.click_pinkla_socket)
        # self.btn_for.clicked.connect(self.click_forward)
        # self.btn_st.clicked.connect(self.click_stop)
        self.btn_auto.clicked.connect(lambda: self.seg_yolo_start(self.camera_th))

    def seg_yolo_start(self, thread):
        if not self.isLaneDetectionOn:
            self.btn_auto.setText('Auto Driving\nSTOP')
            self.isLaneDetectionOn = True
            thread.yolo = True
        else:
            self.btn_auto.setText('Auto Driving\nSTART')
            self.isLaneDetectionOn = False
            thread.yolo = False

    def click_cam_socket(self, flag_soc, flag_cam, flag_rec, socket, btn_soc, btn_cam, btn_rec, label, pix, thread):
        flag_cam[0] = False
        flag_rec[0] = False
        thread.stop()
        if not flag_soc[0]:
            btn_soc.setText('CAMERA\nDISCONNECT')
            btn_cam.setText('CAMERA\nOPEN')
            btn_cam.show()
            btn_rec.hide()
        else:
            btn_soc.setText('CAMERA\nCONNECT')
            btn_cam.hide()
            btn_rec.hide()
        self.cam_socket_connection(flag_soc, socket, label, pix)

    def cam_socket_connection(self, flag, socket, label, pix):
        if not flag[0]:
            flag[0] = True
            socket.running = True
            socket.start()
        else:
            try:
                flag[0] = False
                socket.running = False
                socket.stop()
                self.show_logo(label, pix)
            except Exception as e:
                # print(e)
                pass

    def check_connect_cam(self, conn, self_conn, self_cam_soc, self_cam_flag):
        if conn:
            self_conn[0] = conn
            self_cam_soc.running = False
            QMessageBox.information(self, "CAMERA Connection Status", "CAMERA Connected!")
            self_cam_flag[0] = True
        else:
            QMessageBox.warning(self, "CAMERA Connection Status", "CAMERA Disconnected!")
            self_cam_flag[0] = False

    def click_camera(self, flag_cam, flag_rec, btn_cam, btn_rec, thread, conn):
        if flag_cam[0] == False:
            btn_cam.setText('CAMERA\nCLOSE')
            btn_rec.show()
            flag_rec[0] = False
        else:
            btn_cam.setText('CAMERA\nOPEN')
            btn_rec.hide()
            flag_rec[0] = False
        self.camera_connection(flag_cam, thread, conn)

    def camera_connection(self, flag, thread, conn):
        if not flag[0]:
            flag[0] = True
            thread.conn = conn[0]
            thread.running = True 
            thread.start()
        else:
            flag[0] = False
            thread.running = False
            thread.stop()
        

    def control(self, flag):
        # self.sender.cmd = [0, 100, 5, 0, 0, 0, 0]
        if not flag:
            print("server's disconnect ")
            self.btn_pinkla_socket.setText('PINKLA\nCONNECT')
            self.sender.s.close()
            self.sender.running = False
            self.isPinkSocketOpened = False

    def click_forward(self):
        self.sender.cmd = [0,100,8,0,0,0,0]
    def click_stop(self):
        self.sender.cmd = [0,100,5,0,0,0,0]


    def check_connect_pink(self, conn):
        if conn:
            self.isPinkSocketOpened = True
            self.pinkla_conn = conn
            self.pinkla_socket.running = False
            QMessageBox.information(self, "PINKLA Connection Status", "PINKLA Connected!")
            self.btn_pinkla_socket.setText('PINKLA\nDISCONNECT')

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

    def update_image(self, pixmap, label, pix): 
        try:
            pix = pixmap.scaled(label.width(), label.height())
            label.setPixmap(pix)
            label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            self.show_logo(label, pix)
            pass

    def click_record(self, flag_rec, recorder, btn):
        if not flag_rec[0]:
            flag_rec[0] = True
            recorder.record_start(width=640, height=480, fps=30)
            btn.setText('RECORD\nSTOP')
        else:
            flag_rec[0] = False
            recorder.record_stop()
            btn.setText('RECORD\nSTART')

    def update_record(self, pixmap, recorder):
        try:
            if recorder is not None:
                image = pixmap.toImage()
                width, height = image.width(), image.height()
                ptr = image.bits()
                ptr.setsize(image.byteCount())
                arr = np.array(ptr).reshape(height, width, 4)
                rgb_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
                if recorder.writer is not None:
                    recorder.writer.write(rgb_image)
        except Exception as e:
            # print(e)
            pass
    
    def show_logo(self, label, pix):
        self.logo_img = cv2.imread("./design/pinkla_logo.png")
        self.logo_img = cv2.cvtColor(self.logo_img, cv2.COLOR_BGR2RGB)
        h,w,c = self.logo_img.shape 
        qimage = QImage(self.logo_img.data, w, h, w*c, QImage.Format_RGB888)
        pix = pix.fromImage(qimage)
        pix = pix.scaled(label.width(), label.height())
        label.setPixmap(pix)


    def keyPressEvent(self, event):
        LIN_VEL_STEP_SIZE = 0.2
        ANG_VEL_STEP_SIZE = 2.5

        if event.key() == Qt.Key_W:
            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = 3.0
            # 선속도 직진 3.0 보다 빠르거나 후진 -3.0보다 빠르면 직진속도 추가
            elif (self.cal_cmd.lx >= 3.0) or (-3.0 >= self.cal_cmd.lx):
                self.cal_cmd.lx = self.cal_cmd.lx + LIN_VEL_STEP_SIZE
            # 후진속도 -3.0 아래로 감속 시키면 선속도 초기화
            elif self.cal_cmd.lx > -3.0:
                self.cal_cmd.lx = 0.0
            # 각속도 초기화
            if self.cal_cmd.az != 0.0:
                self.cal_cmd.az = 0.0
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.az)
        elif event.key() == Qt.Key_X:
            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = -3.0         
            # 선속도 후진 -3.0 보다 빠르거나 직진 3.0보다 빠르면 후진속도 추가                
            elif (-3.0 >= self.cal_cmd.lx) or (self.cal_cmd.lx >= 3.0):
                self.cal_cmd.lx = self.cal_cmd.lx - LIN_VEL_STEP_SIZE
            # 선속도 직진 3.0아래로 감속 시키면 선속도 초기화
            elif 3.0 > self.cal_cmd.lx:
                self.cal_cmd.lx = 0.0
            # 각속도 초기화
            if self.cal_cmd.az != 0.0:
                self.cal_cmd.az = 0.0                               
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.az)
        elif event.key() == Qt.Key_A:
            if self.cal_cmd.az == 0.0:
                self.cal_cmd.az = 5.0
            elif (self.cal_cmd.az >= 5.0):
                self.cal_cmd.az = self.cal_cmd.az + ANG_VEL_STEP_SIZE
            elif 0.0 > self.cal_cmd.az:
                self.cal_cmd.az = 0.0       
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.az)            
        elif event.key() == Qt.Key_D:
            if self.cal_cmd.az == 0.0:
                self.cal_cmd.az = -5.0
            elif (-5.0 >= self.cal_cmd.az):                
                self.cal_cmd.az = self.cal_cmd.az - ANG_VEL_STEP_SIZE
            elif self.cal_cmd.az > 0.0:
                self.cal_cmd.az = 0.0  
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.az)            
        elif event.key() == Qt.Key_S:
            self.cal_cmd.lx = 0.0
            self.cal_cmd.az = 0.0          
            self.cal_cmd.print_vels(self.cal_cmd.lx, self.cal_cmd.az)
        value = self.cal_cmd.cal()
        # print(value)
        try:
            self.sender.cmd = [1, 100, 5, int(value[0]), int(value[1]), int(value[2]), int(value[3])]
        except Exception as e:
            print(e)
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec_())
