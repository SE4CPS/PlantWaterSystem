"""
send_data_api.py – FastAPI router for /api/send-data
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
import sqlite3

from .database import get_db, save_record

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────
# 1.  Pydantic models
# ──────────────────────────────────────────────────────────────────────────
class ReadingItem(BaseModel):
    id: int = Field(..., description="Unique reading ID sent by device")
    timestamp: datetime
    sensor_id: int
    adc_value: float
    moisture_level: float
    digital_status: str
    weather_temp: float
    weather_humidity: float
    weather_sunlight: float
    weather_wind_speed: float
    location: str
    weather_fetched: datetime
    device_id: str

    @validator("digital_status")
    def status_must_be_str(cls, v):
        return v.strip()

    def as_db_tuple(self) -> tuple:
        """Return values in DB column order (see save_record)."""
        return (
            self.id,
            self.timestamp.isoformat(sep=" "),
            self.device_id,
            self.sensor_id,
            self.adc_value,
            self.moisture_level,
            self.digital_status,
            self.weather_temp,
            self.weather_humidity,
            self.weather_sunlight,
            self.weather_wind_speed,
            self.location,
            self.weather_fetched.isoformat(sep=" "),
        )


class ReadingPayload(BaseModel):
    data: List[ReadingItem]


# ──────────────────────────────────────────────────────────────────────────
# 2.  Endpoint
# ──────────────────────────────────────────────────────────────────────────
@router.post("/api/send-data")
def send_data(payload: ReadingPayload, db=Depends(get_db)):
    """
    Insert multiple sensor readings.
    Returns 400 on duplicate `id`.
    """
    inserted_ids = []

    try:
        for item in payload.data:
            save_record(db, item.as_db_tuple())
            inserted_ids.append(item.id)
    except sqlite3.IntegrityError:
        # Duplicate primary key or other constraint failure
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="One or more reading IDs already exist in the database.",
        )

    return {"status": "success", "inserted_ids": inserted_ids}
