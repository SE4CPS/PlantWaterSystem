from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserRepository:
    def __init__(self, dal: UserDAL):
        self.dal = dal

    def verify_user(self, user: UserSchema):
        return self.dal.verify_user(user)