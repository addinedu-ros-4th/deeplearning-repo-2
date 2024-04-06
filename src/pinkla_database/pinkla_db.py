import mysql.connector
import pandas as pd

class pinkla_mysql():
    def __init__(self, info):
        self.df = None
        self.info = info
        self.connect_to_database()
        self.cur.execute("USE pinkla_base")
        self.remote.commit()
        
        
    def connect_to_database(self):
        self.remote = mysql.connector.connect(
            host=self.info[0],
            user=self.info[1],
            password=self.info[2]
        )
        self.cur = self.remote.cursor(buffered=True)


    def init_db(self):
        self.create_database()
        self.init_tables()
        
        
    def create_database(self):
        create_db_query = "CREATE DATABASE IF NOT EXISTS pinkla_base"
        self.cur.execute(create_db_query)
        self.remote.commit()
        
        
    def init_tables(self):
        
        self.create_action_table()
        self.create_lane_table()
        self.create_object_table()
        self.create_vehicle_table()
        self.create_class_table()
        # self.save_object_class()
        
    
    
    def create_action_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_action \
                            (time DATETIME PRIMARY KEY, \
                            action VARCHAR(16) NOT NULL, \
                            drive_LED BOOL NOT NULL, \
                            L_LED BOOL NOT NULL, \
                            R_LED BOOL NOT NULL, \
                            break_LED BOOL NOT NULL, \
                            buzzer BOOL NOT NULL)"
        self.cur.execute(create_query)
        self.remote.commit()


    def create_lane_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_lane \
                            (time varchar(32) PRIMARY KEY, \
                            border_line INT NOT NULL, \
                            border_line_centroid VARCHAR(16) NOT NULL, \
                            intersection_line INT NOT NULL, \
                            intersection_line_centroid VARCHAR(16) NOT NULL, \
                            middle_line INT NOT NULL, \
                            middle_line_centroid VARCHAR(16) NOT NULL, \
                            target_point VARCHAR(16) NOT NULL)"
        self.cur.execute(create_query)
        self.remote.commit()


    def create_object_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_object \
                        (time DATETIME PRIMARY KEY, \
                        action VARCHAR(16) NOT NULL, \
                        object_list INT NOT NULL, \
                        object_distance FLOAT NOT NULL, \
                        detected_image BLOB NOT NULL)"
        self.cur.execute(create_query)
        self.remote.commit()


    def create_vehicle_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_vehicle \
                        (target_point VARCHAR(16), \
                        linear_x FLOAT NOT NULL, \
                        angular_z FLOAT NOT NULL)"
        self.cur.execute(create_query)
        self.remote.commit()


    def create_class_table(self):
        check_query = "DROP TABLE IF EXISTS object_class"
        self.cur.execute(check_query)

        create_query = "CREATE TABLE IF NOT EXISTS object_class \
                        (object_list INT PRIMARY KEY, \
                        object_classes VARCHAR(16) NOT NULL)"
        self.cur.execute(create_query)
        self.remote.commit()
        
        
        
    def get_table_info(self):
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'pinkla_base'"
        self.cur.execute(query)
        table_info = [row[0] for row in self.cur.fetchall()]
        
        return table_info
    
    
    def get_time_range(self, table_name):
        query = f"SELECT DISTINCT SUBSTRING(time, 1, 15) AS unique_value FROM {table_name};"
        self.cur.execute(query)
        time_range = self.cur.fetchall()
        
        return time_range
        
        
        
    def save_action_data(self, action_data):
        save_query = f"INSERT INTO pinkla_action (time, drive_LED, action, L_LED, R_LED, break_LED, buzzer) \
                        VALUES ('{action_data[0]}', '{action_data[1]}', '{action_data[2]}', '{action_data[3]}', \
                        '{action_data[4]}', '{action_data[5]}', '{action_data[6]}')"
        self.cur.execute(save_query)
        self.remote.commit()

    def save_lane_data(self, lane_data):
        save_query = f"INSERT INTO pinkla_lane (time, border_line, border_line_centroid, intersection_line, \
                            intersection_line_centroid, middle_line, middle_line_centroid, target_point) \
                        VALUES ('{lane_data[0]}', '{lane_data[1]}', '{lane_data[2]}', '{lane_data[3]}', \
                            '{lane_data[4]}', '{lane_data[5]}', '{lane_data[6]}', '{lane_data[7]}')"
        self.cur.execute(save_query)
        self.remote.commit()

    def save_object_data(self, object_data):
        save_query = f"INSERT INTO pinkla_object (time, action, object_list, object_distance, detected_image) \
                        VALUES ('{object_data[0]}', '{object_data[1]}', '{object_data[2]}', \
                            '{object_data[3]}', '{object_data[4]}')"
        self.cur.execute(save_query)
        self.remote.commit()

    def save_vehicle_data(self, vehicle_data):
        save_query = f"INSERT INTO pinkla_vehicle (target_point, linear_x, angular_z) \
                        VALUES ('{vehicle_data[0]}', '{vehicle_data[1]}', '{vehicle_data[2]}')"
        self.cur.execute(save_query)
        self.remote.commit()

    def save_object_class(self, object_list):
        for i in object_list:
            save_query = f"INSERT INTO object_class (object_list, object_classes) \
                            VALUES ('{i[0]}', '{i[1]}')"
            self.cur.execute(save_query)
        self.remote.commit()
        
    
    def select_data(self, table_name, start_time, end_time):
        if table_name == "pinkla_action":
            self.get_action_data()
        elif table_name == "pinkla_lane":
            self.get_lane_data(start_time, end_time)
        elif table_name == "pinkla_object":
            self.get_object_data()
        elif table_name == "pinkla_vehicle":
            self.get_vehicle_data()
        else:
            self.df = None
            
        return self.df
        
    
    def get_action_data(self):
        self.cur.execute("select * from pinkla_action")
        result = self.cur.fetchall()
        self.df =  pd.DataFrame(result, columns = ["time", "drive_LED", "action", "L_LED", "R_LED", "break_LED", "buzzer"])
    
    
    def get_lane_data(self, start_time, end_time):
        self.cur.execute("SELECT * FROM pinkla_lane WHERE time BETWEEN %s AND %s", (start_time, end_time))
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time", "border_line", "border_line_centroid", "intersection_line",
                                                  "intersection_line_centroid", "middle_line", "middle_line_centroid", "target_point"])
        
    
    def get_object_data(self):
        self.cur.execute("select time, action, object_list, object_distance from pinkla_object")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time", "action", "object_list", "object_distance"])
    
     
    def get_vehicle_data(self):
        self.cur.execute("select * from pinkla_vehicle")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["target_point", "linear_x", "angular_z"])
    
    
    
    def close_mysql(self):
        try:
            self.cur.close()
            self.remote.close()
            return True
        except Exception as e:
            return False