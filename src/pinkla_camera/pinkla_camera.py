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
        connected = False
        while not connected:
            try:
                s.connect((self.server_address, self.port))
                connected = True
                print("Connected to server")
            except ConnectionRefusedError:
                print("Waiting for server...")
                time.sleep(1)
        return s

    def send_video_data(self):
        self.socket = self.connect_to_server()

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
                    print("Failed to capture frame from camera.")
                    break
            except Exception as e:
                self.socket = self.connect_to_server()

        cam.release()
        self.socket.close()
        print("release and close ")

def main():
    server_address = '192.168.0.100'
    port1 = 8485
    port2 = 8584

    # Check the number of arguments
    if len(sys.argv) == 2:
        # Only one argument, run a single thread for the specified camera index
        cam_index = int(sys.argv[1])
        camera = CameraStreamer(server_address, port1, cam_index)
        thread = threading.Thread(target=camera.send_video_data)
        thread.start()
        thread.join()
    elif len(sys.argv) == 3:
        # Two arguments, run threads for both camera indices
        cam_indices = [int(arg) for arg in sys.argv[1:]]
        camera1 = CameraStreamer(server_address, port1, cam_indices[0])
        camera2 = CameraStreamer(server_address, port2, cam_indices[1])
        thread1 = threading.Thread(target=camera1.send_video_data)
        thread2 = threading.Thread(target=camera2.send_video_data)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
    else:
        print("Usage: python3 camera_stream.py <cam_index1> [<cam_index2>]")
        sys.exit(1)

if __name__ == "__main__":
    main()
