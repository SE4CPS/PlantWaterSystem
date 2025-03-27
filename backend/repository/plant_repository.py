from dal.plant_dal import PlantDAL
from schemas.plant_schema import PlantSchema

class PlantRepository:
    def __init__(self, dal: PlantDAL):
        self.dal = dal

    def add_plant(self, plant: PlantSchema, username: str):
        return self.dal.create_plant(plant, username)
    
    def get_plants(self, username: str):
        return self.dal.get_plants(username)