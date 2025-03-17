from fastapi import APIRouter, Depends, HTTPException
from schemas.sensor_schema import MoistureDataListSchema
from schemas.user_schema import UserSchema
from services.sensor_service import get_service, SensorService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from typing import List
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
# from services.user_service import get_user_service, UserService


add_moisture_data = APIRouter()

# security = HTTPBasic()


# def verify_credentials(credentials: HTTPBasicCredentials = Depends(security), user_service: UserService = Depends(get_user_service)):
#     username = credentials.username
#     password = credentials.password
#     user_schema = UserSchema(username=username, password=password)
#     print(user_service.verify_user(user_schema))
#     if user_service.verify_user(user_schema) == 0:
#         raise HTTPException(
#             status_code= 401,
#             detail="Invalid credentials",
#             headers={"WWW-Authenticate": "Basic"},
#         )
#     return username


@add_moisture_data.post("/api/send-data", response_model=dict)
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