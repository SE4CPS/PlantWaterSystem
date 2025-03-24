from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.sensor_schema import MoistureDataListSchema
from services.sensor_service import get_service, SensorService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from typing import List


add_moisture_data = APIRouter()


@add_moisture_data.post("/api/sensor/data", response_model=dict)
def add_moisture_entry(sensors: MoistureDataListSchema, service: SensorService = Depends(get_service)):
    try:
        # Call the service layer to add sensor moisture data
        response = service.receive_moisture_data(sensors.data)

        # Check if the response contains an error (we assume error in the response means failure)
        if "error" in response:
            # If error is present, return the error response with an appropriate status code (400 or 500)
            status_code = 400 if "Invalid Request" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

        # If the response is successful, return the response with a 200 status code
        return JSONResponse(status_code=200, content=response)

    except Exception as e:
        # If an unexpected error occurs during processing, return a 500 status code
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Unexpected error: {str(e)}"})

@add_moisture_data.get("/api/sensor/data", response_model=dict)
async def get_current_data(service: SensorService = Depends(get_service)):
    try:
        # This is a placeholder for any logic to implement for GET requests.
        # For example, return the most recent sensor data or a status message.
        return JSONResponse(status_code=200, content={"message": "GET request received. No data to process."})

    except Exception as e:
        # Handle any unexpected errors
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Unexpected error: {str(e)}"})