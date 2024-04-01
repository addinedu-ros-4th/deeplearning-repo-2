import mysql.connector
import pandas as pd

class pinkla_mysql():
    def __init__(self, info):
        self.df = pd.DataFrame()
        self.info = info
        self.connect_to_database()
        
    def connect_to_database(self):
        self.remote = mysql.connector.connect(
            host=self.info[0],
            user=self.info[1],
            password=self.info[2]
        )
        self.cur = self.remote.cursor(buffered=True)
        
    def init_db(self):
        self.connect_to_database()
        self.create_database()
        self.init_tables()
        self.remote.close()
        
    def create_database(self):
        create_db_query = "CREATE DATABASE IF NOT EXISTS pinkla_base"
        self.cur.execute(create_db_query)
        self.remote.commit()
        
        
    def init_tables(self):
        self.cur.execute("USE pinkla_base")
        self.create_lane_table()
        self.create_vehicle_table()
        self.create_object_table()
        self.create_event_table()
        
    def create_lane_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_lane (time DATETIME PRIMARY KEY, lane_class VARCHAR(32), number_of_lane INT)"
        self.cur.execute(create_query)
        self.remote.commit()
        
    def create_vehicle_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_vehicle (time DATETIME PRIMARY KEY, vehicle_status VARCHAR(32), linear_x FLOAT, angular_z FLOAT)"
        self.cur.execute(create_query)
        self.remote.commit()
        
    def create_object_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_object (time DATETIME PRIMARY KEY, object_class VARCHAR(32), number_of_object INT)"
        self.cur.execute(create_query)
        self.remote.commit()
        
    def create_event_table(self):
        create_query = "CREATE TABLE IF NOT EXISTS pinkla_event (time DATETIME PRIMARY KEY, event_class VARCHAR(32))"
        self.cur.execute(create_query)
        self.remote.commit()
        
    
    def save_lane_data(self, lane_data):
        self.cur.execute(f"insert into pinkla_lane (time, lane_class, number_of_lane) values ({lane_data[0]}, {lane_data[1]}, {lane_data[2]})")
        self.remote.commit()
    
    
    def save_vehicle_data(self, vehicle_data):
        self.cur.execute(f"insert into pinkla_vehicle (time, vehicle_status, linear_x, angular_z) values ({vehicle_data[0]}, {vehicle_data[1]}, {vehicle_data[2]}), {vehicle_data[3]}")
        self.remote.commit()
        
        
    def save_object_data(self, object_data):
        self.cur.execute(f"insert into pinkla_object (time, lane_class, number_of_lane) values ({object_data[0]}, {object_data[1]}, {object_data[2]})")
        self.remote.commit()
        
        
    def save_event_data(self, event_data):
        self.cur.execute(f"insert into pinkla_event (time, lane_class, number_of_lane) values ({event_data[0]}, {event_data[1]})")
        self.remote.commit()
        
        
    def get_lane_data(self):
        self.cur.execute("select * from pinkla_lane")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time, lane_class, lane_number"])
        return self.df
        
        
    def get_vehicle_data(self):
        self.cur.execute("select * from pinkla_vehicle")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time, vehicle_status, linear_x, angular_z"])
        return self.df
        
        
    def get_object_data(self):
        self.cur.execute("select * from pinkla_object")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time, object_class, number_of_object"])
        return self.df
        
        
    def get_event_data(self):
        self.cur.execute("select * from pinkla_event")
        result = self.cur.fetchall()
        self.df = pd.DataFrame(result, columns = ["time, event_class"])
        return self.df
    
    
    def close_mysql(self):
        self.remote.close()