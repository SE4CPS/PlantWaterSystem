from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserRepository:
    def __init__(self, dal: UserDAL):
        self.dal = dal

    def get_user(self, username: str):
        return self.dal.get_user(username)

    def create_user(self, username: str, password):
        return self.dal.create_user(username, password)