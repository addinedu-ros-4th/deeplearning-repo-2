from pinkla_qt.module.common import *

class Socket_Camera(QThread):
    update = pyqtSignal(object)

    def __init__(self, host, port):
        super().__init__()
        self.running = True
        self.host = host
        self.port = port
        self.conn, self.addr = None, None
        self.server = CAMERA_SERVER(self.host, self.port)

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


class CAMERA_SERVER():
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
            # cmtx = cmtx1
            # dist = dist1
            cmtx = cmtx2
            dist = dist2
            cam = "Lane"
        else:
            cmtx = cmtx1
            dist = dist1
            # cmtx = cmtx2
            # dist = dist2
            cam = "Follow"

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
