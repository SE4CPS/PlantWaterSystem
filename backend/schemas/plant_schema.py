from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class PlantSchema(BaseModel):
    plant_name: str
    user_id: str
    sensor_id: str
    device_id: str
    date: Optional[date] = None
    time: Optional[time] = None