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
    
    def get_sensor_data_by_id(self, reading_id: str):
        return self.dal.get_sensor_data_by_id(reading_id)
    
    def get_sensor_data_by_username(self, username: str):
        return self.dal.get_sensor_data_by_username(username)
    
    def get_sensor_data_details_by_sensorid_and_deviceid(self, sensorid: str, deviceid: str):
        return self.dal.get_sensor_data_details_by_sensorid_and_deviceid(sensorid, deviceid)
    
    def update_sensor_data(self, reading_id: str, update_data: dict):
        return self.dal.update_sensor_data(reading_id, update_data)
    
    def delete_sensor_data(self, reading_id: str):
        return self.dal.delete_sensor_data(reading_id)

    def add_sensor_data(self, sensor_data: dict):
        return self.dal.add_sensor_data(sensor_data)
    
    def get_last_status(self, sensorid: str, deviceid: str):
        return self.dal.get_last_status(sensorid, deviceid)
    
    def get_sensor_id_by_device_id(self, deviceid: str):
        return self.dal.get_sensor_id_by_device_id(deviceid)