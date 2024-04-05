from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *


import sys, os
import pandas as pd
import cv2, imutils
import socket
import numpy as np
import serial

import time
# import datetime
from datetime import datetime
import psutil
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir + "/..")

from pinkla_database.pinkla_db import *
from pinkla_lane.lane_detection import *
from pinkla_object.predict_distance import *



cmtx1 = np.array([[474.9308089, 0., 313.10372736],
                  [0., 474.24684641, 254.94399015],
                  [0.,0.,1.]])
dist1 = np.array([[0.0268074362, -0.178310961, -0.000144841081, -0.00103575477, 0.183767484]])

cmtx2 = np.array([[470.86256773, 0., 322.79554974],
                  [0., 470.89842857, 236.76274254],
                  [0.,0.,1.]])
dist2 = np.array([[0.00727918, -0.09059939, -0.00224102, -0.00040328, 0.06114216]])

def center_ui(object):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - object.width()) // 2
        y = (screen_geometry.height() - object.height()) // 2
        object.move(x, y)
