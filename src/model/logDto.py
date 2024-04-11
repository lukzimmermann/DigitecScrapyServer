from enum import Enum
from pydantic import BaseModel

class LogLevel(str, Enum):
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    NOTSET = 'NOTSET'

class LogEntry(BaseModel):
    token: str
    level: LogLevel
    module: str
    message: str