from pydantic import BaseModel
from datetime import datetime, date, time
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
    weather_humidity: float
    location: str # city, state, country
    weather_fetched: datetime


class MoistureDataListSchema(BaseModel):
    data: List[MoistureDataSchema]  # Accept array of sensor data


class SensorDataSchema(BaseModel):
    id: int 
    timestamp: datetime
    sensor_id: int
    adc_value: float
    moisture_level: float
    digital_status: str
    weather_temp: float
    weather_humidity: float
    weather_sunlight: float
    weather_wind_speed: float
    location: str # city, state, country
    weather_fetched: str


class UserPlantSensorSchema(BaseModel):
    firstname: str
    lastname: str
    plantname: str
    scientificname: str
    sensorid: int
    deviceid: str


class SensorDataResponse(BaseModel):
    status_code: int
    data: List[UserPlantSensorSchema]

class SensorDataDetailsResponse(BaseModel):
    id: int
    adcvalue: float
    waterlevel: float
    digitalsatus: str
    moisture_level: float
    date: date
    time: time

class SensorDataDetailsResponseList(BaseModel):
    status_code: int
    data: List[SensorDataDetailsResponse]