from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import sys

# Import your main window class here
from gui import *
import netifaces
import subprocess

ui_path = "./login.ui"
from_class = uic.loadUiType(ui_path)[0]

class LoginDialog(QDialog, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Pinkla.b Login')
        
        center_ui(self)
        self.server_ip = "0.0.0.0"
        self.client_ip = "192.168.0.100"
        self.port1 = 8485
        self.port2 = 8584
        self.port3 = 8090

        self.get_ip_address()
        self.default_init()

    def default_init(self):
        self.text_server.setText(self.server_ip)
        self.port_1.setText(str(self.port1))
        self.port_2.setText(str(self.port2))
        self.port_3.setText(str(self.port3))
        
        self.radio_remote.clicked.connect(self.remote_select)
        self.radio_local.clicked.connect(self.local_select)

        self.radio_remote.setChecked(True)
        self.remote_select()

        self.btn_start.clicked.connect(self.start_pinkla)

    def remote_select(self):
        client_ip = self.client_ip
        self.text_client.setText(client_ip)

    def local_select(self):
        client_ip = self.server_ip
        self.text_client.setText(client_ip)

    def get_ip_address(self):
        interfaces = netifaces.interfaces()
        add = netifaces.ifaddresses('wlo1') # wifi
        self.server_ip = add[netifaces.AF_INET][0]['addr']

    def start_pinkla(self):
        server_ip = self.text_server.toPlainText()
        client_ip = self.text_client.toPlainText()

        port1 = self.port_1.toPlainText()
        port2 = self.port_2.toPlainText()
        port3 = self.port_3.toPlainText()
        # print(server_ip,client_ip, port1,port2,port3)

        status_server = self.validate_login(server_ip)
        status_client = self.validate_login(client_ip)
        # print(status_server, status_client)

        if status_server and status_client:
            QMessageBox.information(self, "Login Status", "    Pinkla.b\nWELCOME    ")
            self.accept()
            self.open_main_window(server_ip, client_ip, port1, port2, port3)
            # sys.exit()
        else:
            QMessageBox.warning(self, "Login Status", "    Pinkla.b\nFAILED START    ")

    def validate_login(self, ip):
        result = subprocess.run(['ping', '-c', '1', '-W','0.1',ip], capture_output=True, text=True)
        if result.returncode == 0:
            return True 
        else:
            return False

    def open_main_window(self, server_ip, client_ip, port1, port2, port3):
        # Create and open the main window
        self.main_window = WindowClass(server_ip, client_ip, port1, port2, port3)
        self.main_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        print("Login Success")
        sys.exit(app.exec_())
    else:
        sys.exit()