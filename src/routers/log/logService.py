import logging
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from src.model.logDto import LogEntry, LogLevel
from src.model.custom_exceptions import InvalidTokenException
from src.utils.user_handler import UserHandler


load_dotenv()

CONFIG_PATH = os.getenv("CONFIG_PATH")
LOG_LENGTH = 500

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class LogService():
    def __init__(self) -> None:
        self.user_handler = UserHandler()
        
    def get_log_html(self):
        with open('./src/html/logs.html', 'r') as file:
            html = file.read()
        logs = self.__get_logs()
        log_text = ''
        for log in logs:
            log_text += f'<p>{log}</p>'
        html = html.replace('XXX', log_text)
        return html
    
    def add_log(self, log_entry: LogEntry):
        user = self.user_handler.get_user_by_token(log_entry.token)
        if user is None:
            logging.error(f'Invalid token for adding a new log entry ')
            raise InvalidTokenException()
        if log_entry.level == LogLevel.DEBUG:
            logging.debug(f"{log_entry.module} - {log_entry.message}")
        elif log_entry.level == LogLevel.INFO:
            logging.info(f"{log_entry.module} - {log_entry.message}")
        elif log_entry.level == LogLevel.WARNING:
            logging.warning(f"{log_entry.module} - {log_entry.message}")
        elif log_entry.level == LogLevel.ERROR:
            logging.error(f"{log_entry.module} - {log_entry.message}")
        elif log_entry.level == LogLevel.CRITICAL:
            logging.critical(f"{log_entry.module} - {log_entry.message}")
        else:
            logging.warning(f"{log_entry.module} - {log_entry.message}")
    
        return "OK"
    
    def __get_logs(self) -> list[str]:
        logs: list[str] = []
        with open(CONFIG_PATH+"/logs", "r") as file:
            data = file.readlines()
            if len(data) > LOG_LENGTH:
                data = data[-LOG_LENGTH:]
        for element in data:
            if "@" in element:
                segments = element.split('@')
                log = segments[0] + " " + " ".join(segments[1].split(' ')[1:])
                logs.append(log)
            else:
                logs.append(element)
        return logs[::-1]