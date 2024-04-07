import zipfile
import io
import os
import logging
import time
import datetime
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from typing import Annotated
from pydantic import BaseModel
from dotenv import load_dotenv
from src.routers.jobs.jobsService import JobService, JobUser

load_dotenv()

DATA_PATH = os.getenv("BASELINE_PATH")
CONFIG_PATH = os.getenv("CONFIG_PATH")
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Job(BaseModel):
    id: str

    def __repr__(self) -> str:
        return super().__repr__()
    
class BatchRequestData(BaseModel):
    token: str
    ip: str

    def __repr__(self) -> str:
        return super().__repr__()

class Batch(BaseModel):
    id: str
    user_name: str
    start: int
    end: int
    created: str
    interval: float

router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_service = JobService()

@router.post("/get_batch/")
async def get_batch(batch_request_data: BatchRequestData) -> Batch:
    if job_service.get_user_by_token(batch_request_data.token) is not None:
        if job_service.is_ip_address_present(batch_request_data.ip):
            raise HTTPException(status_code=403, detail="IP address is still registered for another job, please wait...")
        user: JobUser = job_service.get_user_by_token(batch_request_data.token)
        user.ip = batch_request_data.ip
        new_job = job_service.get_new_job(user=user)
        formatted_time = datetime.datetime.fromtimestamp(new_job.created).strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(f'{user.name}@{user.ip} get a new batch from {new_job.start} to {new_job.end}')
        return Batch(id = new_job.id, start=new_job.start, end=new_job.end, interval=new_job.interval, created=formatted_time, user_name=user.name)
    else:
        raise HTTPException(status_code=403, detail="Not allowed")
    

@router.get("/status/")
async def get_batch() -> list[Batch]:
    status: list[Batch] = []
    for job in job_service.jobs:
        user: JobUser = job.user
        if job.is_running:
            formatted_time = datetime.datetime.fromtimestamp(job.created).strftime('%Y-%m-%d %H:%M:%S')
            status.append(Batch(id=job.id, user_name=user.name, start=job.start, end=job.end, created=formatted_time, interval=job.interval))
    return status
    

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
        logging.info(f'{job.user.name}@{job.user.ip} send {number_files} datasets from {job.start} to {job.end} ({((number_files-1)/(job.end-job.start)*100):.2f}%) in {(time.time() - job.created):.1f}s ({(float(BATCH_SIZE)/(time.time() - job.created)):.1f}A/s)')
        return {"message": "Files uploaded and extracted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Not allowed")


@router.on_event("shutdown")
async def on_shutdown():
    job_service.stop()
