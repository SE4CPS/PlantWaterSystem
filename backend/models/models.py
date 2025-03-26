from sqlalchemy import Column, Integer, String, Float, DateTime
from config.database import Base

class Plant(Base):
    __tablename__ = "plants"
    PlantID = Column(Integer, primary_key=True, index=True)
    PlantName = Column(String(50), nullable=False)
    ScientificName = Column(String(50), nullable=False)
    Threshhold = Column(Float, nullable=False)
    ImageFilename = Column(String(255), nullable=True)  # New column for image filename

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    device_id = Column(String, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    adc_value = Column(Integer, nullable=False)
    moisture_level = Column(Float, nullable=False)
    digital_status = Column(String, nullable=False)
    weather_temp = Column(Float, nullable=False)
    weather_humidity = Column(Integer, nullable=False)
    weather_sunlight = Column(Float, nullable=False)
    weather_wind_speed = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    weather_fetched = Column(DateTime, nullable=False)