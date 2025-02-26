from repository.plant_repository import PlantRepository
from dal.plant_dal import PlantDAL
from schemas.plant_schema import PlantSchema

class PlantService:
    def __init__(self, repository: PlantRepository):
        self.repository = repository

    def create_plant(self, plant: PlantSchema):
        print("im her in service")
        return self.repository.add_plant(plant)
    
    def get_plants(self):
        return self.repository.get_plants()


def get_service():
    dal = PlantDAL()
    repository = PlantRepository(dal)
    return PlantService(repository)