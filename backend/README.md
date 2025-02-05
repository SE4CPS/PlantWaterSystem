
## Architecrure digram for Water Plant Project 

+--------------------------------------------------+
|                  User Interface                  |
|  (Web/Mobile App)                                |
|  - View sensor data (Moisture, Temp, Humidity)   |
|  - Control watering manually                     |
+----------------------▲---------------------------+
                       |
+----------------------▼---------------------------+
|                 Backend                          |
| (  Python / Golang )    |
|  - Stores sensor data (MongoDB/PostgreSQL/SQL)       |
|  - Provides APIs for frontend & mobile app       |
|  - Sends watering commands to microcontroller    |
|  - AI/ML for predictive watering (optional)      |
+----------------------▲---------------------------+
                       |
+----------------------▼---------------------------+
|           Local Edge Processing Unit             |
|  (Raspberry Pi / ESP32 / Arduino)                |
|  - Reads moisture and temperature sensors        |
|  - Controls water pump via relay                 |
|  - Sends data to the cloud (MQTT/HTTP API)       |
|  - Works offline if cloud connection is lost     |
+----------------------▲---------------------------+
                       |
+----------------------▼---------------------------+
|             Sensor & Actuator Layer              |
|  - Soil Moisture Sensor                          |
|  - Temperature & Humidity Sensor                 |
|  - Water Pump + Relay                            |
+--------------------------------------------------+

## DataBase Schema 

### User Data
```
{
    "_id": ObjectId(),
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password_hash": "hashed_password",
    "created_at": ISODate("2025-01-22T10:00:00Z")
}

```

### Plants Collection

```{
    "_id": ObjectId(),
    "user_id": ObjectId("user_id"),
    "name": "Tomato Plant",
    "plant_type": "Vegetable",
    "optimal_moisture_level": 60,
    "created_at": ISODate("2025-01-22T10:00:00Z")
}

```

### Sensors Collection

```
{
    "_id": ObjectId(),
    "sensor_id": ObjectId("sensor_id"),
    "moisture_level": 45,
    "temperature": 22.5,
    "humidity": 60,
    "recorded_at": ISODate("2025-01-22T10:05:00Z")
}

```


###  Sensor Data Collection
```
{
    "_id": ObjectId(),
    "user_id": ObjectId("user_id"),
    "plant_id": ObjectId("plant_id"),
    "sensor_id": ObjectId("sensor_id"),
    "water_amount_ml": 500,
    "watered_at": ISODate("2025-01-22T10:10:00Z")
}

```

### Watering Logs Collection

```
{
    "_id": ObjectId(),
    "user_id": ObjectId("user_id"),
    "message": "Moisture level below threshold. Watering initiated.",
    "status": "unread",
    "created_at": ISODate("2025-01-22T10:15:00Z")
}

```
