from pydantic import BaseModel
from datetime import datetime

class MoistureDataSchema(BaseModel):
    sensor_id: int
    id: int 
    timestamp: datetime
    moisture_level: float
    digital_status: str