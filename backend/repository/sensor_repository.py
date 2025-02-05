from models.sensor_model import SensorData
# from db import db

# def save_sensor_data(sensor_data):
    # db.session.add(sensor_data)
    # db.session.commit()

def get_recent_sensor_data(limit=10):
    return SensorData.query.order_by(SensorData.timestamp.desc()).limit(limit).all()
