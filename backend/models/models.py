# from sqlalchemy import ForeignKey
# from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, Float, DateTime
from config.database import Base

class Plant(Base):
    __tablename__ = "plants"
    PlantID = Column(Integer, primary_key=True, index=True)
    PlantName = Column(String(50), nullable=False)
    ScientificName = Column(String(50), nullable=False)
    Threshhold = Column(Float, nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)

class Sensor(Base):
    __tablename__ = "sensors"
    
    sensor_id = Column(Integer, nullable=False)
    #sensor_id = Column(Integer, ForeignKey("plants.PlantID"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    moisture_level = Column(Float, nullable=False)
    digital_status = Column(String, nullable=False)

    #plant = relationship("Plant")