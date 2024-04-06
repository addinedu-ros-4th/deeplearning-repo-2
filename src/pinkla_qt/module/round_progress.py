import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QPen, QFontMetrics, QFont, QColor
from PyQt5.QtCore import Qt, QRectF

class roundProgressBar(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)

        self.progress = 0

    def setValue(self, value):
        self.progress = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height())
        progress_rect = QRectF(20, 20, size-30, size-30)

        pen = QPen(Qt.gray, 12)
        painter.setPen(pen)
        painter.drawArc(progress_rect, -120 * 16, -250 * 16)

        pen.setColor(Qt.blue)
        painter.setPen(pen)
        painter.drawArc(progress_rect, -120 * 16, int(-250 * self.progress / 10 * 20))
        
        font = QFont()
        font.setPointSize(22)  
        font.setBold(True)     
        painter.setFont(font)

        pen.setColor(Qt.black)  
        painter.setPen(pen)
        

        font_metrics = QFontMetrics(font)
        text_width = font_metrics.width(str(self.progress))
        text_height = font_metrics.height()
        painter.drawText(int(progress_rect.center().x())-60,
                         int(progress_rect.center().y())+10,
                         str(f"{self.progress:.2f}cm/s"))