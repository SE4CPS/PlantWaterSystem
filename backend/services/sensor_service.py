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

    def update_sensor_data(self, reading_id: str, update_data: dict):
        return self.repository.update_sensor_data(reading_id, update_data)

    def delete_sensor_data(self, reading_data: str):
        return self.repository.delete_sensor_data(reading_data)
    
    # def process_moisture_data(db: Session, data: MoistureDataSchema):
    #     # Add any additional processing logic here (e.g., alerts if moisture < threshold)
    #     return create_moisture_data(db, data)

def get_service():
    dal = SensorDAL()
    repository = SensorRepository(dal)
    return SensorService(repository)