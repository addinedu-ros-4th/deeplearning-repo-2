import socket
import cv2
import numpy as np
from datetime import datetime

cmtx = np.array([[474.9308089, 0, 313.10372736],
                [0, 474.24684641, 254.94399015],
                [0,           0,            1]])
dist = np.array([[0.0268074362, -0.178310961, -0.000144841081, -0.00103575477, 0.183767484]])

class CAM_SERVER():
    def __init__(self, host='192.168.0.23', port=8485):
        self.s = None
        self.host = host
        self.port = port
        self.conn, self.addr = None, None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('Socket created')
            self.s.bind((self.host, self.port))
            print('Socket bind complete')
            self.s.listen(2)
            print('Socket now listening')
            # conn, addr = self.s.accept()
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
            return None

    def record_video(self, conn, width=640, height=480, fps=30):
        recording = False
        out = None

        while True:
            length = self.recvall(conn, 16)
            stringData = self.recvall(conn, int(length))
            data = np.fromstring(stringData, dtype = 'uint8')
            frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

            undist = self.undistorted_frame(frame)
            cv2.imshow('ImageWindow',undist)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):  # 'r' 키를 누르면 녹화 시작
                recording = True
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = f'../../data/{current_time}.mp4'
                fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))

            elif key == ord('s'):  # 's' 키를 누르면 녹화 종료
                recording = False
                out.release()
                
            elif key == ord('q'):  # 'q' 키를 누르면 종료
                break

            if recording == True:
                out.write(undist)
            
        conn.close()
        cv2.destroyAllWindows()  # 창 닫기

    def test(self):
        print("Hello, It's Camera.")