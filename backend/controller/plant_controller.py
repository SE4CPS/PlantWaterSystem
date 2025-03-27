from fastapi import APIRouter, Depends, HTTPException
from schemas.plant_schema import PlantSchema
from schemas.user_schema import UserSchema
from services.plant_service import get_service, PlantService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from config.authentication import get_current_user


create_plant = APIRouter()

@create_plant.post("/api/plant/data", response_model=PlantSchema)
def create_plant_entry(
    plant: PlantSchema, 
    service: PlantService = Depends(get_service), 
    current_user: str = Depends(get_current_user)
):
    try:
        # Call the service layer to create the plant
        response = service.create_plant(plant)

        # Check if the response contains an error
        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

        return JSONResponse(status_code=201, content=response)

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})
    

@create_plant.get("/api/plant/data", response_model=list)
def get_plant_data(
    service: PlantService = Depends(get_service),
    current_user: str = Depends(get_current_user)
):
    try: 
        response = service.get_plants(current_user)

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        return JSONResponse(status_code=200, content=response)
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})
