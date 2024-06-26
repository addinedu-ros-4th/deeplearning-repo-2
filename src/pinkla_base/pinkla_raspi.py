import socket
import serial
import time

HOST = ""
PORT = 8090
port = ''
baud = 9600


def get_socket_send_serial(conn, ser):
    while True:
        try:
            received_data = conn.recv(1024).decode()
            if received_data:
                data_list = received_data.split(',')
                data_list = [int(data) for data in data_list]
                if data_list:
                    data_list.append('\n')
                    data_str = ','.join(map(str, data_list))
                    ser.write(data_str.encode())
                else:
                    raise ValueError
            else:
                raise ValueError

        except Exception as e:
            data_list = [0, 0, 5, 0, 0, 0, 0,'\n']
            data_str = ','.join(map(str, data_list))
            ser.write(data_str.encode())

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(10)
    conn, addr = s.accept()
    return conn

def main():
    global s
    conn = connect()
    ser = serial.Serial(port, baud)

    if conn is not None and ser is not None:
        while True:
            try:
                get_socket_send_serial(conn, ser)
            except Exception as e:
                pass
            finally:
                pass

    ser.close()
    conn.close()
    s.close()


if __name__ == "__main__":
    main()
