import cv2
import socket
import numpy as np
import time
import threading
import sys

class CameraStreamer:
    def __init__(self, server_address, port, cam_index=0, width=640, height=480, quality=100):
        self.server_address = server_address
        self.port = port
        self.cam_index = cam_index
        self.width = width
        self.height = height
        self.quality = quality
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        self.socket = None

    def connect_to_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not connected:
            try:
                s.connect((self.server_address, self.port))
                connected = True
            except ConnectionRefusedError:
                time.sleep(1)
        return s

    def send_video_data(self):

        cam = cv2.VideoCapture(self.cam_index)
        cam.set(3, self.width)
        cam.set(4, self.height)

        while True:
            try:
                ret, frame = cam.read() 
                if ret:
                    result, frame = cv2.imencode('.jpg', frame, self.encode_param) 
                    data = np.array(frame)
                    stringData = data.tostring()
                    self.socket.sendall((str(len(stringData))).encode().ljust(16) + stringData)
                else:
                    break
            except Exception as e:
                pass

        cam.release()
        self.socket.close()

def main():
    server_address = ''
    port1 = 8485
    port2 = 8584

    if len(sys.argv) == 2:
        cam_index = int(sys.argv[1])
        camera1 = CameraStreamer(server_address, port1, cam_index)
        thread1 = threading.Thread(target=camera1.send_video_data)
        thread1.start()
        thread1.join()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
