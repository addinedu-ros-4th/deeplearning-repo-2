# -*- coding: utf8 -*-
import cv2
import socket
import numpy as np
import time

def connect_to_server(server_address, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    while not connected:
        try:
            s.connect((server_address, port))
            connected = True
            print("Connected to server")
        except ConnectionRefusedError:
            print("Waiting for server...")
            time.sleep(1)
    return s

def send_video_data(cam_index=0, width=640, height=480, quality=90):
    global server_address, port, s
    cam = cv2.VideoCapture(cam_index)
    cam.set(3, width)
    cam.set(4, height)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

    while True:
        try:
            ret, frame = cam.read() 
            if ret:
                result, frame = cv2.imencode('.jpg', frame, encode_param) 
                data = np.array(frame)
                stringData = data.tostring()
                s.sendall((str(len(stringData))).encode().ljust(16) + stringData)
            else:
                print("Failed to capture frame from camera.")
                break
    #    except ConnectionRefusedError:
    #        print("Connection to server refused. Retrying...")
    #        s = connect_to_server(server_address, port)
    #    except ConnectionResetError:
    #        print("Connection reset by peer. Retrying...")
    #        s = connect_to_server(server_address, port)
        except Exception as e:
            s = connect_to_server(server_address, port)

    cam.release()
    s.close()
    print("release and close ")


if __name__ == "__main__":
    server_address = '192.168.0.23'
    port = 8485

    s = connect_to_server(server_address, port)
    if s is not None:
        print("connected")
        while True:
            try:
                send_video_data(0, 640, 480, 100)
            except Exception as e:
#                print("main e: ",e)
#                s = connect_to_server(server_address, port)
                pass
