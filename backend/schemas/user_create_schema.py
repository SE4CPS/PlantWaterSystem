from pydantic import BaseModel

class UserCreateSchema(BaseModel):
    username: str
    password: str