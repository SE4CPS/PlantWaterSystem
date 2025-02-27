from sqlalchemy.orm import Session

from repository.sensor_repository import SensorRepository
from dal.sensor_dal import SensorDAL
from schemas.sensor_schema import MoistureDataSchema



class SensorService:
    def __init__(self, repository: SensorRepository):
        self.repository = repository

    def receive_moisture_data(self, sensor: MoistureDataSchema):
        print("Sensor Service called!!!")
        return self.repository.add_moisture_data(sensor)
    
    # def process_moisture_data(db: Session, data: MoistureDataSchema):
    #     # Add any additional processing logic here (e.g., alerts if moisture < threshold)
    #     return create_moisture_data(db, data)

def get_service():
    dal = SensorDAL()
    repository = SensorRepository(dal)
    return SensorService(repository)
