from pydantic import BaseModel
from typing import Optional

class PlantSchema(BaseModel):
    PlantID: int
    PlantName: str
    ScientificName: str
    Threshold: float
    ImageFilename: Optional[str] = None  # Optional field for image filename
