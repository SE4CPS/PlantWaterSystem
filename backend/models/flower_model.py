# from db import db
from datetime import datetime

class FlowerData():
    __tablename__ = "flower_data"

    # id = db.Column(db.Integer, primary_key=True)
    # device_id = db.Column(db.String(50), nullable=False)
    # timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # temperature = db.Column(db.Float, nullable=False)
    # humidity = db.Column(db.Float, nullable=False)
    # soil_moisture = db.Column(db.Float, nullable=False)

    def __init__(self, device_id, temperature, humidity, soil_moisture,name):
        self.device_id = device_id
        self.temperature = temperature
        self.humidity = humidity
        self.soil_moisture = soil_moisture
        self.name=name
