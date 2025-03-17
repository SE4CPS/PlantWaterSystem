from dal.sensor_dal import SensorDAL
from schemas.sensor_schema import MoistureDataSchema
from typing import List

class SensorRepository:
    def __init__(self, dal: SensorDAL):
        self.dal = dal

    def add_moisture_data(self, sensors: List[MoistureDataSchema]):
        return self.dal.receive_moisture_data(sensors)