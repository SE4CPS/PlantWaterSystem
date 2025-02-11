from sqlalchemy import Column, Integer, String, Float
from config.database import Base

class Plant(Base):
    __tablename__ = "plants"
    PlantID = Column(Integer, primary_key=True, index=True)
    PlantName = Column(String(50), nullable=False)
    ScientificName = Column(String(50), nullable=False)
    Threshhold = Column(Float, nullable=False)