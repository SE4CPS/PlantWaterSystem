from pydantic import BaseModel

class UserSchema(BaseModel):
    userid: int
    firstname: str
    lastname: str
    username: str
    userpassword: str
    email: str
    phonenumber: str
    deviceid: str