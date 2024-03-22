import socket
import cv2
import numpy as np
from datetime import datetime

HOST = '192.168.0.23'
PORT = 8485
cmtx = np.array([[474.9308089, 0, 313.10372736],
                [0, 474.24684641, 254.94399015],
                [0,           0,            1]])
dist = np.array([[0.0268074362, -0.178310961, -0.000144841081, -0.00103575477, 0.183767484]])

def undistorted_frame(frame):
    undist = cv2.undistort(frame, cmtx, dist)
    return undist

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf
 
def record_video(conn, width=640, height=480, fps=30):
    recording = False
    out = None

    while True:
        length = recvall(conn, 16)
        stringData = recvall(conn, int(length))
        data = np.fromstring(stringData, dtype = 'uint8')
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

        undist = undistorted_frame(frame)
        cv2.imshow('ImageWindow',undist)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):  # 'r' 키 누르면 녹화 시작
            recording = True
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f'../../data/{current_time}.avi'
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
            print(f"record start : {current_time}.avi")

        elif key == ord('s'):  # 's' 키 누르면 녹화 종료
            recording = False
            out.release()
            print("record stop")
            
        elif key == ord('q'):  # 'q' 키 누르면 종료
            break

        if recording == True:
            out.write(undist)
        
    conn.close()
    cv2.destroyAllWindows()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')
    s.bind((HOST, PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn, addr = s.accept()
    record_video(conn)

def test():
    print("hi")

if __name__ == "__main__":
    main()
