import mysql.connector
import pandas as pd

class pinkla_mysql():
    def __init__(self):
                
        self.df = pd.DataFrame()
        
    def init_db(self, info):
        self.remote = mysql.connector.connect(
            host = info[0],
            user = info[1],
            password = info[2],
            database = info[3]
        )

        self.cur = self.remote.cursor(buffered = True)
        
        self.create_lane_table()
        self.create_vehicle_table()
        self.create_object_table()
        self.create_event_table()
                
    def create_lane_table(self):
        create_query = "create table if not exists pinkla_lane (time datetime primary key, lane_class varchar(32), number_of_lane int)"
        self.cur.execute(create_query)
        self.remote.commit()
        
    def create_vehicle_table(self):
        create_query = "create table if not exists pinkla_vehicle (time datetime primary key, vehicle_status varchar(32), linear_x float, angular_z float)"
        self.cur.execute(create_query)
        self.remote.commit()
        
    def create_object_table(self):
        create_query = "create table if not exists pinkla_object (time datetime primary key, object_class varchar(32), number_of_object int)"
        self.cur.execute(create_query)
        self.remote.commit()
        
        
    def create_event_table(self):
        create_query = "create table if not exists pinkla_event (time datetime primary key, event_class varchar(32))"
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