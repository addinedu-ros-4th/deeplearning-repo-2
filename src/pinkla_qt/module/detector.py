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

        self.object_generator = Find_Object()
        self.seg_generator = Find_Road_Center()

        self.yolo_lane = False
        self.yolo_object = False
        self.result = []
        self.seg_result = [None]
        self.obj_result = [None]

    def run(self):
        while self.conn is None:
            QThread.msleep(10)
        self.cam_server.conn = self.conn

        while self.running == True:
            self.source = self.cam_server.show_video()
            
            if self.source is not None:
                if self.yolo_lane :
                    self.image, self.seg_result = self.seg_generator.get_road_center(self.source.copy())
                    self.obj_result = [None]
                elif self.yolo_object :
                    self.image = self.object_generator.calculate_depth(self.source.copy())
                    self.seg_result = [None]
                    self.obj_result = [None]
                else:
                    self.image = self.source.copy()
                    self.seg_result = [None]
                    self.obj_result = [None]

                try:
                    self.result = [self.seg_result, self.obj_result]
                    image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                    self.update.emit(image, self.result)
                except Exception as e:
                    # print(e)
                    pass
            QThread.msleep(8)

    def stop(self):
        self.running = False