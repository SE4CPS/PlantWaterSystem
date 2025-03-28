from pydantic import BaseModel

class UserCreateSchema(BaseModel):
    firstname: str
    lastname: str
    username: str
    userpassword: str
    email: str
    phonenumber: str