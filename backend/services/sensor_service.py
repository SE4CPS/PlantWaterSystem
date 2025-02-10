# from repository.sensor_repository import save_sensor_data
from backend.models.flower_model import Flowerdata

def process_flower_data(data):
    # Validate required fields
    if not all(key in data for key in ("device_id", "temperature", "humidity", "soil_moisture")):
        return {"error": "Missing required fields"}, 400

    # Convert data types and process values
    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
    except ValueError:
        return {"error": "Invalid data format"}, 400

    # Create a SensorData object and save to DB
    sensor_data = Flowerdata(
        device_id=data["device_id"],
        temperature=temperature,
        humidity=humidity,
        soil_moisture=soil_moisture
    )
    print(sensor_data)
    save_sensor_data(sensor_data)
    return {"message": "Sensor data saved successfully"}, 201
