from fastapi import FastAPI
from controller.plant_controller import create_plant
from config.database import Base, engine

# Initialize database
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()

# Include Routes
app.include_router(create_plant)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
