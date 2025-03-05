from sqlalchemy import Column, Integer, String, Float
from config.database import Base

class Plant(Base):
    __tablename__ = "plants"
    PlantID = Column(Integer, primary_key=True, index=True)
    PlantName = Column(String(50), nullable=False)
    ScientificName = Column(String(50), nullable=False)
    Threshhold = Column(Float, nullable=False)

class Sensor(Base):
    __tablename__ = "sensors"
    
    sensor_id = Column(Integer, nullable=False)
    #sensor_id = Column(Integer, ForeignKey("plants.PlantID"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    moisture_level = Column(Float, nullable=False)
    digital_status = Column(String, nullable=False)

    #plant = relationship("Plant")