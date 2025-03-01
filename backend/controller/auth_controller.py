from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from config.authentication import create_access_token, verify_password, hash_password
from services.user_service import get_user_service, UserService

auth_router = APIRouter(prefix="/api")

# Generate JWT token
@auth_router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), user_service: UserService = Depends(get_user_service)):
    user = user_service.get_user(form_data.username)
    print("user", user)
    if not user or not 'password' in user and not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": form_data.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}
