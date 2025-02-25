from repository.user_repository import UserRepository
from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def verify_user(self, user: UserSchema):
        return self.repository.verify_user(user)

def get_user_service():
    dal = UserDAL()
    repository = UserRepository(dal)
    return UserService(repository)