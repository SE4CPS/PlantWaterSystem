from fastapi import APIRouter, Depends
from schemas.plant_schema import PlantSchema
from services.plant_service import get_service, PlantService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials



create_plant = APIRouter()

security = HTTPBasic()

user = {
    "admin": "admin",
    "user": "admin"
}

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    if user.get(username) != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username


@create_plant.post("/api/plant/data", response_model=PlantSchema)
def create_plant_entry(plant: PlantSchema, service: PlantService = Depends(get_service), username: str = Depends(verify_credentials)):
    try:
        # Call the service layer to create the plant
        response = service.create_plant(plant)

        # Check if the response contains an error (we assume error in the response means failure)
        if "error" in response:
            # If error is present, return the error response with an appropriate status code (400 or 500)
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

        # If the response is successful, return the response with a 201 status code
        return JSONResponse(status_code=201, content=response)

    except Exception as e:
        # If an unexpected error occurs during processing, return a 500 status code
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})