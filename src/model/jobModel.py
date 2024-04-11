import uuid
import time

class User():
    def __init__(self, name: str, token: str) -> None:
        self.name = name
        self.display_name = ''
        self.token = token
        self.ip = ''

    def __repr__(self) -> str:
        return f'{self.name}@{self.ip}: {self.token}'
    
class Job():
    def __init__(self, user: User, number_list: list[int]) -> None:
        self.id: str = str(uuid.uuid4())
        self.created: float = time.time()
        self.number_list: list[int] = number_list
        self.is_running: bool = True
        self.user: User = user

    def __repr__(self) -> str:
        if self.is_running: state = "IsRunning"
        else: state = "Finished"
        return f'{self.start:>9} -> {self.end:>9}, {state}'

    
class BaseLineJob(Job):
    def __init__(self, user: User, start: int, end: int) -> None:
        super().__init__(user, list(range(start, end+1)))
        
        self.start = start
        self.end = end