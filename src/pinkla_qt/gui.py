import sys, os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir + "/..")
# print(f'current_dir : {current_dir}')
from pinkla_qt.comm_module import *
from pinkla_database.pinkla_db import *

ui_path = "./gui.ui"
from_class = uic.loadUiType(ui_path)[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self, server_ip="0.0.0.0", client_ip="0.0.0.0", port1="8485", port2="8584", port3="8090"):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Pinkla.b')
        center_ui(self)
        print(server_ip, client_ip)
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
        self.sender = None
        self.controller = None
        self.check_password = 0

    def flag_init(self):
        self.isCamSocketOpened, self.isCamSocketOpened2 = [False], [False]
        self.isCameraOn, self.isCameraOn2 = [False], [False]
        self.isRecOn, self.isRecOn2 = [False], [False]
        self.isPinkSocketOpened = False
        self.isLaneDetectionOn = False
        self.isObjectDetectionOn = False

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
        self.camera_th.update.connect(lambda image, result : self.update_image(image, result,
                                                                        self.label_pixmap,
                                                                        self.pixmap, self.camera_th))
        self.camera_th.update.connect(lambda image, result : self.update_record(image, result,
                                                                        self.camera_server))

        self.camera_server2 = SERVER(self.server_ip, self.cam_port2)
        self.camera_th2 = Camera_Th(self, port=self.cam_port2)
        self.camera_th2.daemon = True
        self.camera_th2.update.connect(lambda image, result : self.update_image(image, result,
                                                                        self.label_pixmap_2,
                                                                        self.pixmap2, self.camera_th2))
        self.camera_th2.update.connect(lambda image, result : self.update_record(image, result,
                                                                        self.camera_server2))

    def btn_init(self):
        self.mysql = None
        self.logButton.hide()
        self.logButton.clicked.connect(self.createLogWindow)
        self.useDBButton.clicked.connect(self.init_db)
        self.dbPassword.returnPressed.connect(self.init_db)
        self.dbPassword.setEchoMode(QLineEdit.Password)

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
        self.btn_auto.clicked.connect(lambda: self.yolo_seg_lane_start(self.camera_th))
        self.btn_auto_2.clicked.connect(lambda: self.yolo_object_detect_start(self.camera_th2))

        

    def yolo_seg_lane_start(self, thread):
        if not self.isLaneDetectionOn:
            self.btn_auto.setText('Auto Driving\nSTOP')
            self.isLaneDetectionOn = True
            thread.yolo_lane = True
        else:
            self.btn_auto.setText('Auto Driving\nSTART')
            self.isLaneDetectionOn = False
            thread.yolo_lane = False
            try:
                if self.sender is not None:
                    self.sender.cmd = [0, 100, 5, 0, 0, 0, 0]
            except Exception as e:
                print("yolo_seg_lane_start: ",e)
                pass
    
    def yolo_object_detect_start(self, thread):
        if not self.isObjectDetectionOn:
            self.btn_auto_2.setText('Object Detection\nSTOP')
            self.isObjectDetectionOn = True
            thread.yolo_object = True
        else:
            self.btn_auto_2.setText('Object Detection\nSTART')
            self.isObjectDetectionOn = False
            thread.yolo_object = False
            try:
                if self.sender is not None:
                    self.sender.cmd = [0, 100, 5, 0, 0, 0, 0]
            except Exception as e:
                print("yolo_object_detect_start: ",e)
                pass

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
                print("check_connect_pink: ", e)
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

    def cv2_info_drawing(self, image, thread, result):

        if thread.yolo_lane and thread.result[0][0] is not None:
            # cv2.rectangle(image, (0, int(self.cal_cmd.img_height/2 - 100)), (self.cal_cmd.img_width, self.cal_cmd.img_height), color=(0,0,255), thickness = 5)
            cv2.putText(image, text=f"delta_x: {self.cal_cmd.hor_dist:.2f}, delta_y: {self.cal_cmd.ver_dist:.2f}, angle: {self.cal_cmd.angle:.2f}", org=(50, 80), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(image, text=f"distance: {self.cal_cmd.dist:.2f}", org=(50, 110), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(image, text="target", org=(int(self.cal_cmd.cen_x-20), int(self.cal_cmd.cen_y-20)), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,0,0), thickness=2)

            cv2.line(image, (int(self.cal_cmd.x)+5, int(self.cal_cmd.y)), (int(self.cal_cmd.seg_center_border[0])-5, int(self.cal_cmd.seg_center_border[1])), color=(128,128,128), thickness=5 )
            cv2.circle(image, (int(self.cal_cmd.cen_x), int(self.cal_cmd.cen_y)), radius=10, color=(255,0,0), thickness=-1)
            cv2.arrowedLine(image, (int(self.cal_cmd.img_width/2), int(self.cal_cmd.img_height)+5), (int(self.cal_cmd.cen_x), int(self.cal_cmd.cen_y)), color=(50,50,50), thickness=5, tipLength=0.2)
            cv2.circle(image, (int(self.cal_cmd.img_width/2), int(self.cal_cmd.img_height)), radius = 10, color = (255, 255, 255), thickness = -1)

        return image

    def update_image(self, image, result, label, pix, thread):
        try:
            cv2.putText(image, text=f"{self.cal_cmd.w4:.2f}, {self.cal_cmd.w3:.2f}, {self.cal_cmd.w2:.2f}, {self.cal_cmd.w1:.2f}", org=(50, 20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)
            cv2.putText(image, text=f"linear_x: {self.cal_cmd.lx:.2f}, linear_y: {self.cal_cmd.ly:.2f}, angular_z: {self.cal_cmd.az:.2f}", org=(50, 50), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,255,255), thickness=2)

            if len(thread.result[0]) > 1:
                image = self.cv2_info_drawing(image, thread, result[0])

            h,w,c = image.shape
            qformat_type = QImage.Format_RGB888
            qimage = QImage(image.data, w, h, w*c, qformat_type)
            pixmap = QPixmap.fromImage(qimage)
            pix = pixmap.scaled(label.width(), label.height())
            label.setPixmap(pix)
            label.setAlignment(Qt.AlignCenter)
            
            if thread.yolo_lane:
                vel = self.cal_cmd.move_to_lane_center(thread.result[0])
                # print(seg_result)
                if self.check_password == 1:
                    self.save_data(thread.result[0])
                else:
                    pass

                try:
                    self.sender.cmd = [1, 100, 5, int(vel[0]), int(vel[1]), int(vel[2]), int(vel[3])]
                except Exception as e:
                    # print(e)
                    pass

        except Exception as e:
            # print(e)
            self.show_logo(label, pix)
            pass
        
    def save_data(self, seg_result):
        coordinate = seg_result[-1]
        # try:
        if coordinate:
            lane_data = []
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            border = coordinate[0]
            intersection = coordinate[1]
            middle = coordinate[2]
            target = [self.cal_cmd.cen_x, self.cal_cmd.cen_y]
            
            lane_data.append(current_time)
            lane_data.append(len(border))
            lane_data.append(border)
            lane_data.append(len(intersection))
            lane_data.append(intersection)
            lane_data.append(len(middle))
            lane_data.append(middle)
            lane_data.append(target)
            # print(type(current_time))
            # print(lane_data)
            
            self.mysql.save_lane_data(lane_data)
        else:
            pass
        # except Exception as e:
        #     print(e)
        #     pass

    def click_record(self, flag_rec, recorder, btn):
        if not flag_rec[0]:
            flag_rec[0] = True
            recorder.record_start(width=640, height=480, fps=20)
            btn.setText('RECORD\nSTOP')
        else:
            flag_rec[0] = False
            recorder.record_stop()
            btn.setText('RECORD\nSTART')

    def update_record(self, cvimage, result, recorder):
        try:
            if recorder is not None:
                h,w,c = cvimage.shape
                qformat_type = QImage.Format_RGB888
                qimage = QImage(cvimage.data, w, h, w*c, qformat_type)
                pixmap = QPixmap.fromImage(qimage)

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
        try:
            # if self.controller is None:
            self.controller = KeyboardTeleopController(self.cal_cmd, self.sender)
            self.controller.press_key_control(event)
        except Exception as e: 
            pass
    
    def init_db(self):
        try:
            self.mysql_info = ["database-2.czo0g0uict7o.ap-northeast-2.rds.amazonaws.com", "pinkla"]
            password = self.dbPassword.text()
            self.mysql_info.append(password)
            self.mysql = pinkla_mysql(self.mysql_info)
            self.mysql.init_db()
            self.check_password = 1
            
        except Exception as e:
            self.checkPW.setText("Wrong Password!!!")
            pass
        
        if self.check_password == 1:
            self.logButton.show()
    
    def createLogWindow(self):
        if self.mysql is not None :
            log_window = logClass(self, self.mysql)
            log_window.exec_()
        
        
    def closeEvent(self, event):
        if self.mysql:
            self.mysql.close_mysql() 
        event.accept()
        

class logClass(QDialog):
    def __init__(self, WindowClass):
        super().__init__()
        self.ui = uic.loadUi("db.ui", self)
        self.main_window = WindowClass
        self.show()
        self.log_in(WindowClass)
        
        
    def set_window(self):
        table_name = self.mysql.get_table_name()
        for name in table_name:
            if name == "object_class" or name == "pinkla_event":
                pass
            else:
                self.tableList.addItem(name)
                
    def log_in(self, class_instance):
        self.info = class_instance.mysql_info
        self.mysql = pinkla_mysql(self.info)
        self.tableList.addItem(" ")
        self.set_window()
        
        self.tableList.currentIndexChanged.connect(self.select_table)
            
    def select_table(self):
        current_select = self.tableList.currentText()
        table = self.mysql.select_data(current_select)
        rows, cols = table.shape
        
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(cols)
        self.tableWidget.setHorizontalHeaderLabels(table.columns)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(table.iloc[i, j]))
                self.tableWidget.setItem(i, j, item)
        
        
    def closeEvent(self, event):
        if self.mysql:
            self.mysql.close_mysql() 
        event.accept()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec_())
