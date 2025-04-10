from repository.sensor_repository import SensorRepository
from dal.sensor_dal import SensorDAL
from schemas.sensor_schema import MoistureDataSchema
from typing import List


class SensorService:
    def __init__(self, repository: SensorRepository):
        self.repository = repository

    def receive_moisture_data(self, sensors: List[MoistureDataSchema]):
        print("Sensor Service called!!!")
        return self.repository.add_moisture_data(sensors)
    
    def get_sensor_data(self):
        return self.repository.get_sensor_data()

    def get_sensor_data_by_id(self, reading_id: str):
        return self.repository.get_sensor_data_by_id(reading_id)

    def get_sensor_data_by_username(self, username: str):
        return self.repository.get_sensor_data_by_username(username)
    
    def get_sensor_data_details_by_sensorid_and_deviceid(self, sensorid: str, deviceid: str):
        return self.repository.get_sensor_data_details_by_sensorid_and_deviceid(sensorid, deviceid)

    def update_sensor_data(self, reading_id: str, update_data: dict):
        return self.repository.update_sensor_data(reading_id, update_data)

    def delete_sensor_data(self, reading_data: str):
        return self.repository.delete_sensor_data(reading_data)

    def add_sensor_data(self, sensor_data: dict):
        return self.repository.add_sensor_data(sensor_data)
    
    # def process_moisture_data(db: Session, data: MoistureDataSchema):
    #     # Add any additional processing logic here (e.g., alerts if moisture < threshold)
    #     return create_moisture_data(db, data)

    def get_last_status(self, sensorid: str, deviceid: str):
        return self.repository.get_last_status(sensorid, deviceid)

    def get_sensor_id_by_device_id(self, deviceid: str):
        return self.repository.get_sensor_id_by_device_id(deviceid)

def get_service():
    dal = SensorDAL()
    repository = SensorRepository(dal)
    return SensorService(repository)