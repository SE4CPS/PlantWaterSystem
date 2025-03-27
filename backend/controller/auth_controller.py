from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from config.authentication import create_access_token, verify_password, hash_password, get_current_user
from services.user_service import get_user_service, UserService
from schemas.user_schema import UserSchema
from schemas.user_create_schema import UserCreateSchema


auth_router = APIRouter(prefix="/api")

# Custom form for email-based authentication
# Change to username-based authentication
class UsernamePasswordForm:
    def __init__(self, username: str = Form(...), password: str = Form(...)):
        self.username = username
        self.password = password

# Generate JWT token
@auth_router.post("/token")
def login_for_access_token(form_data: UsernamePasswordForm = Depends(), user_service: UserService = Depends(get_user_service)):
    user = user_service.get_user(form_data.username)

    # if not user or not verify_password(form_data.password, user["userpassword"]):
    if not user or form_data.password != user["userpassword"]:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": form_data.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/users", response_model=UserSchema)
def create_user(user: UserCreateSchema, user_service: UserService = Depends(get_user_service)):
    try:
        # Hash the password before creating the user
        # hashed_password = hash_password(user.userpassword)
        
        user_details = user_service.create_user(
            firstname=user.firstname,
            lastname=user.lastname,
            username=user.username,
            userpassword=user.userpassword,  # Use the hashed password
            email=user.email,
            phonenumber=user.phonenumber
        )
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
    
@auth_router.get("/users", response_model=UserSchema)
def get_user(
    email: str, 
    user_service: UserService = Depends(get_user_service),
    current_user: str = Depends(get_current_user)
):
    try:
        # Only allow users to access their own information
        if current_user != email:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this user's information"
            )

        user_details = user_service.get_user(email)
        # Check if the response contains an error (we assume error in the response means failure)
        if "error" in user_details:
            # If error is present, return the error response with an appropriate status code (400 or 500)
            status_code = 400 if "Duplicate" in user_details["error"] else 500
            return JSONResponse(status_code=status_code, content={"status": "error", "error": user_details["error"]})

        # If the response is successful, return the response with a 201 status code
        return JSONResponse(status_code=201, content=user_details)

    except HTTPException as he:
        raise he
    except Exception as e:
        # If an unexpected error occurs during processing, return a 500 status code
        return JSONResponse(status_code=500, content={"status": "error", "error": f"Unexpected error: {str(e)}"})
