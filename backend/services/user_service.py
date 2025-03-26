from repository.user_repository import UserRepository
from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, username: str):
        return self.repository.get_user(username)
    
    def create_user(self, username: str, password: str):
        return self.repository.create_user(username, password)


def get_user_service():
    dal = UserDAL()
    repository = UserRepository(dal)
    return UserService(repository)