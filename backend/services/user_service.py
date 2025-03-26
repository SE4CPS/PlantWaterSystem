from repository.user_repository import UserRepository
from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, email: str):
        return self.repository.get_user(email)
    
    def create_user(self, sensorid: int, firstname: str, lastname: str, username: str, userpassword: str, email: str):
        return self.repository.create_user(
            sensorid=sensorid,
            firstname=firstname,
            lastname=lastname,
            username=username,
            userpassword=userpassword,
            email=email
        )


def get_user_service():
    dal = UserDAL()
    repository = UserRepository(dal)
    return UserService(repository)