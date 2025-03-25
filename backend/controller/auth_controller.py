from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from config.authentication import create_access_token, verify_password, hash_password
from services.user_service import get_user_service, UserService
from schemas.user_schema import UserSchema
from schemas.user_create_schema import UserCreateSchema

auth_router = APIRouter(prefix="/api")

# Generate JWT token
@auth_router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), user_service: UserService = Depends(get_user_service)):
    user = user_service.get_user(form_data.username)

    if not user or not 'password' in user and not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": form_data.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/users", response_model=UserSchema)
def create_user(user: UserCreateSchema, user_service: UserService = Depends(get_user_service)):
    try:
        user_details = user_service.create_user(user.username, user.password)
        # Check if the response contains an error (we assume error in the response means failure)
        if "error" in user:
            # If error is present, return the error response with an appropriate status code (400 or 500)
            status_code = 400 if "Duplicate" in user_details["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": user_details["error"]})

        # If the response is successful, return the response with a 201 status code
        return JSONResponse(status_code=201, content=user_details)

    except Exception as e:
        # If an unexpected error occurs during processing, return a 500 status code
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})
    
@auth_router.get("/users", response_model=UserSchema)
def get_user(username: str, user_service: UserService = Depends(get_user_service)):
    try:
        user_details = user_service.get_user(username)
        # Check if the response contains an error (we assume error in the response means failure)
        if "error" in user_details:
            # If error is present, return the error response with an appropriate status code (400 or 500)
            status_code = 400 if "Duplicate" in user_details["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": user_details["error"]})

        # If the response is successful, return the response with a 201 status code
        return JSONResponse(status_code=201, content=user_details)

    except Exception as e:
        # If an unexpected error occurs during processing, return a 500 status code
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})