from dal.user_dal import UserDAL
from schemas.user_schema import UserSchema

class UserRepository:
    def __init__(self, dal: UserDAL):
        self.dal = dal

    def get_user(self, email: str):
        return self.dal.get_user(email)
      
    def create_user(self, sensorid: int, firstname: str, lastname: str, username: str, userpassword: str, email: str):
        return self.dal.create_user(
            sensorid=sensorid,
            firstname=firstname,
            lastname=lastname,
            username=username,
            userpassword=userpassword,
            email=email
        )

