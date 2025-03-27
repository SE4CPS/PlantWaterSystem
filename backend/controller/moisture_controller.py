from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.sensor_schema import MoistureDataListSchema, MoistureDataSchema, SensorDataDetailsResponse, SensorDataResponse, SensorDataSchema, UserPlantSensorSchema, SensorDataDetailsResponseList
from services.sensor_service import get_service, SensorService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
from config.authentication import get_current_user
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
# from services.user_service import get_user_service, UserService


add_moisture_data = APIRouter()


@add_moisture_data.post("/api/send-data", response_model=dict)
def add_moisture_entry(
    sensors: MoistureDataListSchema, 
    service: SensorService = Depends(get_service)
):
    try:
        # Call the service layer to add sensor moisture data
        response = service.receive_moisture_data(sensors.data)

        # Check if the response contains an error
        if "error" in response:
            status_code = 400 if "Invalid Request" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

        return JSONResponse(status_code=200, content=response)

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Unexpected error: {str(e)}"})

@add_moisture_data.post("/api/send-current", response_model=dict)
async def send_current_data(
    sensors: MoistureDataSchema, 
    service: SensorService = Depends(get_service)
):
    try:
        sensors = [sensors]
        # Call the service layer to add sensor moisture data
        response = service.receive_moisture_data(sensors)

        # Check if the response contains an error
        if "error" in response:
            status_code = 400 if "Invalid Request" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

        return JSONResponse(status_code=200, content=response)

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Unexpected error: {str(e)}"})

@add_moisture_data.get("/api/send-current", response_model=dict)
async def get_current_data(
    service: SensorService = Depends(get_service)
):
    try:
        return JSONResponse(status_code=200, content={"message": "GET request received. No data to process."})

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Unexpected error: {str(e)}"})
    
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# For Frontend
@add_moisture_data.get("/api/sensor_data", response_model=SensorDataResponse)
async def get_sensor_data(
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        response = service.get_sensor_data()

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        # Ensure datetime fields are serialized properly
        for item in response:
            item["timestamp"] = serialize_datetime(item["timestamp"])
        # Convert raw dicts into Pydantic models
        sensor_data_objects = [SensorDataSchema(**item) for item in response]

        return SensorDataResponse(status_code=200, data=sensor_data_objects)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})

@add_moisture_data.delete("/api/sensor_data/{reading_id}")
async def delete_sensor_data(
    reading_id: str, 
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        response = service.delete_sensor_data(reading_id)

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        return JSONResponse(status_code=200, content=response)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})

@add_moisture_data.get("/api/sensor_data/user/{username}", response_model=SensorDataResponse)
async def get_sensor_data_by_username(
    username: str,
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        # Only allow users to access their own information
        if current_user != username:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this user's information"
            )

        response = service.get_sensor_data_by_username(username)

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        # Convert raw dicts into Pydantic models
        plant_sensor_objects = [UserPlantSensorSchema(**item) for item in response]

        return SensorDataResponse(status_code=200, data=plant_sensor_objects)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})

@add_moisture_data.patch("/api/sensor_data/{reading_id}")
async def update_sensor_data(
    reading_id: str,
    update_data: dict,
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        # Validate update_data
        if not update_data:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error": "No update data provided"}
            )

        # List of valid database column names
        valid_columns = [
            'sensorid', 'adcvalue', 'moisturelevel', 'digitalstatus',
            'weathertemp', 'weatherhumidity', 'weathersunlight', 'weatherwindspeed',
            'weatherfetched', 'timestamp', 'location'
        ]

        # Filter update data to only include valid columns
        db_update_data = {
            key: value for key, value in update_data.items()
            if key in valid_columns
        }

        if not db_update_data:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error": "No valid fields to update"}
            )

        response = service.update_sensor_data(reading_id, db_update_data)

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        return JSONResponse(status_code=200, content=response)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})

@add_moisture_data.post("/api/sensor_data", response_model=dict)
async def add_sensor_data(
    sensor_data: dict,
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try:
        # Validate sensor_data
        if not sensor_data:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error": "No sensor data provided"}
            )

        # List of required database column names
        required_columns = [
            'sensorid', 'adcvalue', 'moisturelevel', 'digitalstatus',
            'weathertemp', 'weatherhumidity', 'weathersunlight', 'weatherwindspeed',
            'weatherfetched', 'timestamp', 'location'
        ]

        # Check if all required fields are present
        missing_fields = [field for field in required_columns if field not in sensor_data]
        if missing_fields:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error": f"Missing required fields: {', '.join(missing_fields)}"}
            )

        # Call the service layer to add sensor data
        response = service.add_sensor_data(sensor_data)

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        return JSONResponse(status_code=201, content=response)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})
    
@add_moisture_data.get("/api/sensor_data_details", response_model=SensorDataDetailsResponseList)
async def get_sensor_data_details_by_username(
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        response = service.get_sensor_data_details_by_username()

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        # Convert raw dicts into Pydantic models
        sensor_data_objects = [SensorDataDetailsResponse(**item) for item in response]

        return SensorDataDetailsResponseList(status_code=200, data=sensor_data_objects)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})