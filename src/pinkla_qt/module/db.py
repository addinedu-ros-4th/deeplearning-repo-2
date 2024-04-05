from pinkla_qt.module.common import *

class logClass(QDialog):
    def __init__(self, WindowClass):
        super().__init__()
        self.ui = uic.loadUi("./db.ui", self)
        self.main_window = WindowClass
        self.show()
        self.log_in(WindowClass)
        
        
    def set_window(self):
        table_name = self.mysql.get_table_name()
        for name in table_name:
            if name == "object_class":
                pass
            else:
                self.tableList.addItem(name)
                
    def log_in(self, class_instance):
        self.info = class_instance.mysql_info
        self.mysql = pinkla_mysql(self.info)
        self.tableList.addItem(" ")
        self.set_window()
        
        self.tableList.currentIndexChanged.connect(self.select_table)
            
    def select_table(self):
        current_select = self.tableList.currentText()
        table = self.mysql.select_data(current_select)
        rows, cols = table.shape
        
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(cols)
        self.tableWidget.setHorizontalHeaderLabels(table.columns)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(table.iloc[i, j]))
                self.tableWidget.setItem(i, j, item)
        
        
    def closeEvent(self, event):
        if self.mysql:
            self.mysql.close_mysql() 
        event.accept()