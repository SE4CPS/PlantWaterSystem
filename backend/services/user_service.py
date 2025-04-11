from repository.user_repository import UserRepository
from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, username: str):
        return self.repository.get_user(username)
    
    def create_user(self, firstname: str, lastname: str, username: str, userpassword: str, email: str, phonenumber: str):
        return self.repository.create_user(
            firstname=firstname,
            lastname=lastname,
            username=username,
            userpassword=userpassword,
            email=email,
            phonenumber=phonenumber 
        )


def get_user_service():
    dal = UserDAL()
    repository = UserRepository(dal)
    return UserService(repository)