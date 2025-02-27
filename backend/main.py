from fastapi import FastAPI
from controller.plant_controller import create_plant
from config.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

# Initialize database
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this in production)
    allow_credentials=True,  # Allow cookies or authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include Routes
app.include_router(create_plant)

if __name__ == "__main__":
    print("-----------")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
