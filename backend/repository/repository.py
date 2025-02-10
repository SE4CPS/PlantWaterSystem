from abc import ABC, abstractmethod
from typing import List
from models import Plant, Sensors, SensorsData  # Assuming models are defined
from db import db

class PlantRepository(ABC):
    @abstractmethod
    def save_plant(self, plant: Plant) -> None:
        pass

    @abstractmethod
    def get_all_plants(self) -> List[Plant]:
        pass

class SensorsRepository(ABC):
    @abstractmethod
    def save_sensor(self, sensor: Sensors) -> None:
        pass

    @abstractmethod
    def get_sensors_by_plant(self, plant_id: int) -> List[Sensors]:
        pass

class SensorsDataRepository(ABC):
    @abstractmethod
    def save_sensor_data(self, sensor_data: SensorsData) -> None:
        pass

    @abstractmethod
    def get_recent_sensor_data(self, sensor_id: int, limit: int = 10) -> List[SensorsData]:
        pass