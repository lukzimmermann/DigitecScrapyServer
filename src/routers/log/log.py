import os
import logging
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse

from src.model.custom_exceptions import InvalidTokenException
from src.model.logDto import LogEntry, LogLevel
from src.routers.log.logService import LogService

load_dotenv()

CONFIG_PATH = os.getenv("CONFIG_PATH")

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/log", tags=["Log"])

@router.get("/")
async def get_logs():
    try:
        html = LogService().get_log_html()
        return HTMLResponse(content=html, status_code=200, media_type="text/html")
    except:
        logging.error(f'LogEndpoint - Could not create html site for logs')
        return HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/add/")
async def upload_batch(log_entry: LogEntry):
    try:
        return LogService().add_log(log_entry)
    except InvalidTokenException():
        logging.error(f'LogEndpoint - Invalid token for adding log entry')
        return HTTPException(status_code=500, detail="Invalid Token")