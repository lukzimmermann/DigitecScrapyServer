import zipfile
import io
import os
import logging
import sys
from fastapi import APIRouter, Query, File, UploadFile, Form, HTTPException, Request
from typing import Annotated
from pydantic import BaseModel
from dotenv import load_dotenv
from src.routers.jobs.jobsService import JobService

load_dotenv()

DATA_PATH = os.getenv("BASELINE_PATH")
CONFIG_PATH = os.getenv("CONFIG_PATH")

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Job(BaseModel):
    id: str

    def __repr__(self) -> str:
        return super().__repr__()
    
class Token(BaseModel):
    token: str

class Batch(BaseModel):
    id: str
    start: int
    end: int
    interval: float

router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_service = JobService()

@router.get("/get_batch/")
async def get_batch(request: Request, token: Token) -> Batch:
    if token.token in job_service.users:
        user = job_service.users[token.token]
        new_job = job_service.get_new_job(user=user)
        logging.info(f'{user}@{request.client.host} get a new batch from {new_job.start} to {new_job.end}')
        return Batch(id = new_job.id, start=new_job.start, end=new_job.end, interval=new_job.interval)
    else:
        raise HTTPException(status_code=403, detail="Not allowed")
    

@router.post("/upload_batch/")
async def upload_batch(request: Request, id: Annotated[str, Form()], file: UploadFile = File(...)):
    if job_service.is_job_active(id):
        file_content = await file.read()
        file_content_io = io.BytesIO(file_content)

        job = job_service.get_job_by_id(id)

        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        with zipfile.ZipFile(file_content_io, "r") as zip_ref:
            file_names = zip_ref.namelist()
            number_files = len(file_names)
            zip_ref.extractall(DATA_PATH)

        job_service.finish_job(id)
        logging.info(f'{job.user}@{request.client.host} send {number_files} datasets from {job.start} to {job.end} ({(number_files/(job.end-job.start)*100):.2f}%)')
        return {"message": "Files uploaded and extracted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Not allowed")


@router.on_event("shutdown")
async def on_shutdown():
    job_service.stop()
