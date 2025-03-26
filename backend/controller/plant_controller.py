from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from schemas.plant_schema import PlantSchema
from schemas.user_schema import UserSchema
from services.plant_service import get_service, PlantService
from fastapi import  Depends
from fastapi.responses import JSONResponse
from config.authentication import get_current_user
from pathlib import Path


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
        response = service.get_plants()

        if "error" in response:
            status_code = 400 if "Duplicate" in response["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})
        
        return JSONResponse(status_code=200, content=response)
    except HTTPException as he:
        raise he
    except Exception as e:
        JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})


# Define allowed file types and max file size (in bytes)
ALLOWED_FILE_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@create_plant.put("/api/plant/data/{plant_id}", response_model=PlantSchema)
async def update_plant_image(
    plant_id: int,
    file: UploadFile = File(...),
    service: PlantService = Depends(get_service)
):
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum limit of 5 MB.")
    
    # Reset file read position
    await file.seek(0)

    # Update the plant entry with the new image filename and content
    response = service.update_plant_image(plant_id, file.filename, file_content)

    if "error" in response:
        status_code = 400 if "Not Found" in response["error"] else 500
        return JSONResponse(status_code=status_code, content={"status": "error", "error": response["error"]})

    return response
