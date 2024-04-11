import os
from src.model.jobModel import User
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = str(os.getenv("CONFIG_PATH"))

class UserHandler():
    def __init__(self) -> None:
        self.users: list[User] = self.__read_users()

    def get_users(self) -> list[User]:
        return self.users
    
    def update_users(self):
        self.users = self.__read_users()

    def get_user_by_token(self, token: str):
        for user in self.users:
            if str(user.token) == str(token):
                return user
        return None

    def __read_users(self):
        user_list: list[User] = []
        with open(f'{CONFIG_PATH}/users', 'r') as file:
            lines = file.readlines()

        for line in lines:
            segment = line[0:-1].split(';')
            user_list.append(User(segment[0],  segment[1]))

        return user_list