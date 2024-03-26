import socket
import cv2
import numpy as np
import serial
from datetime import datetime

cmtx = np.array([[474.9308089, 0, 313.10372736],
                [0, 474.24684641, 254.94399015],
                [0,           0,            1]])
dist = np.array([[0.0268074362, -0.178310961, -0.000144841081, -0.00103575477, 0.183767484]])

class SERVER():
    def __init__(self, host='0.0.0.0', port=0000):
        self.s = None
        self.host = host
        self.port = port
        self.conn, self.addr = None, None
        self.writer = None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.host, self.port))
            self.s.listen(2)

        except Exception as e:
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
            # print(e)
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