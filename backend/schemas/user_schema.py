from pydantic import BaseModel

class UserSchema(BaseModel):
    sensorid: int
    firstname: str
    lastname: str
    username: str
    userpassword: str
    email: str