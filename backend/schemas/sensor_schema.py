from pydantic import BaseModel
from datetime import datetime
from typing import List

class MoistureDataSchema(BaseModel):
    id: int 
    timestamp: datetime
    device_id: str
    sensor_id: int
    adc_value: int
    moisture_level: float
    digital_status: str
    weather_temp: float
    weather_sunlight: float
    weather_wind_speed: float
    location: str # city, state, country
    weather_fetched: datetime


class MoistureDataListSchema(BaseModel):
    data: List[MoistureDataSchema]  # Accept array of sensor data

