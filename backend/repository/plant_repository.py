from dal.plant_dal import PlantDAL
from schemas.plant_schema import PlantSchema

class PlantRepository:
    def __init__(self, dal: PlantDAL):
        self.dal = dal

    def add_plant(self, plant: PlantSchema):
        return self.dal.create_plant(plant)
    
    def get_plants(self):
        return self.dal.get_plants()

    def update_plant_image(self, plant_id: int, new_image_filename: str, file_content: bytes):
        return self.dal.update_plant_image(plant_id, new_image_filename, file_content)