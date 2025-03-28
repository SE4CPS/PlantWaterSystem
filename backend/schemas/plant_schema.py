from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class PlantSchema(BaseModel):
    PlantID: int
    PlantName: str
    ScientificName: str
    Threshold: float
    date: Optional[date] = None
    time: Optional[time] = None