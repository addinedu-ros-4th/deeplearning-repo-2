from pinkla_qt.module.common import *
from pinkla_qt.module.commun import *

class Camera_Th(QThread):
    update = pyqtSignal(np.ndarray, list)

    def __init__(self, sec=0, parent=None, port=0000):
        super().__init__()
        self.main = parent
        self.running = True
        self.cam_server = CAMERA_SERVER(port=port)
        self.conn = None
        self.source, self.image, self.pixmap = None, None, None
        self.previous_result = None

        self.object_generator = Find_Object()
        self.seg_generator = Find_Road_Center()
        self.recog_generator = Situation_Recognition()

        self.yolo_lane = False
        self.yolo_object = False
        self.result = []
        self.seg_result = [[None]]
        self.obj_result = [[None]]
        self.fps = 0.0

    def run(self):
        while self.conn is None:
            QThread.msleep(10)
        self.cam_server.conn = self.conn

        frame_cnt = 0
        start_time = time.time()
        while self.running == True:
            self.source = self.cam_server.show_video()
            
            if self.source is not None:
                if self.yolo_lane and self.yolo_object:
                    self.image, self.seg_result = self.seg_generator.get_road_center(self.source.copy())
                    self.obj_result = self.object_generator.calculate_depth(self.source.copy())
                    self.check_situation()
                else:
                    if self.yolo_lane :
                        self.image, self.seg_result = self.seg_generator.get_road_center(self.source.copy())
                        self.obj_result = [[None]]
                    elif self.yolo_object :
                        self.obj_result = self.object_generator.calculate_depth(self.source.copy())
                        self.check_situation()
                        self.seg_result = [[None]]
                        self.image = self.source.copy()
                    else:
                        self.image = self.source.copy()
                        self.seg_result = [[None]]
                        self.obj_result = [[None]]

                try:
                    self.result = [self.seg_result, self.obj_result]
                    image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                    self.update.emit(image, self.result)
                except Exception as e:
                    # print(e)
                    self.result = [[[]],[[]]]
                    self.update.emit(self.source, self.result)
                    pass

            frame_cnt += 1
            if frame_cnt >= 10:
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.fps = frame_cnt / elapsed_time
                start_time = time.time()
                frame_cnt = 0
                
            if self.yolo_lane and self.yolo_object:
                QThread.msleep(2)
            elif self.yolo_lane or self.yolo_object:
                QThread.msleep(3)
            else:
                QThread.msleep(8)

    def check_situation(self):
        obj_result = self.recog_generator.only_name_distance(self.obj_result)
        objects_status = self.recog_generator.recognition(obj_result)
        description = self.recog_generator.find_scenario(objects_status)

        if description != self.previous_result:
            print(description)
            self.previous_result = description

    def stop(self):
        self.running = False