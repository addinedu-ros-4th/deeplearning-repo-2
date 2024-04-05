from pinkla_qt.module.common import *


class Control_Pinkla(QThread):
    update = pyqtSignal(bool)

    def __init__(self, s=None):
        super().__init__()
        self.s = s
        self.running = True
        self.cmd = [0, 100, 5, 0, 0, 0, 0]

    def run(self):
        while self.running:
            try:
                data_str = ','.join(map(str, self.cmd))
                self.s.sendall(data_str.encode())

                self.update.emit(True)
                QThread.msleep(30)
            except Exception as e :
                print("Control_Pinkla: ",e)
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
    	# cut_off_freqency: 차단 주파수
        # ts: 주기
        
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
        self.r = 0.025
        # self.b = 0.11
        self.b = 0.08

        self.img_width = 640
        self.img_height = 480

        self.cam_height = 0.08
        self.cam_shift = 0.06
        self.hor_ang = math.radians(1)
        self.ver_ang = math.radians(-18)
        self.hor_pixel_per_deg = self.img_width / math.degrees(self.hor_ang)
        self.ver_pixel_per_deg = self.img_height / math.degrees(self.ver_ang)

        self.angle = 0.0
        self.hor_dist = 0
        self.ver_dist = 0
        self.dist = 0
        self.cen_x, self.cen_y = 0., 0.
        self.x, self.y = 0., 0.
        self.seg_center_border = (0,0)
        self.rate = 10
        self.w1, self.w2, self.w3, self.w4 = 0.0, 0.0, 0.0, 0.0

        self.lpf_x = LowPassFilter(5.0, 1)
        self.lpf_y = LowPassFilter(5.0, 1)
        self.lpf_dx = LowPassFilter(3.0, 1)
        self.lpf_dy = LowPassFilter(3.0, 1)

        self.param_x = 3.2
        self.param_y1 = 1.54
        self.param_y2 = 2.7
        self.param_z = 11.1
        self.loop = False

    def cal(self):
        self.w1 = (1/self.r) * (self.lx-self.ly-self.b*self.az)
        self.w2 = (1/self.r) * (self.lx+self.ly-self.b*self.az)
        self.w3 = (1/self.r) * (self.lx-self.ly+self.b*self.az)
        self.w4 = (1/self.r) * (self.lx+self.ly+self.b*self.az)
        # value = [self.w1, self.w2, self.w3, self.w4]
        value = [self.w4, self.w3, self.w2, self.w1]
        return value

    def move_to_lane_center(self, seg_result):
        # print(seg_result)
        line_center_x = seg_result[0]
        line_center_y = seg_result[1]
        self.seg_center_border = seg_result[2]
        cnt_stop = seg_result[3]

        self.x = self.lpf_x.filter(line_center_x)
        self.y = self.lpf_y.filter(line_center_y)

        self.cen_x = (self.x + self.seg_center_border[0]) / 2
        self.cen_y = (self.y + self.seg_center_border[1]) / 2

        # target_pos - robot_pos
        delta_x_t = (self.img_width/2) - self.cen_x
        delta_y_t = (self.img_height) - self.cen_y

        delta_x = self.lpf_dx.filter(delta_x_t)
        delta_y = self.lpf_dy.filter(delta_y_t)
        self.angle = np.arctan2(delta_x, delta_y)

        # target_pos = np.array([int(cen_x), int(cen_y)])
        # robot_pos = np.array([self.img_center_x, int(self.roi_rect_end[1])])
        # distance = np.sqrt(delta_x**2 + delta_y**2)

        # robot_pos = np.array([self.img_center_x, int(self.roi_rect_end[1] - 50)])
        # distance = np.linalg.norm(robot_pos - target_pos)
        # test_x = robot_pos[0] - distance * np.sin(angle)
        # test_y = robot_pos[1] - distance * np.cos(angle)

        self.hor_dist = delta_x / 10 * -1
        self.ver_dist = (delta_y / self.ver_pixel_per_deg)  + (self.cam_shift * 100 * -1)
        self.angle2 = np.arctan2(self.hor_dist, self.ver_dist)
        # print(self.angle, self.angle2)

        self.dist = math.sqrt(self.hor_dist**2 + self.ver_dist**2 + self.cam_height **2)

        mx = abs(self.ver_dist / self.rate) * self.param_x
        my = abs(self.hor_dist / self.rate / self.param_y1) * self.param_y2
            
        vx = (self.ver_dist / (abs(self.ver_dist) + abs(self.hor_dist)) * mx) * -1
        vy = (self.hor_dist / (abs(self.ver_dist) + abs(self.hor_dist)) * my) * -1
        vz = self.angle * self.param_z

        self.r = 0.025
        self.b = 0.11

        if cnt_stop > 20:
            self.lx = 0.
            self.ly = 0.
            self.dist = 0.
            if self.loop :
                self.az = 25.
            else:
                self.az = 0.
        else:
            self.lx = vx
            self.ly = vy
            self.az = vz

        velo = self.cal()
        # print(velo)
        return velo

    def print_vels(self, linear_x_velocity, linear_y_velocity, angular_velocity):
        print('linear x velocity {0:.3} | linear y velocity {1:.3} | angular velocity {2:.3}'.format(
            linear_x_velocity, linear_y_velocity, angular_velocity))


class KeyboardTeleopController(object):
    def __init__(self, cal_cmd, sender):
        self.LIN_VEL_STEP_SIZE = 0.2
        self.ANG_VEL_STEP_SIZE = 2.5
        self.cal_cmd = cal_cmd
        self.sender = sender

    def press_key_control(self, event):
        value = [0,0,0,0]
        shift_flag = False

        if event.key() == Qt.Key_W:
            self.cal_cmd.ly = 0.0

            if self.cal_cmd.az != 0.0:
                self.cal_cmd.az = 0.0

            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = 2.0
            elif self.cal_cmd.lx >= 5.0:
                self.cal_cmd.lx = 5.0
            else:
                self.cal_cmd.lx += self.LIN_VEL_STEP_SIZE

        elif event.key() == Qt.Key_X:
            self.cal_cmd.ly = 0.0

            if self.cal_cmd.az != 0.0:
                self.cal_cmd.az = 0.0

            if self.cal_cmd.lx == 0.0:
                self.cal_cmd.lx = -2.0
            elif self.cal_cmd.lx <= -5.0:
                self.cal_cmd.lx = -5.0
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

        try:
            self.sender.cmd = [1, 100, 5, int(value[0]), int(value[1]), int(value[2]), int(value[3])]
        except Exception as e:
            print("KeyboardTeleopController: ", e)
            pass