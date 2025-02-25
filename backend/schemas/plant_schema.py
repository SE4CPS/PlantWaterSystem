from pydantic import BaseModel

class PlantSchema(BaseModel):
    PlantID: int
    PlantName: str
    ScientificName: str
    Threshhold: float