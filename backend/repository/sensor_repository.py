from dal.sensor_dal import SensorDAL
from schemas.sensor_schema import MoistureDataSchema

class SensorRepository:
    def __init__(self, dal: SensorDAL):
        self.dal = dal

    def add_moisture_data(self, sensor: MoistureDataSchema):
        return self.dal.receive_moisture_data(sensor)