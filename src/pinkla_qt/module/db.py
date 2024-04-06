from pinkla_qt.module.common import *
import pyqtgraph as pg

class logClass(QDialog):
    def __init__(self, WindowClass):
        super().__init__()
        self.ui = uic.loadUi("./db.ui", self)
        self.main_window = WindowClass
        self.show()
        self.log_in(WindowClass)
        
        
    def set_window(self):
        table_name = self.mysql.get_table_info()
        for name in table_name:
            if name == "object_class":
                pass
            else:
                self.tableList.addItem(name)
                
        self.startTime.setDisplayFormat("yyyyMMdd_hhmmss")
        self.endTime.setDisplayFormat("yyyyMMdd_hhmmss")
        self.startTime.hide()
        self.startDate.hide()
        self.label_2.hide()
        self.endTime.hide()
        self.endDate.hide()
        self.label_3.hide()
        self.plotButton.hide()
                
    def log_in(self, class_instance):
        self.info = class_instance.mysql_info
        self.mysql = pinkla_mysql(self.info)
        self.tableList.addItem(" ")
        self.set_window()
        self.init_plot()
        
        self.tableList.currentIndexChanged.connect(self.select_table)
        self.plotButton.clicked.connect(self.plot_graph)
    
    def init_plot(self):
        self.borderPlot = pg.PlotWidget()
        self.middlePlot = pg.PlotWidget()
        self.interPlot = pg.PlotWidget()
        self.targetPlot = pg.PlotWidget()
        
        self.leftPlotLayout.addWidget(self.borderPlot)
        self.leftPlotLayout.addWidget(self.interPlot)
        
        self.rightPlotLayout.addWidget(self.middlePlot)
        self.rightPlotLayout.addWidget(self.targetPlot)
    
    
    def select_table(self):
        self.current_select = self.tableList.currentText()
        
        self.set_time_range(self.current_select)
        
        self.startTime.show()
        self.startDate.show()
        self.endTime.show()
        self.endDate.show()
        self.label_2.show()
        self.label_3.show()
        self.plotButton.show()
    
    
    def setting_time(self):
        start_date = self.startDate.date()
        start_time = self.startTime.time()
        end_date = self.endDate.date()
        end_time = self.endTime.dateTime()
        
        start_date = start_date.toString("yyyyMMdd")
        start_time = start_time.toString("hhmmss")
        end_date = end_date.toString("yyyyMMdd")
        end_time = end_time.toString("hhmmss")
        
        start = start_date + "_" + start_time
        end = end_date + "_" + end_time
                
        
        self.table = self.mysql.select_data(self.current_select, start, end)
        rows, cols = self.table.shape
        
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(cols)
        self.tableWidget.setHorizontalHeaderLabels(self.table.columns)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(self.table.iloc[i, j]))
                self.tableWidget.setItem(i, j, item)
                
        self.numberOfData.setText(str(rows))    
    
    
    def plot_graph(self):
        self.setting_time()
        
        x, y = [], []
        
        self.borderPlot.clear()
        self.interPlot.clear()
        self.middlePlot.clear()
        self.targetPlot.clear()
        
        data_columns = ["border_line_centroid", "middle_line_centroid", "intersection_line_centroid", "target_point"]
        for col in data_columns:
            
            for point_str in self.table[col]:
                if point_str[-1] != "]":
                    point_str +="]"
                if point_str[0] == "(":
                    point_str = point_str.replace("(", "[")
                    point_str = point_str.replace(")", "")
                if point_str[-1] == ")":
                    point_str = point_str.replace(")", "")

                coord = eval(point_str)
                x.append(coord[0])
                try:
                    y.append(coord[1])
                except Exception as e:
                    y.append(0)
                            

            if col == "border_line_centroid":
                self.borderPlot.plot(x = None, y = x, pen = 'r', name = "x")
                self.borderPlot.plot(x = None, y = y, pen = "b", name = "y")
                self.borderPlot.setTitle("Border Line Centroid")
                self.borderPlot.setXRange(0, len(x))
                self.borderPlot.addLegend(anchor = (1,1))
                
            elif col == "middle_line_centroid":
                self.middlePlot.plot(x = None, y = x, pen = 'r', name = "x")
                self.middlePlot.plot(x = None, y = y, pen = 'b', name = "y")
                self.middlePlot.setTitle("middel Line Centroid")
                self.middlePlot.setXRange(0, len(x))
                self.middlePlot.addLegend(anchor = (1,1))
                
            elif col == "intersection_line_centroid":
                self.interPlot.plot(x = None, y = x, pen = 'r', name = "x")
                self.interPlot.plot(x = None, y = y, pen = 'b', name = "y")
                self.interPlot.setTitle("intersection Line Centroid")
                self.interPlot.setXRange(0, len(x))
                self.interPlot.addLegend(anchor = (1,1))
                

            elif col == "target_point":
                self.targetPlot.plot(x = None, y = x, pen = 'r', name = "x")
                self.targetPlot.plot(x = None, y = y, pen = 'b', name = "y")
                self.targetPlot.setTitle("target Point")
                self.targetPlot.setXRange(0, len(x))
                self.targetPlot.addLegend(anchor = (1,1))
            else: 
                pass
            
            x, y = [], []
            
    def set_time_range(self, table_name):
        
        time_range = self.mysql.get_time_range(table_name)
        start = time_range[0][0]
        end = time_range[-1][0]
        
        start_date = start[:8]
        start_time = start[9:]
        end_date = end[:8]
        end_time = end[9:]
        print(start_date, start_time)
        
        start_date = QDate.fromString(start_date, "yyyyMMdd")
        start_time = QTime.fromString(start_time, "hhmmss")
        end_date = QDate.fromString(end_date, "yyyyMMdd")
        end_time = QTime.fromString(end_time, "hhmmss")

        self.startDate.setDisplayFormat("yyyy-MM-dd")
        self.startTime.setDisplayFormat("hh:mm:ss")
        self.endDate.setDisplayFormat("yyyy-MM-dd")
        self.endTime.setDisplayFormat("hh:mm:ss")
        
        self.startDate.setDate(start_date)
        self.startTime.setTime(start_time)
        self.endDate.setDate(end_date)
        self.endTime.setTime(end_time)
        
        self.startDate.setCalendarPopup(True)
        self.startTime.setCalendarPopup(True)
        self.endDate.setCalendarPopup(True)
        self.endTime.setCalendarPopup(True)
        
        
        
    def closeEvent(self, event):
        if self.mysql:
            self.mysql.close_mysql() 
        event.accept()