from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.sensor_schema import MoistureDataListSchema, SensorDataResponse, SensorDataSchema
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
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
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
    request: Request, 
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try:
        # Parse the incoming JSON data
        data = await request.json()
        sensors = data.get("sensor_data", [])

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
    service: SensorService = Depends(get_service),
    current_user: str = Depends(get_current_user)
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