from dal.sensor_dal import SensorDAL
from schemas.sensor_schema import MoistureDataSchema
from typing import List

class SensorRepository:
    def __init__(self, dal: SensorDAL):
        self.dal = dal

    def add_moisture_data(self, sensors: List[MoistureDataSchema]):
        return self.dal.receive_moisture_data(sensors)
    
    def get_sensor_data(self):
        return self.dal.get_sensor_data()
    
    def get_sensor_data_by_id(self, sensor_id: str):
        return self.dal.get_sensor_data_by_id(sensor_id)
    
    def delete_sensor_data(self, reading_id: str):
        return self.dal.delete_sensor_data(reading_id)