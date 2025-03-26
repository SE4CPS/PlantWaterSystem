from pydantic import BaseModel

class UserCreateSchema(BaseModel):
    sensorid: int
    firstname: str
    lastname: str
    username: str
    userpassword: str
    email: str